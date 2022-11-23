from typing import List

import pytest
from scipy.spatial import ConvexHull
from shapely.geometry import Point

from common_utils.constants import SIMULATION_VERSION
from surroundings.base_tree_surrounding_handler import StandardTreeGenerator
from surroundings.utils import Triangle


def get_volume_from_triangles(triangles: List[Triangle]) -> float:
    return ConvexHull([point for triangle in triangles for point in triangle]).volume


@pytest.mark.parametrize("ground_level", [0, 10])
@pytest.mark.parametrize("simulation_version", list(SIMULATION_VERSION))
@pytest.mark.parametrize(
    "tree_height, expected_volume",
    [(20.0, 640.0), (10, 80.0), (1.0, 0.08)],
)
def test_base_tree_handler_get_crown_triangles(
    tree_height, expected_volume, simulation_version, ground_level
):
    triangles = list(
        StandardTreeGenerator(
            simulation_version=simulation_version
        ).get_crown_triangles(
            ground_level=ground_level,
            tree_location=Point(0.0, 0.0),
            tree_height=tree_height,
        )
    )
    assert len(triangles) == 12
    # One side of the crown of the tree is proportional to the tree elevation
    # For 20m tall tree, the crown side size alone is 20 / 5.0 = 4m from the center point
    # In total we have 8m large for each side of the cube. The crow is half of the tree height. so 8 * 8 * 10

    # For tree top of 10m we have 4 * 4 * 5 == 80.0

    # For tree top of 1m we have 40cm of total length of the cube side so 0.4 * 0.4 * 0.5
    assert get_volume_from_triangles(triangles=triangles) == pytest.approx(
        expected_volume, abs=10**-3
    )


@pytest.mark.parametrize("simulation_version", list(SIMULATION_VERSION))
@pytest.mark.parametrize(
    "ground_level",
    [0.0, 10.0],
)
def test_base_tree_handler_get_crown_triangles_elevation(
    ground_level, simulation_version
):
    triangles = list(
        StandardTreeGenerator(
            simulation_version=simulation_version
        ).get_crown_triangles(
            ground_level=ground_level,
            tree_location=Point(0.0, 0.0),
            tree_height=20.0,
        )
    )
    expected_elevation_triangles = [10.0 + ground_level, 20.0 + ground_level]
    z_values = [point[2] for triangle in triangles for point in triangle]
    assert [min(z_values), max(z_values)] == expected_elevation_triangles


@pytest.mark.parametrize("ground_level", [0, 10])
@pytest.mark.parametrize(
    "tree_height, expected_volume, simulation_version",
    [
        (20.0, 40.0, SIMULATION_VERSION.PH_01_2021),
        (10, 20.0, SIMULATION_VERSION.PH_01_2021),
        (1.0, 2.0, SIMULATION_VERSION.PH_01_2021),
        (1.0, 0.5 * 0.05**2, SIMULATION_VERSION.EXPERIMENTAL),
    ],
)
def test_base_tree_handler_get_trunk_triangles(
    tree_height, expected_volume, simulation_version, ground_level
):
    triangles = list(
        StandardTreeGenerator(
            simulation_version=simulation_version
        ).get_trunk_triangles(
            ground_level=ground_level,
            tree_location=Point(0.0, 0.0),
            tree_height=tree_height,
        )
    )
    assert len(triangles) == 12
    assert get_volume_from_triangles(triangles=triangles) == pytest.approx(
        expected_volume, abs=10**-5
    )
