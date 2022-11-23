import itertools
import json

import pytest
import shapely.wkt
from shapely.affinity import rotate
from shapely.geometry import Point, Polygon, box
from shapely.strtree import STRtree

from common_utils.constants import REGION
from common_utils.exceptions import BaseElevationException
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.osm import OSMLakesHandler
from surroundings.srtm import SRTMElevationHandler
from surroundings.swisstopo import SwisstopoElevationHandler
from tests.utils import random_simulation_version


@pytest.fixture
def river_line(fixtures_osm_path):
    """This is coming as a lake in osm but is really a river"""
    with fixtures_osm_path.joinpath("rivers/l_arve_river.json").open() as f:
        return json.load(f)


line_string_ch = (
    "LINESTRING (2620000.1 1188000.1, 2620278.814829497 1188162.867742785, 2620285.292075869 1188170.316881322, "
    "2621001.756730604 1188645.253806234, 2621001.668887497 1188637.83947994, 2621000.360620378 1188633.136568712, "
    "2620999.152384699 1188627.05329745, 2620998.901838078 1188621.420654731, 2621000.013338582 1188616.39851621)"
)
line_string_zurich = "LINESTRING (2683420.142928296 1246803.435610716, 2683470.142928296 1246853.435610716, 2683520.142928296 1246903.435610716)"


@pytest.mark.parametrize(
    "linestring, location, region, z_max, z_min, elevation_handler",
    [
        (
            line_string_ch,
            Point(2620000.1, 1188000),
            REGION.CH,
            958.5709838867188,
            936.6041259765625,
            SwisstopoElevationHandler,
        ),
        (
            line_string_zurich,
            Point(2683420.142928296, 1246803.435610716),
            REGION.CH,
            413.1,
            406.1,
            SRTMElevationHandler,
        ),
    ],
)
def test_osm_apply_ground_height(
    linestring,
    location,
    region,
    z_max,
    z_min,
    elevation_handler,
    mocked_swisstopo_esri_ascii_grid,
):
    tiles_to_mock = ["swiss_1187_4", "swiss_1188_3", "swiss_1187_2", "swiss_1188_1"]
    elevation_handler = elevation_handler(
        location=location, region=region, simulation_version=random_simulation_version()
    )
    osm_handler = OSMLakesHandler(
        location=location,
        region=region,
        bounding_box_extension=200,
        elevation_handler=elevation_handler,
        simulation_version=random_simulation_version(),
    )
    line = shapely.wkt.loads(linestring).intersection(osm_handler.bounding_box)

    with mocked_swisstopo_esri_ascii_grid(*tiles_to_mock):
        transformed_line = osm_handler.elevation_handler.apply_ground_height(geom=line)

    z_coordinate = [x[2] for x in transformed_line.coords[:]]
    assert not list(filter(lambda x: x > z_max, z_coordinate))
    assert not list(filter(lambda x: x < z_min, z_coordinate))


def test_osm_apply_ground_height_error_outside(mocked_swisstopo_esri_ascii_grid):
    tiles_to_mock = ["swiss_1187_4", "swiss_1188_3", "swiss_1187_2", "swiss_1188_1"]
    point_outside = 2690000.1
    line = shapely.wkt.loads(
        f"LINESTRING ({point_outside} 1188000.1, 2620278.814829497 1188162.867742785, "
        "2620285.292075869 1188170.316881322, 2620999.152384699 1188627.05329745, 2620998.901838078 "
        "1188621.420654731, 2621000.013338582 1188616.39851621)"
    )
    with mocked_swisstopo_esri_ascii_grid(*tiles_to_mock), pytest.raises(
        BaseElevationException
    ):
        OSMLakesHandler(
            location=Point(2620000.1, 1188000),
            region=REGION.CH,
            bounding_box_extension=200,
            simulation_version=random_simulation_version(),
        ).elevation_handler.apply_ground_height(geom=line)


def test_osm_apply_ground_height_element_going_outside_of_switzerland(
    mocker,
    river_line,
    mocked_swisstopo_esri_ascii_grid,
):
    mocker.patch.object(OSMLakesHandler, "load_entities", side_effect=[[river_line]])
    osm_handler = OSMLakesHandler(
        location=Point(2503229.537580522, 1115221.823543631),
        region=REGION.CH,
        bounding_box_extension=495,
        simulation_version=random_simulation_version(),
    )

    with mocked_swisstopo_esri_ascii_grid("swiss_1301_3"):
        triangles = list(osm_handler.get_triangles(building_footprints=[]))

    z_coordinates = [
        point[2] for triangle_coords in triangles for point in triangle_coords[1]
    ]

    assert max(z_coordinates) == pytest.approx(392.52, abs=1.0)
    assert min(z_coordinates) == pytest.approx(388.81, abs=1.0)
    assert len(triangles) == 178


