from unittest.mock import call

import pytest

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    UNIT_USAGE,
    PipelineCompletedCriteria,
)
from common_utils.exceptions import DependenciesUnMetSimulationException
from handlers import (
    DMSFloorDeliverableHandler,
    DMSIFCDeliverableHandler,
    DMSUnitDeliverableHandler,
    DMSVectorFilesHandler,
    QAHandler,
    SiteHandler,
)
from handlers.db import (
    ClientDBHandler,
    SiteDBHandler,
    SlamSimulationDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_client_bucket_name
from tasks import (
    basic_features,
    connectivity_tasks,
    deliverables_tasks,
    noise_tasks,
    qa_validation_tasks,
    quavis_tasks,
    rectangulator_tasks,
    simulations_tasks,
    surroundings_tasks,
    workflow_tasks,
)
from tasks.workflow_tasks import WorkflowGenerator
from tests.utils import random_simulation_version
from workers_config.celery_config import INCREASED_TASK_PRIORITY


@pytest.fixture
def site_unprocessed(site):
    return SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"full_slam_results": ADMIN_SIM_STATUS.UNPROCESSED},
    )


def test_task_site_zip_deliverable_should_export_zip_from_site_with_no_units(
    mocker,
    client_db,
    site,
    building,
    floor,
    plan,
    mocked_gcp_upload_file_to_bucket,
    mocked_gcp_download_file_as_bytes,
    mocked_gcp_download_file_from_media_link,
    celery_eager,
):

    mock_download_vectors = mocker.patch.object(
        DMSVectorFilesHandler, "download_vector_files", return_value=b""
    )
    mock_download_unit_file = mocker.patch.object(
        DMSUnitDeliverableHandler, "download_unit_file", return_value=b""
    )
    mock_download_floor_file = mocker.patch.object(
        DMSFloorDeliverableHandler, "download_floor_file", return_value=b""
    )
    mock_download_ifc = mocker.patch.object(
        DMSIFCDeliverableHandler, "download_ifc_file", return_value=b"ifc baby"
    )
    generate_qa_mock = mocker.patch.object(QAHandler, "generate_qa_report")

    expected_destination_gcs_path = SiteHandler.get_deliverable_zipfile_path(
        client_id=site["client_id"], site_id=site["id"]
    )
    units_in_floor_mock = mocker.patch.object(
        UnitDBHandler, "get_joined_by_site_building_floor_id", return_value=[]
    )

    deliverables_tasks.task_site_zip_deliverable.delay(site_id=site["id"])

    # after finishing DI-1017, the vectors shouldn't be downloaded
    mock_download_vectors.assert_called_once_with(
        site_id=site["id"], download_path=mocker.ANY
    )

    expected_calls = [
        mocker.call(floor_id=floor["id"], file_format=format, language=language)
        for language in SUPPORTED_LANGUAGES
        for format in SUPPORTED_OUTPUT_FILES
        if format != SUPPORTED_OUTPUT_FILES.IFC
    ]
    mock_download_floor_file.assert_has_calls(expected_calls, any_order=True)

    # no unit PNG/PDFs should be downloaded
    mock_download_unit_file.assert_not_called()
    units_in_floor_mock.assert_called_once_with(
        site_id=site["id"], building_id=building["id"], floor_id=floor["id"]
    )

    mock_download_ifc.assert_called_once_with(site_id=site["id"])
    generate_qa_mock.assert_called_once()
    mocked_gcp_upload_file_to_bucket.assert_called_once_with(
        bucket_name=get_client_bucket_name(client_id=site["client_id"]),
        destination_folder=expected_destination_gcs_path.parent,
        local_file_path=mocker.ANY,
        destination_file_name=expected_destination_gcs_path.name,
    )


def test_full_slam_results_field_gets_updated_to_pending(
    mocker,
    mocked_site_pipeline_completed,
    client_db,
    site_coordinates,
    make_buildings,
    make_plans,
    make_floor,
    site_region_proj_ch,
):
    """
    Checks whether executing the generate_view_surroundings_and_features_and_floorplans_for_site_task is updating
    the full_slam_results field in the DB to PENDING and heatmaps qa complete to False
    """
    site_priority = 10
    site = SiteDBHandler.add(
        client_id=client_db["id"],
        region="Switzerland",
        full_slam_results=ADMIN_SIM_STATUS.UNPROCESSED,
        name="Some site",
        pipeline_and_qa_complete=True,
        heatmaps_qa_complete=True,
        priority=site_priority,
        **site_coordinates,
        **site_region_proj_ch,
    )
    buildings = make_buildings(site)
    plans = make_plans(*buildings)
    for i, building in enumerate(buildings):
        _ = make_floor(building=building, plan=plans[i], floornumber=i)

    mocker.patch.object(workflow_tasks.Task, "apply_async", return_value=None)

    workflow_tasks.run_digitize_analyze_client_tasks.delay(site_id=site["id"])
    site_updated = SiteDBHandler.get_by(id=site["id"])
    assert site_updated["full_slam_results"] == ADMIN_SIM_STATUS.PENDING.value
    assert site_updated["heatmaps_qa_complete"] is False


