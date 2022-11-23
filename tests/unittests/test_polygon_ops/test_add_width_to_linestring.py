import pytest
from shapely.geometry import LineString

from dufresne.linestring_add_width import (
    LINESTRING_EXTENSION,
    add_width_to_linestring_improved,
)


@pytest.mark.parametrize(
    "line, width, extension_type, expected_area, expected_bounds",
    [
        (
            LineString(((0, 0), (2, 0))),
            2.0,
            LINESTRING_EXTENSION.SYMMETRIC,
            4.0,
            (0.0, -1.0, 2.0, 1.0),
        ),
        (
            LineString(((0, 0), (2, 0))),
            2.0,
            LINESTRING_EXTENSION.LEFT,
            4.0,
            (0.0, 0.0, 2.0, 2.0),
        ),
        (
            LineString(((0, 0), (2, 0))),
            2.0,
            LINESTRING_EXTENSION.RIGHT,
            4.0,
            (0.0, -2.0, 2.0, 0.0),
        ),
        (
            LineString(((0, 0), (2, 0))),
            4.0,
            LINESTRING_EXTENSION.SYMMETRIC,
            8.0,
            (0.0, -2.0, 2.0, 2.0),
        ),
        (
            LineString(((0, 0), (2, 0), (4, 2))),
            1.0,
            LINESTRING_EXTENSION.SYMMETRIC,
            4.828,
            (0.0, -0.5, 4.353553390593274, 2.353553390593274),
        ),
        (
            LineString(((0, 0), (-2, 0), (-4, -2))),
            1.0,
            LINESTRING_EXTENSION.SYMMETRIC,
            4.828,
            (-4.353553390593274, -2.353553390593274, 0.0, 0.5),
        ),
        (
            LineString(((0, 0), (1, 1), (1, -1), (-1, -2))),
            1.0,
            LINESTRING_EXTENSION.SYMMETRIC,
            5.650,
            (-1.223606797749979, -2.447213595499958, 1.5, 2.2071067811865475),
        ),
        (
            LineString(((0, 0), (1, 1), (1, -1), (-1, -2))),
            2.0,
            LINESTRING_EXTENSION.SYMMETRIC,
            11.935,
            (-1.4472135954999579, -2.8944271909999157, 2.0, 3.414213562373095),
        ),
    ],
)
def test_add_width_to_linestring_improved(
    line, width, expected_area, extension_type, expected_bounds
):
    polygon = add_width_to_linestring_improved(
        line=line, width=width, extension_type=extension_type
    )
    assert polygon.area == pytest.approx(expected_area, abs=10**-3)
    assert polygon.bounds == expected_bounds
