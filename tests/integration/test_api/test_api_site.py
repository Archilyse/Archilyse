import mimetypes
from collections import defaultdict
from http import HTTPStatus
from io import BytesIO

import pytest
from deepdiff import DeepDiff
from google.cloud import exceptions as gcloud_exceptions
from shapely.geometry import box
from werkzeug.datastructures import FileStorage

from brooks.classifications import CLASSIFICATIONS
from brooks.util.projections import REGIONS_CRS
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    DMS_PERMISSION,
    REGION,
    SIMULATION_VERSION,
    TASK_TYPE,
    USER_ROLE,
    PipelineCompletedCriteria,
)
from common_utils.exceptions import DBNotFoundException
from db_models import SiteDBModel
from handlers import PlanLayoutHandler, SiteHandler, SlamSimulationHandler
from handlers.db import (
    DmsPermissionDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    SlamSimulationDBHandler,
    SlamSimulationValidationDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
    UserDBHandler,
)
from slam_api.apis.site import (
    CopySiteView,
    NetAreaDistributionView,
    QAValidationTask,
    SampleSurroundings,
    SiteTaskView,
    SiteView,
    add_site,
    download_deliverable_zipfile,
    generate_features,
    get_ground_georeferenced_plans,
    get_site_pipelines,
    get_site_simulation_validation,
    get_sites,
    get_units_by_site,
    site_app,
    site_get_structure,
    site_get_surrounding_buildings,
    upload_custom_valuator_results,
)
from tasks import workflow_tasks
from tests.constants import UNIT_ID_1, USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.integration.utils import assert_site_consistency, response_message
from tests.utils import login_with


@pytest.mark.timeout(3, method="thread")
@login_as(["TEAMMEMBER"])
def test_get_sites(
    client, client_db, site, site_coordinates, login, site_region_proj_ch
):
    number_new_sites = 10
    SiteDBHandler.bulk_insert(
        [
            {
                "client_id": client_db["id"],
                "client_site_id": f"site_{i}",
                "name": "yep",
                "region": "Switzerland",
                "group_id": login["group"]["id"],
                **site_coordinates,
                "simulation_version": SIMULATION_VERSION.PH_01_2021.value,
                **site_region_proj_ch,
            }
            for i in range(number_new_sites)
        ]
    )

    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=get_sites,
            client_id=site["client_id"],
        )
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == number_new_sites + 1

    api_site = {x["id"]: x for x in response.json}[site["id"]]
    assert api_site.pop("ready") is False
    assert api_site["georef_proj"] == REGIONS_CRS[REGION.CH]
    assert api_site == site


@pytest.mark.parametrize(
    "permission_type,nbr_of_expected_sites",
    [
        (DMS_PERMISSION.READ, 1),
        (DMS_PERMISSION.WRITE, 1),
        (DMS_PERMISSION.READ_ALL, 2),
        (DMS_PERMISSION.WRITE_ALL, 2),
    ],
)
@login_as([USER_ROLE.DMS_LIMITED.name])
def test_get_sites_dms_limited(
    client, client_db, site, login, make_sites, permission_type, nbr_of_expected_sites
):
    from handlers.db import ClientDBHandler

    other_client = ClientDBHandler.add(name="OtherClient")
    _, other_site = make_sites(
        *(other_client, client_db), group_id=login["group"]["id"]
    )

    DmsPermissionDBHandler.add(
        site_id=other_site["id"]
        if permission_type in (DMS_PERMISSION.READ, DMS_PERMISSION.WRITE)
        else None,
        user_id=login["user"]["id"],
        rights=permission_type.name,
    )

    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=get_sites,
            client_id=client_db["id"],
        )
    )

    assert response.status_code == HTTPStatus.OK, response_message(response=response)

    assert len(response.json) == nbr_of_expected_sites


@login_as(["TEAMMEMBER"])
def test_get_sites_with_incorrect_client_site_id(client, site):
    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=get_sites,
            client_id="1/6663",
            client_site_id="1/6663",
        )
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@login_as(["TEAMMEMBER"])
def test_get_sites_with_client_site_id(client, client_db, site, make_sites, login):
    client_site_id_test = "c_s_id"

    # We create the site manually so the 'client_site_id' is not null
    SiteDBHandler.update({"id": site["id"]}, {"client_site_id": client_site_id_test})
    make_sites(client_db)

    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=get_sites,
            client_id=site["client_id"],
            client_site_id=client_site_id_test,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == 1, "Only one site filtered"
    assert (
        response.json[0]["client_site_id"] == client_site_id_test
    ), "Client site id fits with the filtered site"


