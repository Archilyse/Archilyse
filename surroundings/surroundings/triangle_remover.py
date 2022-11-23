from typing import Iterator, List, Tuple, Union

from shapely.geometry import LineString, MultiPolygon, Polygon, box

from brooks.util.geometry_ops import get_line_strings, get_polygons
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from dufresne.polygon.utils import as_multipolygon
from surroundings.utils import SurrTrianglesType, get_interpolated_height


class TriangleRemover:
    Z_MIN = -1000
    Z_MAX = 4000

    @staticmethod
    def _get_y(x: float, straight_line: LineString) -> float:
        a = min(straight_line.coords, key=lambda c: c[0])
        b = max(straight_line.coords, key=lambda c: c[0])
        slope = (b[1] - a[1]) / (b[0] - a[0])
        interception = a[1] - a[0] * slope
        return x * slope + interception

    @classmethod
    def _handle_vertical_triangle(
        cls,
        footprint: Union[Polygon, MultiPolygon],
        triangle: Polygon,
    ) -> Iterator[List[Tuple[float, float, float]]]:
        """
        The idea of this method is to handle a perfectly vertical triangle by flipping z and y
        to do the intersection/ .difference in 2d. Later on we recompute the y values as they
        can be described by a function as the original 2d footprint of the triangle is a straight line.

        In case the 2d footprint of the original triangle is vertical (all x values being identical)
        the y values cannot be described by a function, to handle this scenario we flip x and y before
        the process described above and flip them back afterwards.

        The resulting polygons are then triangulated again.
        """
        if not footprint.contains(triangle.exterior):
            new_triangles = []

            is_2d_vertical = len(set(x for x, _, _ in triangle.exterior.coords)) == 1
            if is_2d_vertical:
                # NOTE: in case of identical x values we have to flip x and y
                triangle = Polygon([(y, x, z) for x, y, z in triangle.exterior.coords])
                footprint = MultiPolygon(
                    [
                        Polygon([(y, x) for x, y in polygon.exterior.coords])
                        for polygon in as_multipolygon(footprint).geoms
                    ]
                )

            # NOTE the triangle footprint is a straight line as the triangle is perfectly vertical
            triangle_footprint = LineString(
                # NOTE sort by x to avoid unnecessary MultiLineStrings resulting from the
                # intersection which would result in a self intersecting MultiPolygon
                # when calling triangle_footprint.intersection(footprint)
                sorted(triangle.exterior.coords[:3], key=lambda c: c[0])
            )

            # NOTE flip z and y and do everything in 2d
            flipped = Polygon([(x, z, y) for x, y, z in triangle.exterior.coords])
            flipped_to_be_removed = MultiPolygon(
                [
                    box(min(line.xy[0]), cls.Z_MIN, max(line.xy[0]), cls.Z_MAX)
                    for line in get_line_strings(
                        triangle_footprint.intersection(footprint)
                    )
                ]
            )

            for p in get_polygons(flipped.difference(flipped_to_be_removed)):
                for new_triangle in triangulate_polygon(p):
                    new_triangle = [
                        # NOTE flip back z and y (back to 3d)
                        (x, cls._get_y(x, triangle_footprint), y)
                        for x, y, _ in new_triangle
                    ]
                    new_triangles.append(new_triangle)

            if is_2d_vertical:
                # NOTE flip back x and y
                for new_triangle in new_triangles:
                    yield [(x, y, z) for y, x, z in new_triangle]
            else:
                yield from new_triangles

    @classmethod
    def _handle_plane_triangle(
        cls, footprint: Union[Polygon, MultiPolygon], triangle: Polygon
    ) -> Iterator[List[Tuple[float, float, float]]]:
        triangle_coords = triangle.exterior.coords[:3]
        for polygon in get_polygons(triangle.difference(footprint)):
            exterior_with_z = [
                (x, y, get_interpolated_height(x, y, triangle_coords))
                for x, y, _ in polygon.exterior.coords
            ]
            interiors_with_z = [
                [
                    (x, y, get_interpolated_height(x, y, triangle_coords))
                    for x, y, _ in hole.coords
                ]
                for hole in polygon.interiors
            ]
            polygon_with_z = Polygon(exterior_with_z, interiors_with_z)
            for new_triangle in triangulate_polygon(polygon_with_z):
                yield [tuple(point) for point in new_triangle]

    @classmethod
    def exclude_2d_intersections(
        cls,
        triangles: Iterator[SurrTrianglesType],
        footprint: Union[Polygon, MultiPolygon],
    ) -> Iterator[SurrTrianglesType]:
        """
        Removes the intersections of 3D triangles and 2D footprints and retriangulates the resulting polygons.

        Args:
            triangles: An iterator of surrounding 3D triangles
            footprint: The 2D footprint, all 2D intersections with this footprint will be removed

        Returns:
            Returns an iterator of 3D triangles excluding the intersections with the provided 2D footprint
        """
        for surrounding_type, triangle in triangles:
            for new_triangle in cls.triangle_difference(
                triangle=triangle, footprint=footprint
            ):
                yield surrounding_type, new_triangle

    @classmethod
    def triangle_difference(cls, triangle, footprint):
        triangle_polygon = Polygon(triangle)
        if triangle_polygon.is_valid and triangle_polygon.intersects(footprint):
            for new_triangle in cls._handle_plane_triangle(
                footprint=footprint, triangle=triangle_polygon
            ):
                yield new_triangle
        elif not triangle_polygon.is_valid and footprint.intersects(
            triangle_polygon.exterior
        ):
            # NOTE this happens in case of a perfectly
            # vertical triangle, e.g. a part of a wall
            for new_triangle in cls._handle_vertical_triangle(
                footprint=footprint, triangle=triangle_polygon
            ):
                yield new_triangle
        else:
            yield triangle
