import pytest

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS,
    SIMULATION_VERSION,
    PipelineCompletedCriteria,
    SurroundingType,
)
from common_utils.exceptions import (
    DependenciesUnMetSimulationException,
    TaskAlreadyRunningException,
)
from handlers import SiteHandler
from handlers.db import SiteDBHandler
from handlers.quavis import SLAMQuavisHandler
from surroundings.visualization import sourroundings_3d_figure
from tasks.surroundings_tasks import (
    enqueue_sample_surroundings_task,
    generate_sample_surroundings_for_view_analysis_task,
)


def test_generate_sample_surroundings_for_view_analysis_task(
    celery_eager, mocker, mocked_gcp_upload_file_to_bucket, site
):
    triangles = [(0, 0, 0), (0, 1, 0), (1, 1, 0)]
    mocked_generate_view_surroundings = mocker.patch.object(
        SiteHandler,
        SiteHandler.generate_view_surroundings.__name__,
        return_value=iter([(SurroundingType.GROUNDS, triangles)]),
    )
    mocked_get_site_triangles = mocker.patch.object(
        SLAMQuavisHandler,
        SLAMQuavisHandler.get_site_triangles.__name__,
        return_value=iter([("foo", triangles)]),
    )
    mocked_create_3d = mocker.patch.object(
        sourroundings_3d_figure,
        sourroundings_3d_figure.create_3d_surroundings_from_triangles_per_type.__name__,
    )

    generate_sample_surroundings_for_view_analysis_task.delay(site_id=site["id"])

    call_args = mocked_generate_view_surroundings.call_args_list[0][1]
    assert call_args["sample"]
    assert call_args["site_info"]["id"] == site["id"]
    assert (
        call_args["site_info"]["sample_surr_task_state"]
        == ADMIN_SIM_STATUS.PROCESSING.value
    )

    mocked_create_3d.assert_called_once()
    assert not mocked_create_3d.call_args.kwargs["auto_open"]

    assert mocked_get_site_triangles.call_args.kwargs["entity_info"]["id"] == site["id"]
    assert mocked_get_site_triangles.call_args.kwargs[
        "simulation_version"
    ] == SIMULATION_VERSION(site["simulation_version"])

    mocked_gcp_upload_file_to_bucket.assert_called_once()
    assert mocked_gcp_upload_file_to_bucket.call_args.kwargs[
        "destination_file_name"
    ] == SiteHandler.get_surroundings_sample_path(site_id=site["id"])
    assert (
        mocked_gcp_upload_file_to_bucket.call_args.kwargs["destination_folder"]
        == GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS
    )
    assert (
        SiteDBHandler.get_by(id=site["id"])["sample_surr_task_state"]
        == ADMIN_SIM_STATUS.SUCCESS.value
    )


def test_generate_sample_surroundings_for_view_analysis_not_ready(
    celery_eager, mocker, mocked_gcp_upload_file_to_bucket, site
):
    mocker.patch.object(
        SiteHandler,
        SiteHandler.pipeline_completed_criteria.__name__,
        return_value=PipelineCompletedCriteria(
            labelled=False,
            classified=True,
            splitted=True,
            units_linked=True,
            georeferenced=True,
        ),
    )
    with pytest.raises(DependenciesUnMetSimulationException):
        enqueue_sample_surroundings_task(site_id=site["id"])


def test_generate_sample_surroundings_for_view_analysis_already_running(
    celery_eager, mocked_gcp_upload_file_to_bucket, site
):
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"sample_surr_task_state": ADMIN_SIM_STATUS.PROCESSING.value},
    )
    with pytest.raises(TaskAlreadyRunningException):
        enqueue_sample_surroundings_task(site_id=site["id"])