@login_as(["ARCHILYSE_ONE_ADMIN"])
def test_get_dms_sites(
    client, client_db, site, site_coordinates, login, site_region_proj_ch
):
    """Request dms sites with coords and ensure only completed ones are returned"""
    completed_sites = 5
    COMPLETED_SITE_NAME = "complete_site"
    SiteDBHandler.bulk_insert(
        [
            {
                "client_id": client_db["id"],
                "client_site_id": f"site_{i}",
                "name": COMPLETED_SITE_NAME,
                "region": "Switzerland",
                "group_id": login["group"]["id"],
                "full_slam_results": ADMIN_SIM_STATUS.SUCCESS,
                "heatmaps_qa_complete": True,
                **site_coordinates,
                "simulation_version": SIMULATION_VERSION.PH_01_2021.value,
                **site_region_proj_ch,
            }
            for i in range(completed_sites)
        ]
    )

    pending_sites = 3
    SiteDBHandler.bulk_insert(
        [
            {
                "client_id": client_db["id"],
                "client_site_id": f"site_pending_{i}",
                "name": "yep",
                "region": "Switzerland",
                "group_id": login["group"]["id"],
                "full_slam_results": ADMIN_SIM_STATUS.PENDING,
                **site_coordinates,
                "simulation_version": SIMULATION_VERSION.PH_01_2021.value,
                **site_region_proj_ch,
            }
            for i in range(pending_sites)
        ]
    )

    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=get_sites,
            client_id=client_db["id"],
            dms_sites=True,
        )
    )

    assert response.status_code == HTTPStatus.OK
    assert len(response.json) == completed_sites
    for api_site in response.json:
        assert api_site["lat"] == site_coordinates["lat"]
        assert api_site["lon"] == site_coordinates["lon"]
        assert api_site["name"] == COMPLETED_SITE_NAME
        assert "client_site_id" in api_site


def test_run_features_returns_error(
    mocked_delay_slam_result,
    client,
    client_db,
    site_coordinates,
    login,
    site_region_proj_ch,
):
    """If conditions for site are not met return an error"""
    site = SiteDBHandler.add(
        client_id=client_db["id"],
        name="A nice site",
        region="Switzerland",
        **site_region_proj_ch,
        **site_coordinates,
    )
    response = client.post(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=generate_features,
            site_id=site["id"],
        ),
        follow_redirects=True,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST, response_message(
        response=response
    )
    assert "Some requirements are not met for the site requested:" in response.get_data(
        as_text=True
    )
    assert mocked_delay_slam_result.call_count == 0


def test_run_features_checks_if_task_is_already_running(
    mocked_delay_slam_result,
    client,
    client_db,
    site_coordinates,
    login,
    random_text,
    site_region_proj_ch,
):
    """If conditions for site are not met return an error"""
    site = SiteDBHandler.add(
        client_id=client_db["id"],
        name=random_text(),
        region="Switzerland",
        full_slam_results=ADMIN_SIM_STATUS.PROCESSING.name,
        **site_region_proj_ch,
        **site_coordinates,
    )
    response = client.post(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=generate_features,
            site_id=site["id"],
        ),
        follow_redirects=True,
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST, response_message(
        response=response
    )
    assert f"Analysis for site {site['id']} is already running" in response.get_data(
        as_text=True
    )
    assert mocked_delay_slam_result.call_count == 0


def test_run_features_do_not_flash_error(
    mocked_delay_slam_result,
    mocked_site_pipeline_completed,
    client,
    client_db,
    site_coordinates,
    login,
    make_buildings,
    make_plans,
    make_floor,
    random_text,
    site_region_proj_ch,
):
    """If conditions for site are met, it doesn't flash an error"""
    site = SiteDBHandler.add(
        client_id=client_db["id"],
        region="Switzerland",
        name=random_text(),
        pipeline_and_qa_complete=True,
        **site_region_proj_ch,
        **site_coordinates,
    )

    buildings = make_buildings(site)
    plans = make_plans(*buildings)
    _ = make_floor(building=buildings[0], plan=plans[0], floornumber=0)

    response = client.post(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=generate_features,
            site_id=site["id"],
        ),
        follow_redirects=True,
    )
    assert response.status_code == HTTPStatus.OK, response_message(response=response)
    assert mocked_delay_slam_result.call_count == 1  # digitize/analyze chain
    assert "Successfully started running analysis for site" in response.get_data(
        as_text=True
    )


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER])
def test_client_all_tasks(
    mocker, client, celery_eager, first_pipeline_complete_db_models, user_role
):
    login_with(client, USERS[user_role.name])
    analyze_task_mock = mocker.patch.object(
        workflow_tasks.run_digitize_analyze_client_tasks, "run", return_value=None
    )
    response = client.post(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=generate_features,
            site_id=first_pipeline_complete_db_models["site"]["id"],
        ),
        follow_redirects=True,
    )
    assert response.status_code == HTTPStatus.OK, response_message(response=response)

    analyze_task_mock.assert_called_with(
        site_id=first_pipeline_complete_db_models["site"]["id"]
    )


@pytest.mark.parametrize(
    "put_json,expected_call",
    [({"lat": 47.0}, 1), ({"name": "new name"}, 0)],
)
@login_as(["TEAMMEMBER"])
def test_update_site_triggers_task_only_if_location_changes(
    mocked_generate_geo_referencing_surroundings_for_site_task,
    client,
    site,
    put_json,
    expected_call,
    login,
    mocked_geolocator,
):

    response = client.put(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=SiteView,
            site_id=site["id"],
        ),
        json=put_json,
    )

    assert response.status_code == HTTPStatus.OK, response_message(response=response)
    assert (
        mocked_generate_geo_referencing_surroundings_for_site_task.call_count
        == expected_call
    )


