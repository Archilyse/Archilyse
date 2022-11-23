import json

import pytest
from shapely.geometry import Point, Polygon

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from surroundings.swisstopo import SwissTopoRailroadSurroundingHandler


def test_create_swisstopo_railroad_surrounding_triangles(
    mocker, fixtures_swisstopo_path
):

    with fixtures_swisstopo_path.joinpath(
        "railroads/mocked_railroad_fiona_entities.json"
    ).open() as f:
        mocked_fiona_open = mocker.patch.object(
            SwissTopoRailroadSurroundingHandler,
            "load_entities",
            return_value=json.load(f),
        )

    lv95_location = Point(2682366.0, 1248229.0)
    railroad_type_triangle_tuples = list(
        SwissTopoRailroadSurroundingHandler(
            location=lv95_location, simulation_version=SIMULATION_VERSION.PH_01_2021
        ).get_triangles()
    )

    assert mocked_fiona_open.call_count == 1
    assert len(railroad_type_triangle_tuples) == pytest.approx(6285, abs=2)
    assert railroad_type_triangle_tuples[0][0] is SurroundingType.RAILROADS
    assert sum(
        [Polygon(p[1]).area for p in railroad_type_triangle_tuples]
    ) == pytest.approx(341613.0696152157, rel=1e-8)
    assert isinstance(railroad_type_triangle_tuples[0][1], list)
    assert isinstance(railroad_type_triangle_tuples[0][1][0], tuple)
    assert isinstance(railroad_type_triangle_tuples[0][1][0][0], float)
