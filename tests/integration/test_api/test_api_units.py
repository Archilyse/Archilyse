import uuid
from http import HTTPStatus

import pytest
from deepdiff import DeepDiff
from shapely.geometry import shape

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    DMS_PERMISSION,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    TASK_TYPE,
    USER_ROLE,
)
from common_utils.exceptions import DBNotFoundException
from handlers import GCloudStorageHandler, SlamSimulationHandler
from handlers.db import UnitAreaDBHandler, UnitDBHandler
from handlers.utils import get_client_bucket_name
from slam_api.apis.unit import (
    PutUnitAreaView,
    UnitCollectionView,
    UnitView,
    get_bytes_of_unit_deliverable,
    get_unit_simple_brooks_model_api,
    simulation_results,
    unit_app,
)
from tests.constants import UNIT_ID_1, USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.integration.utils import add_site_permissions, change_site_ownership
from tests.utils import login_with


@pytest.fixture
def unit_area(unit, areas_db):
    return UnitAreaDBHandler.add(unit_id=unit["id"], area_id=areas_db[0]["id"])


@pytest.mark.parametrize(
    "unit_id,add_results_to_db,expected_status",
    [
        (UNIT_ID_1, True, HTTPStatus.OK),
        (UNIT_ID_1, False, HTTPStatus.NOT_FOUND),
        (1337, False, HTTPStatus.NOT_FOUND),
    ],
)
@pytest.mark.parametrize("georeferenced", [True, False])
def test_get_unit_view_results(
    mocker,
    client,
    login,
    first_pipeline_complete_db_models,
    view_sun_simulation_finished,
    potential_view_results_test_api_simulations,
    georeferenced,
    unit_id,
    add_results_to_db,
    expected_status,
):
    from handlers import plan_layout_handler

    georeferencing_transformation_spy = mocker.spy(
        plan_layout_handler, "GeoreferencingTransformation"
    )

    if add_results_to_db:
        some_db_area_id = UnitAreaDBHandler.find(
            unit_id=unit_id, output_columns=["area_id"]
        )[0]["area_id"]
        results = {
            some_db_area_id: list(potential_view_results_test_api_simulations.values())[
                0
            ]["area"]
        }
        SlamSimulationHandler.store_results(
            run_id=view_sun_simulation_finished["run_id"], results={unit_id: results}
        )

    url = get_address_for(
        blueprint=unit_app,
        view_function=simulation_results,
        simulation_type=TASK_TYPE.VIEW_SUN.name,
        unit_id=unit_id,
        georeferenced=georeferenced,
        use_external_address=False,
    )
    response = client.get(url)

    assert response.status_code == expected_status, response.data
    expected_dimensions = {
        "observation_points",
        "site",
        "ground",
        "buildings",
        "water",
        "streets",
        "greenery",
        "railway_tracks",
        "isovist",
        "sky",
        "sun-2018-03-21 07:00:00+00:00",
        "sun-2018-06-21 07:00:00+00:00",
        "sun-2018-12-21 07:00:00+00:00",
        "sun-2018-03-21 12:00:00+00:00",
        "sun-2018-06-21 12:00:00+00:00",
        "sun-2018-12-21 12:00:00+00:00",
        "sun-2018-03-21 17:00:00+00:00",
        "sun-2018-06-21 17:00:00+00:00",
        "sun-2018-12-21 17:00:00+00:00",
    }
    if expected_status == HTTPStatus.OK:
        result = response.json

        assert {k for k in result.keys()} == expected_dimensions

        if not georeferenced:
            assert georeferencing_transformation_spy.call_count == 1
        else:
            assert georeferencing_transformation_spy.call_count == 0