def test_full_slam_results_field_gets_updated_to_processing(
    mocker, site_unprocessed, mocked_site_pipeline_completed, celery_eager
):
    priority = 10
    SiteDBHandler.update(
        item_pks={"id": site_unprocessed["id"]}, new_values={"priority": priority}
    )
    mocked_target_task = mocker.patch.object(
        workflow_tasks.slam_results_success, "apply_async", autospec=True
    )
    mocker.patch.object(
        WorkflowGenerator,
        WorkflowGenerator.get_full_chain_based_on_client_options.__name__,
        return_value=workflow_tasks.slam_results_success,
    )
    workflow_tasks.run_digitize_analyze_client_tasks(site_id=site_unprocessed["id"])

    mocked_target_task.assert_called_with(priority=priority + INCREASED_TASK_PRIORITY)
    assert (
        SiteDBHandler.get_by(id=site_unprocessed["id"])["full_slam_results"]
        == ADMIN_SIM_STATUS.PROCESSING.value
    )


def test_full_slam_results_field_gets_updated_to_success(
    mocker,
    site_unprocessed,
    floor,
    mocked_site_pipeline_completed,
    celery_eager,
    run_ids,
    mocked_gcp_delete,
    generate_ifc_file_mocked,
    unit,
):
    tasks_to_mock = (
        qa_validation_tasks.run_qa_validation_task,
        basic_features.run_basic_features_task,
        basic_features.run_unit_types_task,
        simulations_tasks.run_buildings_elevation_task,
        simulations_tasks.update_site_location_task,
        surroundings_tasks.generate_surroundings_for_view_analysis_task,
        simulations_tasks.configure_quavis_task,
        simulations_tasks.configure_sun_v2_quavis_task,
        quavis_tasks.run_quavis_task,
        simulations_tasks.store_quavis_results_task,
        simulations_tasks.store_sun_v2_quavis_results_task,
        connectivity_tasks.connectivity_simulation_task,
        noise_tasks.noise_simulation_task,
        rectangulator_tasks.biggest_rectangle_task,
        deliverables_tasks.generate_building_triangulation_task,
        deliverables_tasks.task_site_zip_deliverable,
        deliverables_tasks.generate_unit_pngs_and_pdfs,
        deliverables_tasks.generate_pngs_and_pdfs_for_floor_task,
        deliverables_tasks.generate_dxf_floor_task,
        deliverables_tasks.generate_dwg_floor_task,
        deliverables_tasks.generate_vector_files_task,
        deliverables_tasks.generate_vector_files_task,
        deliverables_tasks.generate_energy_reference_area_task,
        deliverables_tasks.generate_unit_plots_task,
    )
    mocked_runs = {
        task.__name__: mocker.patch.object(task, "run", return_value=True)
        for task in tasks_to_mock
    }
    workflow_tasks.run_digitize_analyze_client_tasks(site_id=site_unprocessed["id"])

    assert mocked_runs.pop("run_quavis_task").call_count == 2

    assert all(t.call_count == 1 for _, t in mocked_runs.items())
    assert (
        SiteDBHandler.get_by(id=site_unprocessed["id"])["full_slam_results"]
        == ADMIN_SIM_STATUS.SUCCESS.value
    )
    for run_id in run_ids[:3]:  # basic features and sun view
        assert (
            SlamSimulationDBHandler.get_by(run_id=run_id)["state"]
            == ADMIN_SIM_STATUS.SUCCESS.value
        )


def test_run_view_sun_task_chain_should_delete_simulation_artifacts(
    mocker, site, run_ids, celery_eager
):
    from handlers.quavis import QuavisGCPHandler

    # mock other tasks in chain
    for task in [
        simulations_tasks.configure_quavis_task,
        simulations_tasks.register_simulation,
        simulations_tasks.simulation_success,
        quavis_tasks.run_quavis_task,
        simulations_tasks.store_quavis_results_task,
    ]:
        mocker.patch.object(task, "run", return_value=True)

    mocked_delete = mocker.patch.object(
        QuavisGCPHandler,
        QuavisGCPHandler.delete_simulation_artifacts.__name__,
    )

    workflow_tasks.WorkflowGenerator(site_id=site["id"]).get_view_task_chain().delay()

    mocked_delete.assert_called_once_with(run_id=run_ids[0])


