import json

import pytest
from shapely.affinity import scale, translate
from shapely.geometry import MultiPolygon, Point, box, shape

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from surroundings.base_forest_surrounding_handler import BaseForestGenerator
from surroundings.swisstopo import SwissTopoForestSurroundingHandler
from tests.utils import check_surr_triangles, random_simulation_version


@pytest.mark.parametrize(
    "fixture, num_triangles, area, first_elem_height, simulation_version",
    [
        (
            "land_coverage/bush_forest.json",
            1188,
            198.0,
            100.0,
            random_simulation_version(),
        ),
        (
            "land_coverage/open_forest.json",
            360,
            600.0,
            100.0,
            SIMULATION_VERSION.PH_01_2021,
        ),
        (
            "land_coverage/open_forest.json",
            360,
            487.5,
            100.0,
            SIMULATION_VERSION.EXPERIMENTAL,
        ),
        (
            "land_coverage/standard_forest.json",
            744,
            1240.0,
            100.0,
            SIMULATION_VERSION.PH_01_2021,
        ),
        (
            "land_coverage/standard_forest.json",
            744,
            1007.5,
            100.0,
            SIMULATION_VERSION.EXPERIMENTAL,
        ),
    ],
)
def test_forest_get_triangles(
    mocker,
    fixtures_swisstopo_path,
    fixture,
    num_triangles,
    area,
    first_elem_height,
    mocked_gcp_download,
    mock_elevation,
    simulation_version,
):

    mock_elevation(100.0)
    with fixtures_swisstopo_path.joinpath(fixture).open() as f:
        entity = json.load(f)

    mocked_fiona_open = mocker.patch.object(
        SwissTopoForestSurroundingHandler,
        "load_entities",
        return_value=[entity],
    )

    location = shape(entity["geometry"]).centroid

    target_building_centroid = Point(2751798, 1236396)
    floor_footprint = box(
        minx=target_building_centroid.x - 10,
        miny=target_building_centroid.y - 5,
        maxx=target_building_centroid.x + 10,
        maxy=target_building_centroid.y + 5,
    )
    sample_layout_footprints = [
        MultiPolygon(
            [
                scale(geom=floor_footprint, xfact=0.1, yfact=0.01),
                translate(geom=floor_footprint, xoff=1),
            ]
        ),
        floor_footprint,
    ]

    coverage_triangles = list(
        SwissTopoForestSurroundingHandler(
            location=location, simulation_version=simulation_version
        ).get_triangles(building_footprints=sample_layout_footprints)
    )

    assert mocked_fiona_open.call_count == 1
    check_surr_triangles(
        expected_area=area,
        first_elem_height=first_elem_height,
        expected_num_triangles=num_triangles,
        surr_triangles=coverage_triangles,
        expected_surr_type={SurroundingType.FOREST},
    )


def test_random_sampling():
    lv95_location = Point(2679373, 1246755)
    polygon = box(
        lv95_location.x - 50,
        lv95_location.y - 50,
        lv95_location.x + 50,
        lv95_location.y + 50,
    )

    points = BaseForestGenerator.sample_points_inside_polygon(polygon=polygon)

    assert len(points) == 441