@login_as(["TEAMMEMBER"])
def test_change_classification_scheme(client, site):
    assert (
        SiteDBHandler.get_by(id=site["id"])["classification_scheme"]
        == CLASSIFICATIONS.UNIFIED.name
    )
    response = client.put(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=SiteView,
            site_id=site["id"],
        ),
        json={"classification_scheme": "UNIFIED"},
    )

    assert response.status_code == HTTPStatus.OK
    assert (
        SiteDBHandler.get_by(id=site["id"])["classification_scheme"]
        == CLASSIFICATIONS.UNIFIED.name
    )


@pytest.mark.parametrize(
    "update_field",
    [
        column.name
        for column in SiteDBModel.__table__.columns
        if column.name
        not in {
            "basic_features_status",
            "validation_notes",
            "id",
            "gcs_ifc_file_links",
            "updated",
            "raw_dir",
            "client_id",
            "ifc_import_status",
            "created",
            "priority",
            "simulation_version",
            "gcs_buildings_link",
            "full_slam_results",
            "pipeline_and_qa_complete",
            "group_id",
            "georef_region",  # can't be set from outside
            "lat",  # Can't be set independently
            "lon",
            "heatmaps_qa_complete",
            "basic_features_error",
            "qa_validation",
            "labels",
            "site_plan_file",
            "ifc_import_exceptions",
            "sample_surr_task_state",
            "old_editor",
            "enforce_masterplan",
        }
    ],
)
@login_as(["TEAMMEMBER"])
def test_update_site_turns_site_to_unprocessed_for_specific_columns(
    client, site_delivered_simulated, update_field
):
    update_value = {
        "delivered": "True",
        "classification_scheme": "UNIFIED",
        "client_site_id": "new_client_site_id",
        "name": "new random name",
        "region": "new region",
        "georef_region": REGION.CZ.name,
        "lat": 999.0,
        "lon": 999.0,
        "sub_sampling_number_of_clusters": 10,
    }
    expected_set_to_unprocessed = {
        "delivered": False,
        "classification_scheme": True,
        "client_site_id": True,
        "name": True,
        "region": True,
        "lat": True,
        "lon": True,
        "sub_sampling_number_of_clusters": True,
    }

    assert update_field in update_value
    assert update_field in expected_set_to_unprocessed

    response = client.put(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=SiteView,
            site_id=site_delivered_simulated["id"],
        ),
        json={update_field: update_value[update_field]},
    )

    assert response.status_code == HTTPStatus.OK
    assert_site_consistency(
        site_id=site_delivered_simulated["id"],
        consistency_altered=expected_set_to_unprocessed[update_field],
    )


def test_update_site_sub_sampling_empty_change_value(client, site_delivered_simulated):
    SiteDBHandler.update(
        item_pks={"id": site_delivered_simulated["id"]},
        new_values={"sub_sampling_number_of_clusters": 10},
    )
    response = client.put(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=SiteView,
            site_id=site_delivered_simulated["id"],
        ),
        json={"sub_sampling_number_of_clusters": None},
    )

    assert response.status_code == HTTPStatus.OK
    assert_site_consistency(
        site_id=site_delivered_simulated["id"],
        consistency_altered=True,
    )
    site_updated = SiteDBHandler.get_by(id=site_delivered_simulated["id"])
    assert site_updated["sub_sampling_number_of_clusters"] is None


@pytest.mark.parametrize(
    "user_role", [USER_ROLE.TEAMMEMBER, USER_ROLE.ARCHILYSE_ONE_ADMIN]
)
def test_get_units_by_site(client, site, unit, login, user_role):
    login_with(client, USERS[user_role.name])
    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=get_units_by_site,
            site_id=site["id"],
        )
    )
    expected_response = [unit]
    assert response.status_code == HTTPStatus.OK
    assert response.json == expected_response


@login_as(["TEAMMEMBER"])
def test_site_get_structure(
    client, make_sites, make_clients, make_buildings, make_floor, plan, login
):
    clients = make_clients(1)
    sites = make_sites(*clients)
    site = sites[0]
    building_1, building_2 = make_buildings(*sites, *sites)
    floor_1 = make_floor(building=building_1, plan=plan, floornumber=0)
    floor_2 = make_floor(building=building_1, plan=plan, floornumber=1)
    floor_3 = make_floor(building=building_2, plan=plan, floornumber=1)

    response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=site_get_structure,
            site_id=site["id"],
        )
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json

    assert data["id"] == site["id"], "Wrong site"
    assert len(data["buildings"]) == 2, "Wrong number of buildings"
    buildings_by_id = {building["id"]: building for building in data["buildings"]}

    floors_building1 = buildings_by_id[building_1["id"]]["floors"]
    floors_building2 = buildings_by_id[building_2["id"]]["floors"]

    floor1 = floors_building1[str(floor_1["id"])]
    floor2 = floors_building1[str(floor_2["id"])]
    floor3 = floors_building2[str(floor_3["id"])]

    assert floor1["floor_number"] == 0, "Wrong floor 1 floor_number building 1"
    assert floor2["floor_number"] == 1, "Wrong floor 2 floor_number building 1"
    assert floor3["floor_number"] == 1, "Wrong floor 3 floor_number building 1"

    assert floor1["plan_id"] == plan["id"]
    assert floor2["plan_id"] == plan["id"]
    assert floor3["plan_id"] == plan["id"]