@pytest.mark.parametrize(
    "pipeline_and_qa_complete, pipeline_status, have_buildings, have_floors, expected_task_called",
    [
        (False, False, False, False, False),
        (True, False, False, False, False),
        (False, True, False, False, False),
        (False, False, True, False, False),
        (False, True, True, True, False),
        (True, False, True, True, False),
        (True, True, True, False, False),
        (True, True, True, True, True),
    ],
)
def test_generate_full_slam_results_task_chains_conditions_unmet(
    mocker,
    pipeline_and_qa_complete,
    pipeline_status,
    expected_task_called,
    site,
    have_buildings,
    have_floors,
    make_floor,
    make_plans,
    make_buildings,
):
    from handlers import SiteHandler

    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"pipeline_and_qa_complete": pipeline_and_qa_complete},
    )

    mocker.patch.object(
        SiteHandler,
        "pipeline_completed_criteria",
        return_value=PipelineCompletedCriteria(
            labelled=pipeline_status,
            classified=pipeline_status,
            splitted=pipeline_status,
            units_linked=pipeline_status,
            georeferenced=pipeline_status,
        ),
    )
    if have_buildings:
        buildings = make_buildings(site)
        plans = make_plans(*buildings)
        if have_floors:
            for i, building in enumerate(buildings):
                _ = make_floor(building=building, plan=plans[i], floornumber=i)

    if not expected_task_called:
        with pytest.raises(DependenciesUnMetSimulationException):
            workflow_tasks.run_digitize_analyze_client_tasks.delay(site_id=site["id"])
    else:
        mocked_call = mocker.patch.object(
            workflow_tasks.run_digitize_analyze_client_tasks, "apply_async"
        )
        workflow_tasks.run_digitize_analyze_client_tasks.delay(site_id=site["id"])
        assert (
            SiteDBHandler.get_by(id=site["id"])["full_slam_results"]
            == ADMIN_SIM_STATUS.PENDING.value
        )
        assert mocked_call.called


