import pytest
from shapely.geometry import LineString, Polygon, box

from dufresne.polygon.polygon_get_rectangular_side_vectors import (
    get_parallel_side_lines_to_reference_line,
    get_sides_parallel_lines,
)


@pytest.mark.parametrize(
    "rectangle, expected_lines, offset_in_pct",
    [
        (
            box(0.0, 0.0, 2.0, 1.0),
            (
                [(2.1, 1.0), (2.1, 0.0)],
                [(-0.1, 0.0), (-0.1, 1.0)],
                [(0.0, 1.1), (2.0, 1.1)],
                [(2.0, -0.1), (0.0, -0.1)],
            ),
            0.1,
        ),
        (
            box(0.0, 0.0, 2.0, 1.0),
            (
                [(2.2, 1.0), (2.2, 0.0)],
                [(-0.2, 0.0), (-0.2, 1.0)],
                [(0.0, 1.2), (2.0, 1.2)],
                [(2.0, -0.2), (0.0, -0.2)],
            ),
            0.2,
        ),
        (
            box(0.0, 0.0, 1.0, 2.0),
            (
                [(0.0, 2.1), (1.0, 2.1)],
                [(1.0, -0.1), (0.0, -0.1)],
                [(1.1, 2.0), (1.1, 0.0)],
                [(-0.1, 0.0), (-0.1, 2.0)],
            ),
            0.1,
        ),
        (
            Polygon([(0.0, 1.0), (1.0, 0.0), (3.0, 2.0), (2.0, 3.0), (0.0, 1.0)]),
            (
                [(0.5, -0.5), (-0.5, 0.5)],
                [(2.5, 3.5), (3.5, 2.5)],
                [(3.5, 1.5), (1.5, -0.5)],
                [(-0.5, 1.5), (1.5, 3.5)],
            ),
            0.5,
        ),
    ],
)
def test_get_sides_parallel_lines(rectangle, expected_lines, offset_in_pct):
    lines = get_sides_parallel_lines(rectangle=rectangle, offset_in_pct=offset_in_pct)
    assert len(lines) == 4
    for line, expected_line in zip(lines, expected_lines):
        assert line.coords[:] == expected_line


@pytest.mark.parametrize(
    "reference_line_coords, expected_coords",
    [
        (
            [(0.0, 0.0), (2.0, 0.0)],
            [[(0.0, 1.1), (2.0, 1.1)], [(2.0, -0.1), (0.0, -0.1)]],
        ),
        (
            [(0.0, 0.0), (0.0, 1.0)],
            [[(2.1, 1.0), (2.1, 0.0)], [(-0.1, 0.0), (-0.1, 1.0)]],
        ),
    ],
)
def test_get_parallel_side_lines_to_reference_line(
    reference_line_coords, expected_coords
):
    rectangle = box(0.0, 0.0, 2.0, 1.0)
    parallel_sides = get_parallel_side_lines_to_reference_line(
        reference_line=LineString(reference_line_coords),
        rectangle=rectangle,
        offset_in_pct=0.1,
    )
    actual_coords = [line.coords[:] for line in parallel_sides.geoms]
    assert actual_coords == expected_coords