@pytest.mark.parametrize(
    "site_coordinates_to_put,expected_status_code,expected_call_count",
    [
        (
            {"lon": 46.9022094312901, "lat": 9.2246596978254},
            HTTPStatus.OK,
            1,
        ),
        (
            {"lon": 9.2246596978254, "lat": 46.9022094312901},
            HTTPStatus.OK,
            0,
        ),
        ({"lon": 9.2246596978254, "lat": 46.7}, HTTPStatus.OK, 1),
    ],
)
@login_as(["TEAMMEMBER"])
def test_put_site_task_should_be_triggered(
    mocked_generate_geo_referencing_surroundings_for_site_task,
    site_for_coordinate_validation,
    client,
    login,
    site_coordinates_to_put,
    expected_status_code,
    expected_call_count,
    mocked_geolocator,
):
    response = client.put(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=SiteView,
            site_id=site_for_coordinate_validation["id"],
        ),
        json=site_coordinates_to_put,
    )

    assert response.status_code == expected_status_code
    assert (
        mocked_generate_geo_referencing_surroundings_for_site_task.call_count
        == expected_call_count
    )


@pytest.mark.parametrize(
    "site_coordinates, expected_status_code, expected_call_count",
    [
        (
            {},
            HTTPStatus.BAD_REQUEST,
            0,
        ),
        (
            {"lat": 46.902209431290146, "lon": 9.224659697825485},
            HTTPStatus.CREATED,
            1,
        ),
    ],
)
@login_as(["TEAMMEMBER"])
def test_add_site_task_should_be_triggered(
    mocked_generate_geo_referencing_surroundings_for_site_task,
    client_db,
    client,
    login,
    site_coordinates,
    expected_status_code,
    expected_call_count,
    site_data,
    qa_without_site,
    mocked_geolocator,
):
    response = client.post(
        get_address_for(
            blueprint=site_app, use_external_address=False, view_function=add_site
        ),
        content_type="multipart/form-data",
        data={**site_data, **site_coordinates, "qa_id": qa_without_site["id"]},
    )
    assert response.status_code == expected_status_code
    assert (
        mocked_generate_geo_referencing_surroundings_for_site_task.call_count
        == expected_call_count
    )


@login_as(["TEAMMEMBER"])
def test_add_site_task_should_not_be_triggered_outside_ch(
    mocked_generate_geo_referencing_surroundings_for_site_task,
    client_db,
    client,
    login,
    site_data,
    qa_without_site,
    mocked_geolocator_outside_ch,
):
    response = client.post(
        get_address_for(
            blueprint=site_app, use_external_address=False, view_function=add_site
        ),
        content_type="multipart/form-data",
        data={
            **site_data,
            **{"lat": 58.68410068980541, "lon": -16.5914955288763},
            "qa_id": qa_without_site["id"],
            "sub_sampling_number_of_clusters": 10,
        },
    )
    assert response.status_code == HTTPStatus.CREATED, response.json
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 0


@login_as(["ADMIN", "TEAMMEMBER"])
def test_add_site_should_have_right_group(
    mocked_generate_geo_referencing_surroundings_for_site_task,
    client,
    client_db,
    login,
    site_coordinates,
    site_data,
    qa_without_site,
    mocked_geolocator,
):
    db_user = UserDBHandler.get_by(login=login["user"]["login"])

    response = client.post(
        get_address_for(
            blueprint=site_app, use_external_address=False, view_function=add_site
        ),
        content_type="multipart/form-data",
        data={**site_data, "qa_id": qa_without_site["id"]},
    )
    assert response.status_code == HTTPStatus.CREATED
    site = response.json

    created_site = SiteDBHandler.get_by(id=site["id"])
    if USER_ROLE.ADMIN in login["roles"]:
        assert created_site["group_id"] is None
    else:
        assert created_site["group_id"] == db_user["group_id"]

    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 1


@login_as(["TEAMMEMBER"])
def test_site_get_endpoint(site, client, login):
    response = client.get(
        get_address_for(blueprint=site_app, view_function=SiteView, site_id=site["id"])
    )

    assert response.status_code == HTTPStatus.OK, response.get_json()
    assert not DeepDiff(response.json, site, significant_digits=12)


