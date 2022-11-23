from enum import Enum, auto
from typing import Iterable, Union

import numpy as np
from shapely.geometry import (
    JOIN_STYLE,
    LineString,
    MultiLineString,
    MultiPolygon,
    Polygon,
)

from common_utils.exceptions import BaseSlamException
from dufresne.rotation.vector_rotate_right import rotate_vec_right


class LINESTRING_EXTENSION(Enum):
    LEFT = auto()
    RIGHT = auto()
    SYMMETRIC = auto()


def add_width_to_linestring(
    line: LineString,
    width: float,
    extension_type: LINESTRING_EXTENSION = LINESTRING_EXTENSION.SYMMETRIC,
) -> MultiPolygon:
    """Adds a width to a LineString (e.g. a street width to LineStrings
    representing a street)

    Args:
        line (LineString): Shapely LineString 3d or 2d
        width (float): width to add to LineString
        extension_type (LINESTRING_EXTENSION, optional): Defaults to SYMMETRIC.
        How to extend the LineString
            1: Symmetrical extensions in both direction of half of the width
            2: Extension to the rigth
            3: Extension to the left

    Returns:
        MultiPolygon: Extended LineString
    """
    coordinates = np.asarray(line.coords)
    is_3d = len(coordinates[0]) == 3

    polygons = []
    for i in range(len(coordinates) - 1):
        vec = coordinates[i + 1, :2] - coordinates[i, :2]
        vec = vec / np.linalg.norm(vec)
        vec_turned = rotate_vec_right(vec)
        if extension_type is LINESTRING_EXTENSION.SYMMETRIC:
            p1 = coordinates[i, :2] - vec_turned * width / 2
            p2 = coordinates[i, :2] + vec_turned * width / 2
            p3 = coordinates[i + 1, :2] + vec_turned * width / 2
            p4 = coordinates[i + 1, :2] - vec_turned * width / 2

        elif extension_type is LINESTRING_EXTENSION.RIGHT:
            p1 = coordinates[i, :2]
            p2 = coordinates[i, :2] + vec_turned * width
            p3 = coordinates[i + 1, :2] + vec_turned * width
            p4 = coordinates[i + 1, :2]

        elif extension_type is LINESTRING_EXTENSION.LEFT:
            p1 = coordinates[i, :2] - vec_turned * width
            p2 = coordinates[i, :2]
            p3 = coordinates[i + 1, :2]
            p4 = coordinates[i + 1, :2] - vec_turned * width

        if is_3d:
            p1 = np.append(p1, coordinates[i, 2])
            p2 = np.append(p2, coordinates[i, 2])
            p3 = np.append(p3, coordinates[i + 1, 2])
            p4 = np.append(p4, coordinates[i + 1, 2])

        polygon = Polygon([p1, p2, p3, p4])

        if polygon.is_valid:
            polygons.append(polygon)

    return MultiPolygon(polygons)


def add_width_to_linestring_improved(
    line: LineString,
    width: float,
    extension_type: LINESTRING_EXTENSION = LINESTRING_EXTENSION.SYMMETRIC,
) -> Polygon:
    """Note:There is a big assumption in the way we build the polygon, as at the moment,
    the left line and the right line are always going in opposite directions, the polygon is built nicely.
    This is because the right extension has always the opposite direction.
    If any update of shapely changes this, it will be flagged in any case by the tests"""

    def get_line_z(line: LineString, i: int) -> float:
        if i >= len(line.coords):
            return line.coords[-1][2]
        return line.coords[i][2]

    def get_coords(geoms: Union[LineString, MultiLineString]) -> Iterable[tuple]:
        if isinstance(geoms, LineString):
            yield from geoms.coords
        else:  # MultiLineString
            for geom in geoms:
                yield from geom.coords

    join_style = JOIN_STYLE.mitre
    if extension_type == LINESTRING_EXTENSION.RIGHT:
        right_line = line.parallel_offset(width, "right", join_style=join_style)
        left_line = line
    elif extension_type == LINESTRING_EXTENSION.LEFT:
        left_line = line.parallel_offset(width, "left", join_style=join_style)
        right_line = LineString(list(reversed(line.coords[:])))
    elif extension_type == LINESTRING_EXTENSION.SYMMETRIC:
        left_line = line.parallel_offset(width / 2.0, "left", join_style=join_style)
        right_line = line.parallel_offset(width / 2.0, "right", join_style=join_style)
    else:
        raise BaseSlamException(f"invalid argument {extension_type}")

    if line.has_z:
        left_line_coords = [
            (*c[:2], get_line_z(line, i)) for i, c in enumerate(get_coords(left_line))
        ]
        right_line_coords = [
            (*c[:2], get_line_z(line, i)) for i, c in enumerate(get_coords(right_line))
        ]
        coords = left_line_coords + right_line_coords + [left_line_coords[0]]
    else:
        left_line_coords = [c[:2] for c in get_coords(left_line)]
        right_line_coords = [c[:2] for c in get_coords(right_line)]
        coords = left_line_coords + right_line_coords + [left_line_coords[0]]

    return Polygon(coords)