def test_segment_polygon_should_yield_same_unsplit_polygon():
    # Given no raster grid is provided
    polygon = box(-0.75, 0.25, 1.5, 0.75)
    handler = OSMLakesHandler(
        location=Point(2500430.3, 1116821.0),
        region=REGION.CH,
        raster_grid=None,
        simulation_version=random_simulation_version(),
    )
    # When the segment method is called
    sub_polygons = list(handler._segment_polygon(polygon=polygon))
    # Then the segmentation is not applied
    assert sub_polygons == [polygon]


def test_segment_polygon_should_not_yield_polygon():
    # Given a polygon not intersecting with the raster grid
    polygon = box(-0.75, 0.25, 1.5, 0.75)
    handler = OSMLakesHandler(
        location=Point(2500430.3, 1116821.0),
        region=REGION.CH,
        raster_grid=STRtree([Polygon([(2, 0), (2, 2), (3, 2)])]),
        simulation_version=random_simulation_version(),
    )
    # When the segment method is called
    sub_polygons = list(handler._segment_polygon(polygon=polygon))
    # Then the polygon is silently ignored
    assert not sub_polygons


def test_segment_polygon_simple_case():
    """
    Tests, that the input polygon is split into 2 smaller ones when segmented against the raster grid.

    Input:
                      raster grid
                      _________
             |--------|-----/-|--|
    polygon  |        |   /   |  |
             |--------|-/-----|--|
                      ---------

    Output:
                      |-----/-|
    sub polygons      |   /   |
                      |-/-----|

    """
    ground_triangles = [
        [(0, 0), (0, 1), (1, 1)],
        [(0, 0), (1, 0), (1, 1)],
    ]
    raster_grid = STRtree(Polygon(t) for t in ground_triangles)
    polygon = box(-0.75, 0.25, 1.5, 0.75)
    handler = OSMLakesHandler(
        location=Point(2500430.3, 1116821.0),
        region=REGION.CH,
        raster_grid=raster_grid,
        simulation_version=random_simulation_version(),
    )
    sub_polygons = list(
        p.exterior.coords[:-1] for p in handler._segment_polygon(polygon=polygon)
    )
    assert sub_polygons == [
        [(0.0, 0.75), (0.75, 0.75), (0.25, 0.25), (0.0, 0.25)],
        [(1.0, 0.25), (0.25, 0.25), (0.75, 0.75), (1.0, 0.75)],
    ]


def test_segment_polygon_complex_case():
    """
    Tests, that the input polygon is split into 6 smaller ones if intermediate sub-polygons are intersected by a second
    triangle from a 2x2 raster grid.
    """
    grid = [
        Polygon([(0, 0), (1, 0), (1, 1)]),
        Polygon([(0, 0), (0, 1), (1, 1)]),
        Polygon([(1, 0), (1, 1), (2, 1)]),
        Polygon([(1, 0), (2, 0), (2, 1)]),
        Polygon([(0, 1), (1, 1), (1, 2)]),
        Polygon([(0, 1), (0, 2), (1, 2)]),
        Polygon([(1, 1), (1, 2), (2, 2)]),
        Polygon([(1, 1), (2, 1), (2, 2)]),
    ]
    raster_grid = STRtree(grid)

    polygon = rotate(box(0.5, 0.5, 1.5, 1.5), angle=45)

    handler = OSMLakesHandler(
        location=Point(2500430.3, 1116821.0),
        region=REGION.CH,
        raster_grid=raster_grid,
        simulation_version=random_simulation_version(),
    )
    sub_polygons = list(handler._segment_polygon(polygon=polygon))

    assert len(sub_polygons) == 6
    assert all(isinstance(s, Polygon) for s in sub_polygons)
    assert (
        len([s for s in sub_polygons if s.area == pytest.approx(0.125, abs=1e-9)]) == 4
    )
    assert (
        len([s for s in sub_polygons if s.area == pytest.approx(0.25, abs=1e-9)]) == 2
    )
    assert sum(sub_polygon.area for sub_polygon in sub_polygons) == pytest.approx(
        polygon.area, rel=1e-6
    )
    assert all(p1.touches(p2) for p1, p2 in itertools.combinations(sub_polygons, 2))


@pytest.mark.parametrize(
    "elevation_handler_class,region,should_inject",
    [
        (ZeroElevationHandler, REGION.CH, True),
        (SRTMElevationHandler, REGION.MC, True),
        (SwisstopoElevationHandler, REGION.CH, False),
        (ZeroElevationHandler, REGION.DK, False),
        (SRTMElevationHandler, REGION.CZ, False),
        (ZeroElevationHandler, REGION.CZ, True),
    ],
)
def test_base_entity_osm_surrounding_handler_should_accept_elevation_handler(
    elevation_handler_class, region, should_inject
):
    standard_args = dict(
        location=Point(2500430.3, 1116821.0),
        region=region,
        simulation_version=random_simulation_version(),
    )
    elevation_handler = (
        elevation_handler_class(**standard_args) if should_inject else None
    )
    handler = OSMLakesHandler(**standard_args, elevation_handler=elevation_handler)
    assert isinstance(handler.elevation_handler, elevation_handler_class)