class TestQAValidationTask:
    @login_as(["TEAMMEMBER"])
    def test_post_calls_qa_validation_workflow(
        self, site_w_qa_data, mocker, client, login
    ):
        import celery.canvas

        delay_mocked = mocker.patch.object(
            celery.canvas._chain, "delay", return_value=None
        )

        response = client.post(
            get_address_for(
                blueprint=site_app,
                view_function=QAValidationTask,
                site_id=site_w_qa_data["id"],
            )
        )

        assert response.status_code == HTTPStatus.OK, response.json
        delay_mocked.assert_called_once()

    @login_as(["TEAMMEMBER"])
    def test_post_returns_400_when_qa_task_is_running(
        self, site, client, login, basic_features_started
    ):
        site = SiteDBHandler.update(
            item_pks=dict(id=site["id"]),
            new_values=dict(basic_features_status=ADMIN_SIM_STATUS.PROCESSING.name),
        )

        response = client.post(
            get_address_for(
                blueprint=site_app, view_function=QAValidationTask, site_id=site["id"]
            )
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert response.json == {
            "msg": f'QA task for site {site["id"]} is already running'
        }
        # validate that nothing changed
        assert (
            SlamSimulationHandler.get_simulation(
                site_id=site["id"], task_type=TASK_TYPE.BASIC_FEATURES
            )
            == basic_features_started
        )
        assert SiteDBHandler.get_by(id=site["id"]) == site

    @login_as(["TEAMMEMBER"])
    def test_post_returns_400_when_simulations_are_running(self, site, client, login):
        site = SiteDBHandler.update(
            item_pks=dict(id=site["id"]),
            new_values=dict(
                basic_features_status=ADMIN_SIM_STATUS.SUCCESS.name,
                full_slam_results=ADMIN_SIM_STATUS.PROCESSING.name,
            ),
        )

        response = client.post(
            get_address_for(
                blueprint=site_app, view_function=QAValidationTask, site_id=site["id"]
            )
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert response.json == {
            "msg": f"Cannot start QA task while simulations for {site['id']} are running."
        }
        assert SiteDBHandler.get_by(id=site["id"]) == site

    @login_as(["TEAMMEMBER"])
    def test_post_returns_400_when_qa_data_is_missing(
        self, site, client, plan, login, qa_db_empty
    ):
        response = client.post(
            get_address_for(
                blueprint=site_app, view_function=QAValidationTask, site_id=site["id"]
            )
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.json
        assert response.json == {"msg": f"Site {site['id']} doesn't have QA data"}
        # validate that nothing changed
        assert not SlamSimulationDBHandler.exists(
            site_id=site["id"], type=TASK_TYPE.BASIC_FEATURES.name
        )
        assert SiteDBHandler.get_by(id=site["id"]) == site


@pytest.mark.parametrize(
    "pipeline_status, task_status, expected_response_code, expected_response_msg",
    [
        (True, ADMIN_SIM_STATUS.UNPROCESSED.value, HTTPStatus.OK, ""),
        (
            False,
            ADMIN_SIM_STATUS.UNPROCESSED.value,
            HTTPStatus.BAD_REQUEST,
            "Pipeline not completed for all plans",
        ),
        (
            True,
            ADMIN_SIM_STATUS.PROCESSING.value,
            HTTPStatus.BAD_REQUEST,
            "Sample Surroundings generation for site ",
        ),
        (
            False,
            ADMIN_SIM_STATUS.PROCESSING.value,
            HTTPStatus.BAD_REQUEST,
            "Sample Surroundings generation for site ",
        ),
    ],
)
def test_enqueue_sample_surroundings_task(
    mocker,
    client,
    login,
    site,
    pipeline_status,
    task_status,
    expected_response_code,
    expected_response_msg,
):
    from celery.canvas import Signature

    # Mocks any call to delay method
    mocked_run = mocker.patch.object(
        Signature,
        "delay",
        return_value=None,
    )
    mocker.patch.object(
        SiteHandler,
        SiteHandler.pipeline_completed_criteria.__name__,
        return_value=PipelineCompletedCriteria(
            labelled=pipeline_status,
            classified=pipeline_status,
            splitted=pipeline_status,
            units_linked=pipeline_status,
            georeferenced=pipeline_status,
        ),
    )
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"sample_surr_task_state": task_status}
    )

    response = client.post(
        get_address_for(
            blueprint=site_app,
            view_function=SampleSurroundings,
            site_id=site["id"],
        )
    )

    assert response.status_code == expected_response_code, response.json
    if expected_response_msg:
        assert expected_response_msg in response.json["msg"]

    if expected_response_code == HTTPStatus.OK:
        mocked_run.assert_called_once()
        assert (
            SiteDBHandler.get_by(id=site["id"])["sample_surr_task_state"]
            == ADMIN_SIM_STATUS.PENDING.value
        )
    else:
        mocked_run.assert_not_called()
        assert (
            SiteDBHandler.get_by(id=site["id"])["sample_surr_task_state"] == task_status
        )


def test_download_zip_file(site, mocker, client, login):
    from handlers import GCloudStorageHandler

    def fake_download(local_file_name, *args, **kwargs):
        with local_file_name.open("w") as f:
            f.write("FOO/BAR")

    patched = mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file.__name__,
        side_effect=fake_download,
    )

    response = client.get(
        get_address_for(
            blueprint=site_app,
            view_function=download_deliverable_zipfile,
            site_id=site["id"],
        )
    )

    assert response.status_code == HTTPStatus.OK
    assert response.content_type == mimetypes.types_map[".zip"]
    patched.assert_called()


def test_download_sample_surr_html_file(site, mocker, client, login):
    from handlers import GCloudStorageHandler

    def fake_download(local_file_name, *args, **kwargs):
        with local_file_name.open("w") as f:
            f.write("FOO/BAR")

    mocked_download = mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file.__name__,
        side_effect=fake_download,
    )

    response = client.get(
        get_address_for(
            blueprint=site_app,
            view_function=SampleSurroundings,
            site_id=site["id"],
        )
    )

    assert response.status_code == HTTPStatus.OK
    assert response.content_type == f'{mimetypes.types_map[".html"]}; charset=utf-8'
    mocked_download.assert_called()


