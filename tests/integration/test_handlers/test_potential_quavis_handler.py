import pytest
from numpy import array
from shapely.geometry import Polygon

from brooks.util.projections import project_geometry
from common_utils.constants import (
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
    REGION,
)
from handlers.db import PotentialSimulationDBHandler
from handlers.quavis import PotentialViewQuavisHandler
from surroundings.swisstopo import SwisstopoElevationHandler
from tests.utils import random_simulation_version


@pytest.fixture
def building_polygon() -> Polygon:
    return Polygon([(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)])


@pytest.fixture
def expected_obs_points():
    # Keys are ignored, only order is important
    return {
        "1": array(
            [
                [1.03405453, 0.59890889, 5.8],
                [1.03405453, 1.59890889, 5.8],
                [0.16802913, 1.09890889, 5.8],
            ]
        )
    }


def test_get_obs_points_by_area_sortable(
    mocker,
    potential_db_simulation_ch_sun_empty,
    building_polygon,
    expected_obs_points,
):
    simulation_id = potential_db_simulation_ch_sun_empty["id"]

    building_polygon_lat_lon = project_geometry(
        geometry=building_polygon, crs_from=REGION.CH, crs_to=REGION.LAT_LON
    )
    pot_sim = PotentialSimulationDBHandler.update(
        item_pks={"id": simulation_id},
        new_values={"building_footprint": building_polygon_lat_lon},
    )
    swisstopo_elevation_handler = mocker.patch.object(
        SwisstopoElevationHandler,
        "get_elevation",
        return_value=0,
    )

    obs_points = PotentialViewQuavisHandler.get_obs_points_by_area(
        entity_info=pot_sim,
        grid_resolution=DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=0,
        simulation_version=random_simulation_version(),
    )

    point = swisstopo_elevation_handler.call_args_list[0].kwargs["point"]

    assert point.x == pytest.approx(building_polygon.centroid.x, abs=1e-2)
    assert point.y == pytest.approx(building_polygon.centroid.y, abs=1e-2)

    assert list(obs_points.keys()) == [simulation_id]

    for (_, expected_value), (_, value) in zip(
        sorted(expected_obs_points.items()), sorted(obs_points[simulation_id].items())
    ):  # Key is irrelevant
        assert expected_value == pytest.approx(value)