@pytest.mark.parametrize("option_dxf", [True, False])
@pytest.mark.parametrize("option_pdf", [True, False])
@pytest.mark.parametrize("option_analysis", [True, False])
@pytest.mark.parametrize("option_competition", [True, False])
@pytest.mark.parametrize("option_ifc", [True, False])
@pytest.mark.parametrize("has_residential_apartments", [True, False])
def test_generate_full_slam_results_task_chains_partial_client_options(
    celery_eager,
    run_ids,
    mocked_site_pipeline_completed,
    initial_tasks_mocked,
    quavis_task_mocked,
    basic_feature_mocked,
    qa_validation_task_mocked,
    clustering_units_mocked,
    generate_building_triangulation_task_mocked,
    generate_surroundings_task_mocked,
    store_quavis_results_mocked,
    store_quavis_sun_v2_results_mocked,
    configure_quavis_mocked,
    configure_sun_v2_quavis_task_mocked,
    success_task_mocked,
    zip_task_mocked,
    site_coordinates,
    png_pdf_floor_task_mocked,
    dxf_task_mocked,
    dwg_task_mocked,
    connectivity_mocked,
    biggest_rectangle_simulation_mocked,
    noise_simulation_mocked,
    noise_window_simulation_mocked,
    competition_features_mocked,
    generate_ifc_file_mocked,
    generate_energy_reference_area_task_mocked,
    generate_unit_plots_task_mocked,
    generate_vector_files_task_mocked,
    generate_unit_pngs_and_pdfs_mocked,
    make_buildings,
    make_plans,
    make_floor,
    make_units,
    option_dxf,
    option_pdf,
    option_analysis,
    option_competition,
    option_ifc,
    has_residential_apartments,
    mocked_gcp_delete,
    site_region_proj_ch,
):
    client_db = ClientDBHandler.add(
        **{
            "name": "SL",
            "option_dxf": option_dxf,
            "option_analysis": option_analysis,
            "option_competition": option_competition,
            "option_ifc": option_ifc,
        }
    )
    site = SiteDBHandler.add(
        client_id=client_db["id"],
        client_site_id="123",
        name="Big-tal portfolio",
        region="Switzerland",
        basic_features_status=ADMIN_SIM_STATUS.PENDING.value,
        pipeline_and_qa_complete=True,
        simulation_version=random_simulation_version(),
        **site_region_proj_ch,
        **site_coordinates,
    )
    buildings = make_buildings(site)
    plans = make_plans(*buildings)
    floor = make_floor(building=buildings[0], plan=plans[0], floornumber=0)
    units = make_units(floor, floor)

    if not has_residential_apartments:
        UnitDBHandler.bulk_update(
            unit_usage={
                unit_id: UNIT_USAGE.COMMERCIAL.name
                for unit_id in UnitDBHandler.find_ids(site_id=site["id"])
            }
        )

    workflow_tasks.run_digitize_analyze_client_tasks.delay(site_id=site["id"])

    # Called in all the options
    basic_feature_mocked.assert_called_with(run_id=run_ids[0])

    chained_task_called = [
        x.call_args.kwargs for x in initial_tasks_mocked if x.call_args
    ]
    assert chained_task_called == [{"site_id": site["id"]}] * 3, [
        x.call_args for x in initial_tasks_mocked
    ]
    success_task_mocked.assert_called_with(site_id=site["id"])
    zip_task_mocked.assert_called_with(site_id=site["id"])

    if client_db["option_dxf"]:
        dxf_task_mocked.assert_called_with(floor_id=floor["id"])
        dwg_task_mocked.assert_called_with(floor_id=floor["id"])

    if client_db["option_pdf"]:
        png_pdf_floor_task_mocked.assert_called_with(floor_id=floor["id"])
        png_pdf_floor_task_mocked.assert_called_with(floor_id=floor["id"])

    if client_db["option_ifc"]:
        generate_ifc_file_mocked.assert_called_with(site_id=site["id"])

    if client_db["option_analysis"]:
        generate_surroundings_task_mocked.assert_called_with(site_id=site["id"])
        view_sun_run_id, sun_v2_run_id = run_ids[1:3]
        configure_quavis_mocked.assert_called_with(run_id=view_sun_run_id)
        store_quavis_results_mocked.assert_called_with(run_id=view_sun_run_id)
        configure_sun_v2_quavis_task_mocked.assert_called_with(run_id=sun_v2_run_id)
        store_quavis_sun_v2_results_mocked.assert_called_with(run_id=sun_v2_run_id)
        quavis_task_mocked.assert_has_calls = [
            call(run_id=view_sun_run_id),
            call(run_id=sun_v2_run_id),
        ]
        connectivity_mocked.assert_called_with(site_id=site["id"], run_id=run_ids[3])
        clustering_units_mocked.assert_not_called()
        biggest_rectangle_simulation_mocked.assert_called_with(
            site_id=site["id"], run_id=run_ids[4]
        )
        noise_window_simulation_mocked.assert_called_with(
            site_id=site["id"], run_id=run_ids[5]
        )
        noise_simulation_mocked.assert_called_with(
            site_id=site["id"], run_id=run_ids[6]
        )
        generate_building_triangulation_task_mocked.assert_called_with(
            building_id=buildings[0]["id"]
        )
        generate_vector_files_task_mocked.assert_called_with(site_id=site["id"])
        mocked_gcp_delete.assert_called()
        if client_db["option_competition"]:
            if has_residential_apartments:
                competition_features_mocked.assert_called_with(
                    site_id=site["id"],
                    run_id=run_ids[7],
                )
            else:
                competition_features_mocked.assert_not_called()
        else:
            competition_features_mocked.assert_not_called()

        if has_residential_apartments:
            generate_unit_plots_task_mocked.assert_called_with(site_id=site["id"])
        else:
            generate_unit_plots_task_mocked.assert_not_called()

        for unit in units:
            generate_unit_pngs_and_pdfs_mocked.assert_any_call(unit_id=unit["id"])