@pytest.mark.parametrize(
    "simulations_in_db,expected_result",
    [
        (
            [
                (
                    TASK_TYPE.VIEW_SUN,
                    {"greenery": [1, 1], "sun-2018-12-31 07:00+00:00": [1, 1]},
                ),
                (
                    TASK_TYPE.SUN_V2,
                    {"greenery": [2, 2], "sun-2018-12-31 10:00+01:00": [2, 2]},
                ),
            ],
            {"greenery": [1, 1], "sun-2018-12-31 10:00+01:00": [2, 2]},
        ),
        (
            [
                (
                    TASK_TYPE.VIEW_SUN,
                    {"greenery": [1, 1], "sun-2018-12-31 07:00+00:00": [1, 1]},
                )
            ],
            {"greenery": [1, 1], "sun-2018-12-31 07:00+00:00": [1, 1]},
        ),
    ],
)
def test_get_unit_view_results_returns_view_sun_if_sun_v2_is_not_available(
    first_pipeline_complete_db_models, client, login, simulations_in_db, expected_result
):
    some_unit_id = first_pipeline_complete_db_models["units"][0]["id"]
    some_area_id = UnitAreaDBHandler.find(unit_id=some_unit_id)[0]["area_id"]
    expected_result.update({"observation_points": []})

    for task_type, results in simulations_in_db:
        run_id = str(uuid.uuid4())
        SlamSimulationHandler.register_simulation(
            run_id=run_id,
            site_id=first_pipeline_complete_db_models["site"]["id"],
            state=ADMIN_SIM_STATUS.SUCCESS,
            task_type=task_type,
        )
        SlamSimulationHandler.store_results(
            run_id=run_id, results={some_unit_id: {some_area_id: results}}
        )
    url = get_address_for(
        blueprint=unit_app,
        view_function=simulation_results,
        simulation_type=TASK_TYPE.VIEW_SUN.name,
        unit_id=some_unit_id,
        georeferenced=True,
        use_external_address=False,
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK, response.data

    assert response.json == expected_result


def test_get_unit_results_resolution(client, slam_simulation_with_results, unit):
    """This includes saved results with resolution parameter"""

    # when api queried for values of the unit
    url = get_address_for(
        blueprint=unit_app,
        view_function=simulation_results,
        unit_id=unit["id"],
        simulation_type=TASK_TYPE.VIEW_SUN.name,
        georeferenced=True,
        use_external_address=False,
    )
    response = client.get(url)

    expected = {
        # Obs points are projected to lat lon
        "observation_points": [
            [32.12449784593359, -19.91798993787843, 1],
            [32.12450920106198, -19.91798371149029, 1],
            [32.12452055619028, -19.91797748510002, 1],
            [32.12449784593359, -19.91798993787843, 1],
            [32.12450920106198, -19.91798371149029, 1],
            [32.12452055619028, -19.91797748510002, 1],
        ],
        "resolution": 0.25,
        "traffic_day": [100, 200, 300, 400, 500, 600],
        "traffic_night": [1000, 2000, 3000, 4000, 5000, 6000],
    }

    assert response.json == expected


def test_get_unit_connectivity_results_formatted(
    client,
    plan_georeferenced,
    make_classified_plans,
    floor,
    unit,
    site,
):
    # given saved results
    SlamSimulationHandler.register_simulation(
        site_id=site["id"],
        run_id="12345",
        task_type=TASK_TYPE.CONNECTIVITY,
        state=ADMIN_SIM_STATUS.SUCCESS,
    )
    make_classified_plans(plan_georeferenced, db_fixture_ids=False)
    area_ids = [1, 2]
    for area_id in area_ids:
        UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area_id)

    SlamSimulationHandler.store_results(
        run_id="12345",
        results={
            unit["id"]: {
                area_id: {
                    "observation_points": [
                        [1261577.7136439893, 2696508.8727149838, 0],
                        [1261577.7136439893, 2696510.6227149838, 0],
                    ],
                    "connectivity_pagerank": [1.0, 0.001],
                }
                for area_id in area_ids
            }
        },
    )
    url = get_address_for(
        blueprint=unit_app,
        view_function=simulation_results,
        unit_id=unit["id"],
        simulation_type=TASK_TYPE.CONNECTIVITY.name,
        georeferenced=True,
        use_external_address=False,
    )
    response = client.get(url)
    assert not DeepDiff(
        {
            "connectivity_pagerank": [1.0, 0.001, 1.0, 0.001],
            "observation_points": [
                [47.49786971525917, 8.719476641459478, 0.0],
                [47.49786945833071, 8.719499863105598, 0.0],
                [47.49786971525917, 8.719476641459478, 0.0],
                [47.49786945833071, 8.719499863105598, 0.0],
            ],
        },
        response.json,
        significant_digits=8,
    )


