from typing import List, Tuple

from shapely.geometry import JOIN_STYLE, LineString, MultiLineString, Polygon
from shapely.geometry.polygon import orient

from common_utils.utils import pairwise


def get_sides_as_lines_by_length(polygon: Polygon) -> List[LineString]:
    """Takes a polygon as input and returns all sides as Linestrings
    in length size ordered sequence increasing

    Args:
        polygon (Polygon): shapely polygon

    Returns:
        List[LineString]: List of Sides as LineString
    """
    return sorted(
        [
            LineString([point_a, point_b])
            for point_a, point_b in pairwise(orient(polygon=polygon).exterior.coords[:])
        ],
        key=lambda x: x.length,
    )


def get_sides_parallel_lines(
    rectangle: Polygon, offset_in_pct: float
) -> Tuple[LineString]:
    """
    Takes a polygon with 4 sides as input and returns the outer parallel lines of the sides.
                                   ───────── parallel line 2
                                    +offset%
                                  ┌─────────┐
      parallel line 1  │ +offset% │         │ +offset% │ parallel line 3
                                  └─────────┘
                                    +offset%
                                   ───────── parallel line 4
    """
    sides_as_lines_by_length = get_sides_as_lines_by_length(rectangle)
    if len(sides_as_lines_by_length) != 4:
        raise ValueError("Polygon has to have 4 sides!")
    distance = sides_as_lines_by_length[0].length * offset_in_pct
    parallel_lines: List[LineString] = [
        line.parallel_offset(
            distance=distance, side=direction, join_style=JOIN_STYLE.mitre
        )
        for line in sides_as_lines_by_length
        for direction in ["left", "right"]
    ]
    return tuple(line for line in parallel_lines if not line.intersects(rectangle))


def get_parallel_side_lines_to_reference_line(
    rectangle: Polygon, reference_line: LineString, offset_in_pct: float
) -> MultiLineString:
    """
                               reference line
                                     │
                                ┌────│────┐
    parallel line 1  │ +offset% │    │    │ +offset% │ parallel line 2
                                └────│────┘
                                     │
    """
    from brooks.util.geometry_ops import dot_product_normalised_linestrings

    parallel_lines_sorted_by_most_parallel = sorted(
        get_sides_parallel_lines(rectangle=rectangle, offset_in_pct=offset_in_pct),
        key=lambda line: abs(
            dot_product_normalised_linestrings(
                line_a=reference_line,
                line_b=line,
            )
        ),
        reverse=True,
    )
    return MultiLineString(parallel_lines_sorted_by_most_parallel[:2])