def test_generate_full_slam_results_task_chains_site_basic_features_ready(
    celery_eager,
    mocked_site_pipeline_completed,
    initial_tasks_mocked,
    quavis_task_mocked,
    basic_feature_mocked,
    qa_validation_task_mocked,
    clustering_units_mocked,
    connectivity_mocked,
    biggest_rectangle_simulation_mocked,
    noise_simulation_mocked,
    noise_window_simulation_mocked,
    store_quavis_results_mocked,
    store_quavis_sun_v2_results_mocked,
    configure_quavis_mocked,
    configure_sun_v2_quavis_task_mocked,
    client_db,
    generate_ifc_file_mocked,
    generate_energy_reference_area_task_mocked,
    generate_unit_plots_task_mocked,
    png_pdf_floor_task_mocked,
    dxf_task_mocked,
    dwg_task_mocked,
    generate_vector_files_task_mocked,
    success_task_mocked,
    generate_surroundings_task_mocked,
    generate_building_triangulation_task_mocked,
    zip_task_mocked,
    site_coordinates,
    run_ids,
    make_buildings,
    make_plans,
    make_floor,
    mocked_gcp_delete,
    site_region_proj_ch,
):

    site = SiteDBHandler.add(
        client_id=client_db["id"],
        client_site_id="123",
        name="Big-caca portfolio",
        region="Switzerland",
        basic_features_status=ADMIN_SIM_STATUS.SUCCESS.value,
        pipeline_and_qa_complete=True,
        **site_region_proj_ch,
        **site_coordinates,
    )

    buildings = make_buildings(site)
    plans = make_plans(*buildings)
    _ = make_floor(building=buildings[0], plan=plans[0], floornumber=0)

    workflow_tasks.run_digitize_analyze_client_tasks.delay(site_id=site["id"])

    for chained_task in initial_tasks_mocked:
        chained_task.assert_called_with(site_id=site["id"])

    generate_surroundings_task_mocked.assert_called_with(site_id=site["id"])

    (
        basic_features_run_id,
        view_sun_run_id,
        sun_v2_run_id,
        *_,
    ) = run_ids
    quavis_task_mocked.assert_has_calls(
        [call(run_id=view_sun_run_id), call(run_id=sun_v2_run_id)]
    )

    store_quavis_results_mocked.assert_called_with(run_id=view_sun_run_id)

    configure_quavis_mocked.assert_called_with(run_id=view_sun_run_id)

    basic_feature_mocked.assert_called_with(run_id=basic_features_run_id)
    clustering_units_mocked.assert_not_called()
    biggest_rectangle_simulation_mocked.assert_called_with(
        site_id=site["id"], run_id=run_ids[4]
    )
    connectivity_mocked.assert_called()


@pytest.mark.parametrize(
    "exclude_sites,pipeline_and_qa_complete, nbr_of_floor_content_download",
    [(False, True, 1), (False, False, 0), (True, True, 0)],
)
def test_task_client_delivery(
    mocker,
    celery_eager,
    client_db,
    site,
    floor,
    unit,
    mocked_gcp_upload_file_to_bucket,
    exclude_sites,
    pipeline_and_qa_complete,
    nbr_of_floor_content_download,
):
    from tasks.deliverables_tasks import task_full_client_zip_delivery

    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"pipeline_and_qa_complete": pipeline_and_qa_complete},
    )
    mocked_download_floor_content = mocker.patch(
        "tasks.utils.deliverable_utils._download_floors_content"
    )
    task_full_client_zip_delivery.delay(
        client_id=client_db["id"],
        excluded_site_ids=[site["id"]] if exclude_sites else [],
    )
    assert mocked_download_floor_content.call_count == nbr_of_floor_content_download
    assert (
        mocked_gcp_upload_file_to_bucket.call_args.kwargs["destination_file_name"]
        == f"{client_db['name']}_delivery.zip"
    )
    assert (
        mocked_gcp_upload_file_to_bucket.call_args.kwargs[
            "destination_folder"
        ].as_posix()
        == f"deliverables/{client_db['id']}"
    )


def test_get_sample_surr_generation_chain(mocker, site, celery_eager):
    tasks_to_mock = (
        simulations_tasks.run_buildings_elevation_task,
        simulations_tasks.update_site_location_task,
        surroundings_tasks.generate_sample_surroundings_for_view_analysis_task,
    )
    mocked_runs = [
        mocker.patch.object(task, "run", return_value=True) for task in tasks_to_mock
    ]

    WorkflowGenerator(site_id=site["id"]).get_sample_surr_generation_chain().delay()

    for mock in mocked_runs:
        mock.assert_called_with(site_id=site["id"])


def test_get_vector_generation_tasks_chain_no_subsampling(mocker, site):
    wf = WorkflowGenerator(site_id=site["id"])
    task = wf._get_vector_generation_tasks_chain()
    assert task.name == "tasks.deliverables_tasks.generate_vector_files_task"


def test_get_vector_generation_tasks_chain_subsampling(mocker, site):
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"sub_sampling_number_of_clusters": 4}
    )
    wf = WorkflowGenerator(site_id=site["id"])
    chain = wf._get_vector_generation_tasks_chain()
    assert chain.name == "celery.chain"
    assert len(chain.tasks) == 2