def test_download_sample_surr_html_file_not_found(site, mocker, client, login):
    from handlers import GCloudStorageHandler

    mocked_download = mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file.__name__,
        side_effect=gcloud_exceptions.NotFound("foo"),
    )

    response = client.get(
        get_address_for(
            blueprint=site_app,
            view_function=SampleSurroundings,
            site_id=site["id"],
        )
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    mocked_download.assert_called()


def test_download_zip_file_not_found(site, mocker, client, login):
    from handlers import GCloudStorageHandler

    mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.download_file.__name__,
        side_effect=gcloud_exceptions.NotFound("foo"),
    )
    response = client.get(
        get_address_for(
            blueprint=site_app,
            view_function=download_deliverable_zipfile,
            site_id=site["id"],
        )
    )

    assert response.status_code == HTTPStatus.NOT_FOUND


def test_site_get_building_footprints(
    mocker, client, site, plan, login, building_surroundings_path
):
    from handlers import site_handler

    with building_surroundings_path.open("rb") as f:
        mocked_gcp_download = mocker.patch.object(
            site_handler.GCloudStorageHandler,
            "download_bytes_from_media_link",
            return_value=f.read(),
        )

    new_values = {"lon": 47.5642388562567, "lat": 7.636568666258004}
    SiteDBHandler.update(item_pks=dict(id=site["id"]), new_values=new_values)

    site_response = client.get(
        get_address_for(
            blueprint=site_app,
            use_external_address=False,
            view_function=site_get_surrounding_buildings,
            site_id=site["id"],
        )
    )

    assert site_response.status_code == HTTPStatus.OK

    assert mocked_gcp_download.call_count == 1
    assert len(site_response.json["data"]) == 26


def test_upload_custom_valuator_results_success(
    client, login, units_with_vector_with_balcony, fixtures_path
):
    # Given
    site_id = units_with_vector_with_balcony[0]["site_id"]
    fields = ("ph_final_gross_rent_annual_m2", "ph_final_gross_rent_adj_factor")

    with fixtures_path.joinpath("ph_upload/rent_example.xlsx").open("rb") as f:
        data = f.read()

    # When a xlsx file is uploaded
    response = client.post(
        get_address_for(
            blueprint=site_app,
            view_function=upload_custom_valuator_results,
            use_external_address=False,
            site_id=site_id,
        ),
        content_type="multipart/form-data",
        data={
            "custom_valuator_results": FileStorage(
                stream=BytesIO(data),
                filename="ph_file.xlsx",
                content_type="text/xlsx",
            )
        },
    )

    # Then
    assert response.status_code == HTTPStatus.OK, response.data
    units_by_client_id = defaultdict(list)
    for unit in UnitDBHandler.find(site_id=site_id):
        units_by_client_id[unit["client_id"]].append(unit)

    for unit in UnitDBHandler.find(site_id=site_id):
        for field in fields:
            assert unit[field] != 0


def test_upload_custom_valuator_results_wrong_headers(
    client, login, units_with_vector_with_balcony, fixtures_path
):
    # Given
    site_id = units_with_vector_with_balcony[0]["site_id"]

    with fixtures_path.joinpath("ph_upload/rent_wrong_example.xlsx").open("rb") as f:
        data = f.read()

    # When a xlsx file is uploaded
    response = client.post(
        get_address_for(
            blueprint=site_app,
            view_function=upload_custom_valuator_results,
            use_external_address=False,
            site_id=site_id,
        ),
        content_type="multipart/form-data",
        data={
            "custom_valuator_results": FileStorage(
                stream=BytesIO(data),
                filename="ph_file.xlsx",
                content_type="text/xlsx",
            )
        },
    )

    # Then
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data
    assert response.json["msg"].startswith(
        "The file does not contain the expected header at row 7"
    )


def test_upload_custom_valuator_results_returns_422_on_invalid_type(
    client, site, units_with_vector_with_balcony, login
):
    csv_data = (
        "client_unit_id,ph_final_gross_rent_annual_m2,ph_arch_adj_factor,ph_final_sale_price_m2,ph_final_sale_price_adj_factor\n"
        "GS20.00.01,7000,2,7000,2\n"
    )

    # When
    # a csv file is uploaded
    response = client.post(
        get_address_for(
            blueprint=site_app,
            view_function=upload_custom_valuator_results,
            use_external_address=False,
            site_id=site["id"],
        ),
        content_type="multipart/form-data",
        data={
            "custom_valuator_results": FileStorage(
                stream=BytesIO(csv_data.encode("utf-8")),
                filename="my_file.csv",
                content_type="text/csv",
            )
        },
    )
    # Then
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data


def test_delete_site(client, site, plan, building, login):
    assert (
        HTTPStatus.OK
        == client.delete(
            get_address_for(
                blueprint=site_app,
                use_external_address=False,
                view_function=SiteView,
                site_id=site["id"],
            )
        ).status_code
    )
    with pytest.raises(DBNotFoundException):
        SiteDBHandler.get_by(id=site["id"])


