from typing import Iterator, Tuple

from numpy import array
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union


def create_pseudo_slice_view(
    triangles: array, slice_range: Tuple[float, float]
) -> Iterator[Polygon]:
    slice_range_as_linestring = LineString([(slice_range[0], 0), (slice_range[1], 0)])
    slice_polygons = [
        Polygon(triangle)
        for triangle in triangles
        if z_range_of_triangle_as_linestring(triangle=triangle).intersects(
            slice_range_as_linestring
        )
    ]
    valid_slice_polygons = []
    for polygon in slice_polygons:
        if not polygon.is_valid:
            polygon = polygon.buffer(0.0001)

        if not polygon.is_valid:
            continue
        valid_slice_polygons.append(polygon)

    return unary_union(valid_slice_polygons)


def z_range_of_triangle_as_linestring(triangle: array) -> LineString:
    z_coords_triangle = [coord[2] for coord in triangle]
    z_max = max(z_coords_triangle)
    z_min = min(z_coords_triangle)
    if z_max - z_min < 0.001:
        z_max += 0.001
    return LineString([(z_min, 0), (z_max, 0)])
