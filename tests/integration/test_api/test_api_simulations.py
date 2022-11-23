from http import HTTPStatus

import pytest
from shapely.geometry import Point

from common_utils.constants import (
    IMMO_RESPONSE_PRECISION,
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    VIEW_SUN_DIMENSIONS,
)
from handlers.db import PotentialSimulationDBHandler
from slam_api.apis.potential.endpoints import GetPotentialSimulation, potential_api
from slam_api.apis.potential.private_endpoints import (
    GetSimulationById,
    GetSimulationResultsById,
    GetSimulations,
    potential_private_api,
)
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.utils import check_immo_response_precision


@login_as(["POTENTIAL_API"])
def test_get_simulation_wrong_format(
    mocked_geolocator,
    client,
    login,
    potential_db_simulation_ch_sun_empty,
    zurich_location,
):
    response = client.get(
        get_address_for(
            view_function=GetPotentialSimulation,
            blueprint=potential_api,
            simulation_type=potential_db_simulation_ch_sun_empty["type"],
            lat=zurich_location["lat"],
            lon=zurich_location["lon"],
            key="should not be here",
        ),
    )
    assert response.status_code == 422


@pytest.mark.parametrize("simulation_type", [SIMULATION_TYPE.VIEW, SIMULATION_TYPE.SUN])
@login_as(["POTENTIAL_API"])
def test_get_potential_simulation_finished(
    zurich_location,
    simulation_type,
    login,
    client,
    potential_view_results_test_api_simulations,
):
    from handlers import PotentialSimulationHandler

    PotentialSimulationDBHandler.add(
        floor_number=zurich_location["floor_number"],
        type=simulation_type,
        status=POTENTIAL_SIMULATION_STATUS.SUCCESS,
        result=PotentialSimulationHandler.format_view_sun_raw_results(
            potential_view_results_test_api_simulations,
            VIEW_SUN_DIMENSIONS[simulation_type.value.lower()],
            simulation_region=REGION.CH,
        ),
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        building_footprint=Point(zurich_location["lon"], zurich_location["lat"]).buffer(
            0.01
        ),
    )

    response = client.get(
        get_address_for(
            view_function=GetPotentialSimulation,
            blueprint=potential_api,
            lat=zurich_location["lat"],
            lon=zurich_location["lon"],
            floor_number=zurich_location["floor_number"],
            sim_type=simulation_type.value,
        )
    )
    simulation = response.get_json()

    assert simulation["lat"] == zurich_location["lat"]
    assert simulation["lon"] == zurich_location["lon"]

    actual_dimensions = set(simulation["result"].keys())
    actual_dimensions.remove("observation_points")
    expected_dimensions = set(VIEW_SUN_DIMENSIONS[simulation_type.value.lower()])

    assert not set.symmetric_difference(actual_dimensions, expected_dimensions)

    # Check values precision
    check_immo_response_precision(simulation["result"], IMMO_RESPONSE_PRECISION)


@pytest.mark.parametrize(
    "simulation_type", [SIMULATION_TYPE.VIEW.value, SIMULATION_TYPE.SUN.value]
)
@login_as(["ADMIN"])
def test_get_potential_simulation_results_by_id(
    zurich_location,
    simulation_type,
    login,
    client,
    potential_view_results_test_api_simulations,
):
    from handlers import PotentialSimulationHandler

    expected_dimensions = set(VIEW_SUN_DIMENSIONS[simulation_type.lower()])

    db_sim = PotentialSimulationDBHandler.add(
        floor_number=zurich_location["floor_number"],
        building_footprint=Point(zurich_location["lat"], zurich_location["lon"]).buffer(
            0.01
        ),
        type=simulation_type,
        status=POTENTIAL_SIMULATION_STATUS.SUCCESS,
        result=PotentialSimulationHandler.format_view_sun_raw_results(
            potential_view_results_test_api_simulations,
            VIEW_SUN_DIMENSIONS[simulation_type.lower()],
            simulation_region=REGION.CH,
        ),
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
    )

    response = client.get(
        get_address_for(
            view_function=GetSimulationResultsById,
            blueprint=potential_private_api,
            simulation_id=db_sim["id"],
        )
    )
    result = response.get_json()
    actual_dimensions = set(result.keys())
    actual_dimensions.remove("observation_points")

    assert not set.symmetric_difference(actual_dimensions, expected_dimensions)

    # Check values precision
    check_immo_response_precision(result, IMMO_RESPONSE_PRECISION)


