import pytest
from deepdiff import DeepDiff
from shapely.geometry import Polygon, box

from dufresne.polygon import get_sides_as_lines_by_length
from simulations.room_shapes import get_room_shapes


@pytest.mark.parametrize(
    "polygon, expected",
    [
        (
            Polygon(((0.0, 0.0), (2.0, 0.0), (1.0, 2.0), (0.0, 0.0))),
            [2.0, 2.23, 2.23],
        ),  # triangle
        (
            Polygon(((0.0, 0.0), (0.0, 4.0), (2.0, 5.0), (4.0, 4.0), (4.0, 0.0))),
            [
                2.236,
                2.236,
                4.0,
                4.0,
                4.0,
            ],
        ),  # pentagon
    ],
)
def test_get_sides_as_lines_by_length(polygon, expected):
    lines = get_sides_as_lines_by_length(polygon=polygon)
    assert [line.length for line in lines] == pytest.approx(expected, abs=0.01)


def test_get_room_shapes_circle(circle_polygon):
    result = get_room_shapes(polygon=circle_polygon)
    assert not DeepDiff(
        result,
        {
            "mean_walllengths": 0.096,
            "compactness": 0.999,
            "std_walllengths": 0.0,
        },
        ignore_order=True,
        significant_digits=2,
        ignore_type_subclasses=True,
    )


def test_get_room_shapes_square():
    result = get_room_shapes(polygon=box(0, 0, 10, 10))
    assert not DeepDiff(
        result,
        {
            "mean_walllengths": 10.0,
            "compactness": 0.785,
            "std_walllengths": 0.0,
        },
        ignore_order=True,
        significant_digits=2,
        ignore_type_subclasses=True,
    )