def test_get_pipelines_by_site_endpoint(client, site, plan, building, login):
    url = get_address_for(
        blueprint=site_app,
        view_function=get_site_pipelines,
        site_id=site["id"],
        use_external_address=False,
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK, response.data
    json_response = response.json
    json_response[0].pop("created")
    json_response[0].pop("updated")
    assert json_response == [
        {
            "client_building_id": "1",
            "building_housenumber": "20-22",
            "building_id": building["id"],
            "classified": False,
            "client_site_id": "Leszku-payaso",
            "floor_numbers": [],
            "georeferenced": False,
            "id": plan["id"],
            "labelled": False,
            "splitted": False,
            "units_linked": False,
            "is_masterplan": False,
        }
    ]


def test_get_pipelines_by_site_endpoint_plans_without_units(
    client, site, plan_classified_scaled_georeferenced, floor, building, login
):
    PlanDBHandler.update(
        item_pks={"id": plan_classified_scaled_georeferenced["id"]},
        new_values={"without_units": True},
    )
    url = get_address_for(
        blueprint=site_app,
        view_function=get_site_pipelines,
        site_id=site["id"],
        use_external_address=False,
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK, response.data
    json_response = response.json
    json_response[0].pop("created")
    json_response[0].pop("updated")
    assert json_response == [
        {
            "client_building_id": "1",
            "building_housenumber": "20-22",
            "building_id": building["id"],
            "classified": True,
            "client_site_id": "Leszku-payaso",
            "floor_numbers": [floor["id"]],
            "georeferenced": True,
            "id": plan_classified_scaled_georeferenced["id"],
            "labelled": True,
            "splitted": True,
            "units_linked": True,
            "is_masterplan": False,
        }
    ]


def test_get_site_simulation_validation(
    client, site, login, validation_unit_stats_results
):
    SlamSimulationValidationDBHandler.add(
        site_id=site["id"],
        results=validation_unit_stats_results,
    )

    url = get_address_for(
        blueprint=site_app,
        view_function=get_site_simulation_validation,
        site_id=site["id"],
        use_external_address=False,
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK, response.data
    assert response.json == validation_unit_stats_results


@pytest.mark.parametrize(
    "existing_floors, num_plans_expected",
    [
        ([0, 1, 2], 1),
        ([-1, 0], 2),
        ([-1], 1),
        ([-2], 1),
        ([3], 1),
        ([3, 4, 5], 1),
        ([0, 3, 4, 5], 1),
        ([-1, 0, 3, 4, 5], 2),
    ],
)
def test_get_ground_georeferenced_plans(
    mocker,
    client,
    site,
    make_floor,
    make_plans,
    building,
    login,
    existing_floors,
    num_plans_expected,
):
    mocker.patch.object(
        PlanLayoutHandler,
        PlanLayoutHandler.get_georeferenced_footprint.__name__,
        return_value=box(0, 0, 10, 10),
    )
    for floor_number in existing_floors:
        (plan,) = make_plans(building)
        make_floor(building=building, plan=plan, floornumber=floor_number)

    url = get_address_for(
        blueprint=site_app,
        view_function=get_ground_georeferenced_plans,
        site_id=site["id"],
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK, response.data

    assert len(response.json["features"]) == num_plans_expected
    assert set(response.json["features"][0].keys()) == {
        "geometry",
        "type",
    }


def test_get_ground_georeferenced_multiple_buildings(
    mocker,
    client,
    site,
    make_floor,
    make_plans,
    make_buildings,
    login,
):
    mocker.patch.object(
        PlanLayoutHandler,
        PlanLayoutHandler.get_georeferenced_footprint.__name__,
        return_value=box(0, 0, 10, 10),
    )
    building1, building2 = make_buildings(site, site)
    plans = make_plans(building1, building1, building1, building2, building2)

    make_floor(building=building1, plan=plans[0], floornumber=0)
    make_floor(building=building1, plan=plans[1], floornumber=-1)
    make_floor(building=building1, plan=plans[2], floornumber=4)

    make_floor(building=building2, plan=plans[3], floornumber=10)
    make_floor(building=building2, plan=plans[4], floornumber=5)

    url = get_address_for(
        blueprint=site_app,
        view_function=get_ground_georeferenced_plans,
        site_id=site["id"],
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK, response.data

    # 3 floors, 2 for the first building (0 and -1), 1 for the second (5)
    assert len(response.json["features"]) == 3
    assert set(response.json["features"][0].keys()) == {
        "geometry",
        "type",
    }


@login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
def test_net_area_distribution(
    client, client_db, login, first_pipeline_complete_db_models
):
    site_id = first_pipeline_complete_db_models["site"]["id"]
    building_id = first_pipeline_complete_db_models["building"]["id"]
    floor_id = first_pipeline_complete_db_models["floor"]["id"]
    random_unit_id = 50000
    unit_net_area = 80.51168821392893

    analysis_url = get_address_for(
        blueprint=site_app,
        use_external_address=False,
        view_function=NetAreaDistributionView,
    )

    # This unit does not have basic features and should not affect results
    UnitDBHandler.add(
        id=random_unit_id,
        site_id=site_id,
        plan_id=first_pipeline_complete_db_models["plan"]["id"],
        floor_id=first_pipeline_complete_db_models["floor"]["id"],
        apartment_no=5,
    )

    expected_distribution_by_floor_id = {
        str(random_unit_id): 0,
        "100": unit_net_area,
        "200": unit_net_area,
        "300": unit_net_area,
        "301": unit_net_area,
    }

    # Aggregated by site
    response = client.get(f"{analysis_url}?site_id={site_id}")
    assert response.json == {str(building_id): pytest.approx(unit_net_area * 4)}

    # Now aggregated by building, where endpoint returns distribution by floors & by units
    response = client.get(f"{analysis_url}?building_id={building_id}")
    assert response.json["floors"] == {str(floor_id): pytest.approx(unit_net_area * 4)}
    assert response.json["units"] == expected_distribution_by_floor_id

    # Now aggregated by floor_id
    response = client.get(f"{analysis_url}?floor_id={floor_id}")
    assert response.json == expected_distribution_by_floor_id

    # Now no param should raise an error
    response = client.get(f"{analysis_url}")
    assert response.status_code == HTTPStatus.BAD_REQUEST


@login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
def test_net_area_distribution_by_area_id(
    client, client_db, login, first_pipeline_complete_db_models
):
    UnitDBHandler.add(
        site_id=first_pipeline_complete_db_models["site"]["id"],
        plan_id=first_pipeline_complete_db_models["plan"]["id"],
        floor_id=first_pipeline_complete_db_models["floor"]["id"],
        apartment_no=5,
    )

    analysis_url = get_address_for(
        blueprint=site_app,
        use_external_address=False,
        view_function=NetAreaDistributionView,
        unit_id=UNIT_ID_1,
    )
    unit_response = client.get(analysis_url)
    assert unit_response.status_code == HTTPStatus.OK, unit_response.json
    expected = {
        str(unit_area["area_id"]): 21.09984728932049
        for unit_area in UnitAreaDBHandler.find(unit_id=UNIT_ID_1)
    }

    assert unit_response.json == pytest.approx(expected, abs=0.001)


class TestSiteTaskView:
    @pytest.mark.parametrize(
        "task_name",
        [
            "generate_unit_plots_task",
            "generate_energy_reference_area_task",
            "generate_ifc_file_task",
            "generate_vector_files_task",
            "all_deliverables",
        ],
    )
    @login_as(["ADMIN"])
    def test_post_calls_task(
        self,
        site_w_qa_data,
        mocker,
        client,
        login,
        celery_eager,
        generate_ifc_file_mocked,
        generate_energy_reference_area_task_mocked,
        generate_unit_plots_task_mocked,
        generate_vector_files_task_mocked,
        slam_results_success_mocked,
        task_name,
    ):
        from slam_api.apis import site

        post_message_to_slack_mock = mocker.patch.object(
            site, site.post_message_to_slack.__name__
        )
        deliverable_tasks_mock = mocker.patch.object(
            workflow_tasks.WorkflowGenerator,
            "get_deliverables_tasks",
        )

        MOCKS = {
            "generate_ifc_file_task": generate_ifc_file_mocked,
            "generate_energy_reference_area_task": generate_energy_reference_area_task_mocked,
            "generate_unit_plots_task": generate_unit_plots_task_mocked,
            "generate_vector_files_task": generate_vector_files_task_mocked,
            "slam_results_success": slam_results_success_mocked,
            "all_deliverables": deliverable_tasks_mock,
        }

        response = client.post(
            get_address_for(
                blueprint=site_app,
                view_function=SiteTaskView,
                site_id=site_w_qa_data["id"],
                task_name=task_name,
            )
        )

        assert response.status_code == HTTPStatus.OK, response.json
        MOCKS[task_name].assert_called_once()
        post_message_to_slack_mock.assert_called_once()

    @login_as(["ADMIN"])
    def test_post_set_to_success_for_processing_site(
        self,
        site_w_qa_data,
        mocker,
        client,
        login,
        celery_eager,
        generate_ifc_file_mocked,
    ):
        SiteDBHandler.update(
            item_pks={"id": site_w_qa_data["id"]},
            new_values={"full_slam_results": ADMIN_SIM_STATUS.PROCESSING.name},
        )

        response = client.post(
            get_address_for(
                blueprint=site_app,
                view_function=SiteTaskView,
                site_id=site_w_qa_data["id"],
                task_name="slam_results_success",
            )
        )

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json


class TestCopySiteView:
    def test_copy_site_launch_copy_site_task(self, mocker, client, site):
        from api.slam_api.apis.site import copy_site_task

        copy_site_task_mocked = mocker.patch.object(
            copy_site_task,
            "delay",
            return_value=None,
        )

        response = client.post(
            get_address_for(
                blueprint=site_app, view_function=CopySiteView, site_id=site["id"]
            ),
            json={"client_target_id": 12},
        )
        assert response.status_code == HTTPStatus.OK

        copy_site_task_mocked.assert_called_once_with(
            target_client_id=12, site_id_to_copy=site["id"], copy_area_types=True
        )

    def test_copy_site_bad_params(self, mocker, client, site):
        from api.slam_api.apis.site import copy_site_task

        copy_site_task_mocked = mocker.patch.object(
            copy_site_task,
            "delay",
            return_value=None,
        )

        response = client.post(
            get_address_for(
                blueprint=site_app, view_function=CopySiteView, site_id=site["id"]
            ),
            json={"foo": 12},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

        copy_site_task_mocked.assert_not_called()