@login_as(["ARCHILYSE_ONE_ADMIN"])
def test_get_unit_view_results_unauthorized_user(
    client, login, first_pipeline_complete_db_models
):
    url = get_address_for(
        blueprint=unit_app,
        view_function=simulation_results,
        simulation_type=TASK_TYPE.VIEW_SUN.name,
        unit_id=UNIT_ID_1,
        use_external_address=False,
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.FORBIDDEN


def test_get_unit_simple_brooks(client, login, first_pipeline_complete_db_models):
    url = get_address_for(
        blueprint=unit_app,
        view_function=get_unit_simple_brooks_model_api,
        unit_id=UNIT_ID_1,
        use_external_address=False,
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert {"features", "openings", "separators"} == set(response.json.keys())
    assert set(response.json["openings"].keys()) == {"DOOR", "WINDOW"}
    assert set(response.json["separators"].keys()) == {"WALL"}

    for separator in response.json["separators"]["WALL"]:
        assert shape(separator["geometry"])

    for opening in response.json["openings"]["DOOR"]:
        assert shape(opening["geometry"])


def test_get_api_unit(client, login, unit):
    url = get_address_for(
        blueprint=unit_app,
        use_external_address=False,
        view_function=UnitView,
        unit_id=unit["id"],
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {
        "client_id": unit["client_id"],
        "floor_id": unit["floor_id"],
        "id": unit["id"],
    }


def test_delete_unit(client, login, unit):
    url = get_address_for(
        blueprint=unit_app,
        use_external_address=False,
        view_function=UnitView,
        unit_id=unit["id"],
    )
    response = client.delete(url)
    assert response.status_code == HTTPStatus.NO_CONTENT
    with pytest.raises(DBNotFoundException):
        UnitDBHandler.get_by(id=unit["id"])


def test_get_api_units_by_floor(client, login, building, plan, make_floor, make_units):
    floor0 = make_floor(building=building, plan=plan, floornumber=0)
    floor1 = make_floor(building=building, plan=plan, floornumber=1)
    make_units(*[floor0, floor1])

    url = get_address_for(
        blueprint=unit_app,
        use_external_address=False,
        view_function=UnitCollectionView,
        floor_id=floor1["id"],
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK

    response_units = response.json
    for unit in response_units:
        assert unit["floor_id"] == floor1["id"]


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.DMS_LIMITED])
def test_put_unit_area_labels(client, site, unit_area, user_role):
    user = login_with(client, USERS[user_role.name])["user"]
    change_site_ownership(site["id"], user["client_id"])
    add_site_permissions(site["id"], user["id"], DMS_PERMISSION.READ.name)
    response = client.put(
        get_address_for(
            blueprint=unit_app,
            use_external_address=False,
            view_function=PutUnitAreaView,
            unit_id=unit_area["unit_id"],
            area_id=unit_area["area_id"],
        ),
        json={"labels": ["testing", "a", "label"]},
    )
    assert response.status_code == HTTPStatus.OK, response.json
    assert response.json["labels"] == ["testing", "a", "label"]


@pytest.mark.parametrize(
    "user_role,expected_http_response",
    [(USER_ROLE.ADMIN, HTTPStatus.OK), (USER_ROLE.DMS_LIMITED, HTTPStatus.FORBIDDEN)],
)
def test_put_unit_area_labels_not_permitted_to_site(
    client, site, unit_area, user_role, expected_http_response
):
    user = login_with(client, USERS[user_role.name])["user"]
    change_site_ownership(site["id"], user["client_id"])
    response = client.put(
        get_address_for(
            blueprint=unit_app,
            use_external_address=False,
            view_function=PutUnitAreaView,
            unit_id=unit_area["unit_id"],
            area_id=unit_area["area_id"],
        ),
        json={"labels": ["testing", "a", "label"]},
    )
    assert response.status_code == expected_http_response, response.json


class TestDownloadUnitFiles:
    @staticmethod
    def test_missing_arguments(client, unit, login):
        response = client.get(
            get_address_for(
                blueprint=unit_app,
                use_external_address=False,
                view_function=get_bytes_of_unit_deliverable,
                unit_id=unit["id"],
            )
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json["errors"] == {
            "querystring": {
                "file_format": ["Missing data for required field."],
                "language": ["Missing data for required field."],
            }
        }

    @staticmethod
    def test_download_successful(
        client, unit, login, mocked_gcp_download_file_as_bytes, client_db
    ):
        new_link = "fake link"
        UnitDBHandler.update(
            item_pks={"id": unit["id"]},
            new_values={"gcs_en_floorplan_link": new_link},
        )
        response = client.get(
            get_address_for(
                blueprint=unit_app,
                use_external_address=False,
                view_function=get_bytes_of_unit_deliverable,
                unit_id=unit["id"],
                file_format=SUPPORTED_OUTPUT_FILES.PNG.name,
                language=SUPPORTED_LANGUAGES.EN.name,
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert SUPPORTED_OUTPUT_FILES.PNG.name.lower() in response.mimetype
        assert (
            response.headers[0][1]
            == 'attachment; filename="Big-ass portfolio_GS20.00.01_EN.png"'
        )
        # Check filename
        mocked_gcp_download_file_as_bytes.assert_called_with(
            bucket_name=get_client_bucket_name(client_id=client_db["id"]),
            source_file_name=GCloudStorageHandler._convert_media_link_to_file_in_gcp(
                new_link
            ),
        )

    @staticmethod
    def test_download_missing_link(mock_gcp_client, client, unit, login):
        response = client.get(
            get_address_for(
                blueprint=unit_app,
                use_external_address=False,
                view_function=get_bytes_of_unit_deliverable,
                unit_id=unit["id"],
                file_format=SUPPORTED_OUTPUT_FILES.PNG.name,
                language=SUPPORTED_LANGUAGES.EN.name,
            )
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
