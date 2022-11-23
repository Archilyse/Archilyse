import pytest
from deepdiff import DeepDiff
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon, box, shape

from brooks.models import SimOpening, SimSeparator
from brooks.types import OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle


@pytest.mark.parametrize(
    "height, expected", [((2, 1), 1.5), ((10, 0), 5), (None, 1.45)]
)
def test_sim_opening_mid_height_point(height, expected):
    separator = SimSeparator(
        footprint=box(0, 0, 1, 1), separator_type=SeparatorType.WALL
    )
    opening = SimOpening(
        height=height,
        footprint=box(0, 0, 1, 1),
        opening_type=OpeningType.WINDOW,
        separator=separator,
        separator_reference_line=get_center_line_from_rectangle(
            polygon=separator.footprint
        )[0],
    )
    assert opening.mid_height_point == pytest.approx(expected)


def test_reference_geometry():
    opening = SimOpening(
        height=(2, 1),
        footprint=box(0, 0, 2, 1),
        opening_type=OpeningType.WINDOW,
        separator=SimSeparator(
            footprint=box(0, 0, 2, 1), separator_type=SeparatorType.WALL
        ),
        separator_reference_line=LineString([(0, 0), (0, 1)]),
    )

    reference_geometry = opening.reference_geometry()
    assert reference_geometry

    actual_coords = [line.coords[:] for line in reference_geometry.geoms]
    expected_coords = [[(2.1, 1.0), (2.1, 0.0)], [(-0.1, 0.0), (-0.1, 1.0)]]

    assert not DeepDiff(expected_coords, actual_coords, significant_digits=4)


def test_adjust_geometry_to_wall_linestring():
    """makes sure if the intersection is a Linestring (only touching borders)
    to convert it to polygon"""
    wall = Polygon([(0, 0), (2, 0), (2, 10), (0, 10)])
    opening = Polygon([(2, 2), (4, 2), (4, 7), (2, 7)])

    result = SimOpening.adjust_geometry_to_wall(
        opening=opening, wall=wall, buffer_width=1.05
    )

    expected_geometry = shape(
        {
            "type": "Polygon",
            "coordinates": (
                (
                    (2.05, 7.009999999999999),
                    (-0.050000000000000044, 7.009999999999999),
                    (-0.050000000000000044, 1.9899999999999993),
                    (2.05, 1.9899999999999993),
                    (2.05, 7.009999999999999),
                ),
            ),
        }
    )

    assert result.symmetric_difference(expected_geometry).area < 1e-4

    assert isinstance(result, Polygon)
    assert result.area > 1
    assert result.intersection(wall).area > 1


@pytest.mark.parametrize("rotation_angle", [i for i in range(0, 360, 20)])
def test_adjust_geometry_to_wall(rotation_angle):
    wall = rotate(
        geom=Polygon([(0, 0), (10, 0), (10, 2), (0, 2)]),
        angle=rotation_angle,
        origin=Point(0, 0),
    )
    opening = rotate(
        geom=Polygon([(4, 1), (6, 1), (6, 1.5), (4, 1.5)]),
        angle=rotation_angle,
        origin=Point(0, 0),
    )
    adjusted_opening = SimOpening.adjust_geometry_to_wall(
        opening=opening, wall=wall, buffer_width=1.05
    )
    adjusted_opening.distance(wall)
    assert adjusted_opening.area == pytest.approx(expected=4.2, abs=0.0001)
    assert adjusted_opening.difference(wall).area == pytest.approx(
        expected=0.2, abs=0.0001
    )