@pytest.mark.parametrize(
    "simulation_type", [SIMULATION_TYPE.VIEW.value, SIMULATION_TYPE.SUN.value]
)
@login_as(["ADMIN"])
def test_get_potential_simulation_by_id(
    zurich_location,
    simulation_type,
    login,
    client,
    potential_view_results_test_api_simulations,
):
    from handlers import PotentialSimulationHandler

    expected_dimensions = set(VIEW_SUN_DIMENSIONS[simulation_type.lower()])

    db_sim = PotentialSimulationDBHandler.add(
        floor_number=zurich_location["floor_number"],
        type=simulation_type,
        status=POTENTIAL_SIMULATION_STATUS.SUCCESS,
        result=PotentialSimulationHandler.format_view_sun_raw_results(
            potential_view_results_test_api_simulations,
            VIEW_SUN_DIMENSIONS[simulation_type.lower()],
            simulation_region=REGION.CH,
        ),
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        building_footprint=Point(zurich_location["lat"], zurich_location["lon"]).buffer(
            0.01
        ),
    )

    response = client.get(
        get_address_for(
            view_function=GetSimulationById,
            blueprint=potential_private_api,
            simulation_id=db_sim["id"],
        )
    )
    simulation = response.get_json()

    for key in ["floor_number", "id", "type"]:
        assert simulation[key] == db_sim[key]
    result = simulation["result"]
    actual_dimensions = set(result.keys())
    actual_dimensions.remove("observation_points")

    assert not set.symmetric_difference(actual_dimensions, expected_dimensions)

    # Check values precision
    check_immo_response_precision(result, IMMO_RESPONSE_PRECISION)


@login_as(["ADMIN"])
def test_get_potential_simulation_should_return_404_if_db_empty(
    client, mocked_geolocator, login
):
    response = client.get(
        get_address_for(
            view_function=GetPotentialSimulation,
            blueprint=potential_api,
            lat=45.8,
            lon=10,
            floor_number=10,
            sim_type=SIMULATION_TYPE.VIEW.value,
        )
    )
    assert response.status_code == 404
    assert response.get_json() == {
        "msg": "Entity not found! Could not find one item for table PotentialSimulationDBModel"
    }


@pytest.mark.parametrize(
    "simulation_type", [(SIMULATION_TYPE.VIEW.value), (SIMULATION_TYPE.SUN.value)]
)
def test_get_potential_simulation_unauthorized_should_return_401(
    mocked_geolocator,
    simulation_type,
    client,
):
    response = client.get(
        get_address_for(
            view_function=GetPotentialSimulation,
            blueprint=potential_api,
            lat=10,
            lon=10,
            floor_number=10,
            simulation_type=simulation_type,
        )
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


class TestGetSimulations:
    @pytest.mark.parametrize(
        "bounds, expected_length",
        [
            ([5, 45, 12, 50], 1),
            ([0.0, 0.0, 20.0, 40.0], 0),
            ([10.0, 0.0, 20.0, 50.0], 0),
            ([10.0, 50.0, 20.0, 60.0], 0),
            ([], 1),
        ],
    )
    @login_as(["ADMIN"])
    def test_get_optional_bounding_box(
        self,
        client,
        two_potential_simulations_success_and_failed,
        bounds,
        expected_length,
        login,
    ):
        """zurich_location is lat=47.37482, lon=8.49410"""
        # when
        response = client.get(
            get_address_for(
                blueprint=potential_private_api,
                view_function=GetSimulations,
                **dict(zip(["min_lon", "min_lat", "max_lon", "max_lat"], bounds)),
            )
        )

        # then
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == expected_length

    @pytest.mark.parametrize(
        "bounds",
        [
            [0.0, None, 20.0, 50.0],
            [0.0, 0.0, 20.0],
            [0.0, 0.0],
            [0.0],
        ],
    )
    @login_as(["ADMIN"])
    def test_get_returns_422_on_invalid_bounding_box(self, client, bounds, login):
        response = client.get(
            get_address_for(
                blueprint=potential_private_api,
                view_function=GetSimulations,
                **dict(zip(["min_lon", "min_lat", "max_lon", "max_lat"], bounds)),
            )
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json
