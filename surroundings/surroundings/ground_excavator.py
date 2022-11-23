from functools import cached_property
from typing import Iterable, Iterator

from shapely.affinity import scale, translate
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

from brooks.util.geometry_ops import get_line_strings, get_polygons
from dufresne.dimension_from2dto3d import from2dto3d
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from dufresne.polygon.utils import as_multipolygon
from surroundings.utils import PointTuple, Triangle, get_interpolated_height


class GroundExcavator:
    def __init__(
        self,
        building_footprints: list[Polygon | MultiPolygon],
    ):
        self._triangles_intersecting_borders = []
        self._building_footprints = building_footprints

    @property
    def _triangles_intersecting_buildings_borders(self):
        return self._triangles_intersecting_borders

    def excavate(
        self, triangles: Iterable[Triangle], lowering_construction_site: float = 1.0
    ) -> Iterator[Triangle]:
        for triangle_coords in triangles:
            for sub_triangle in self._filter_triangles_inside_construction_site(
                triangle_coords=triangle_coords
            ):
                yield sub_triangle

        yield from self._get_triangles_construction_site(
            lowering_construction_site=lowering_construction_site
        )

    @staticmethod
    def _apply_ground_height(
        coords: Iterable[PointTuple], triangle_coords: Triangle
    ) -> Iterator[PointTuple]:
        return (
            (
                point[0],
                point[1],
                get_interpolated_height(
                    *point[:2],
                    from_triangle=triangle_coords,
                ),
            )
            for point in coords
        )

    def _filter_triangles_inside_construction_site(
        self, triangle_coords: Triangle
    ) -> Iterator[Triangle]:
        """
        3 different scenarios are handled:
        - If triangle doesn't intersect with the construction site its simply returned
        - If triangle within construction site, returns empty iterator
        - If triangle intersects with construction site, the difference is triangulated and returned as an iterator of
        triangles

        Additionally, all triangles intersecting with the border of the building footprints are stored in
        self.triangles_intersecting_buildings_borders . This will later be used for generating the triangles
        of the construction site

        """
        triangle_as_polygon = Polygon(triangle_coords)
        if triangle_as_polygon.intersects(self._excavation_footprints):
            if difference := triangle_as_polygon.difference(
                self._excavation_footprints
            ):
                self._triangles_intersecting_buildings_borders.append(
                    triangle_as_polygon
                )
                for sub_polygon in get_polygons(difference):
                    sub_polygon = Polygon(
                        self._apply_ground_height(
                            coords=sub_polygon.exterior.coords,
                            triangle_coords=triangle_coords,
                        )
                    )
                    yield from triangulate_polygon(polygon=sub_polygon)
        else:
            yield triangle_coords

    def _get_elevation_construction_site_floor(
        self, excavation_footprint: Polygon, lowering_construction_site: float
    ) -> float:
        return (
            min(
                xyz[2]
                for line in self._get_building_borders_3d(
                    excavation_footprint=excavation_footprint
                )
                for xyz in line.coords
            )
            - lowering_construction_site
        )

    def _get_triangles_construction_site(
        self,
        lowering_construction_site: float,
    ) -> Iterator[Triangle]:
        """
        returns triangles representing the excavation of the construction site [shoe box like hole per building]
        the depth of the hole can be provided by the lowering_construction_site parameter
        """
        for excavation_footprint in self._excavation_footprints.geoms:
            ground_elevation = self._get_elevation_construction_site_floor(
                excavation_footprint=excavation_footprint,
                lowering_construction_site=lowering_construction_site,
            )
            yield from self._get_triangles_excavation_floor(
                excavation_footprint=excavation_footprint,
                ground_elevation=ground_elevation,
            )
            yield from self._get_triangles_excavation_sides(
                excavation_footprint=excavation_footprint,
                ground_elevation=ground_elevation,
            )

    def _get_triangles_excavation_sides(
        self,
        excavation_footprint: Polygon,
        ground_elevation: float,
    ) -> Iterator[Triangle]:
        """
        returns triangles representing the excavation of the construction site [shoe box like hole per building]
        the depth of the hole is given by the ground_elevation parameter
        """
        for linestring in self._get_building_borders_3d(
            excavation_footprint=excavation_footprint
        ):
            z_values = [coord[2] - ground_elevation for coord in linestring.coords]
            faces = self._extrude_faces_from_linestring(
                linestring=linestring,
                z_values=z_values,
            )
            for face in [translate(geom=face, zoff=ground_elevation) for face in faces]:
                yield from triangulate_polygon(polygon=face)

    def _get_building_borders_3d(
        self, excavation_footprint: Polygon
    ) -> Iterator[LineString]:
        """
        Uses the collection of triangles which are intersecting with the border of
        the building footprints. yields 3 dimensional border lines.
        """
        border_2d = LineString(excavation_footprint.exterior.coords)
        for triangle in self._triangles_intersecting_buildings_borders:
            triangle_coords = triangle.exterior.coords[:3]
            intersection = triangle.intersection(border_2d)
            yield from (
                LineString(
                    self._apply_ground_height(
                        coords=linestring.coords, triangle_coords=triangle_coords
                    )
                )
                for linestring in get_line_strings(intersection)
            )

    @classmethod
    def _get_triangles_excavation_floor(
        cls,
        excavation_footprint: Polygon,
        ground_elevation: float,
    ) -> Iterator[Triangle]:
        """
        returns triangles representing the provided footprint (the floor of the excavation hole)
        """
        for polygon in as_multipolygon(
            from2dto3d(obj=excavation_footprint, z_coordinate=ground_elevation)
        ).geoms:
            yield from triangulate_polygon(polygon=polygon)

    @cached_property
    def _excavation_footprints(self) -> MultiPolygon:
        """
        1. takes the minimum rotated rectangle of all plan footprints per building.
        2. scales the minimum rotated rectangle with 1.2
        3. returns the unary union of all these scaled building footprints rectangles
        """
        if not self._building_footprints:
            return MultiPolygon()

        scaled_footprints_union = unary_union(
            [
                scale(
                    geom=unary_union(plan_footprints).minimum_rotated_rectangle,
                    xfact=1.2,
                    yfact=1.2,
                )
                for plan_footprints in self._building_footprints
            ]
        )
        return MultiPolygon(get_polygons(scaled_footprints_union))

    @staticmethod
    def _extrude_faces_from_linestring(
        linestring: LineString, z_values: list[float]
    ) -> list[Polygon]:
        """
        Creates vertical polygons from the linestring and the provided z values.
        for each interval along the linestring a vertical polygon is created which extends from 0 to the provided z
        value the number of points in the linestring has to match exactly the length of the provided z values
        """
        faces = []
        coordinates = list(linestring.coords)
        for i in range(0, len(coordinates) - 1):
            first_value = [coordinates[i][0], coordinates[i][1], 0]

            faces.append(
                Polygon(
                    shell=[
                        first_value,
                        [coordinates[i + 1][0], coordinates[i + 1][1], 0],
                        [coordinates[i + 1][0], coordinates[i + 1][1], z_values[i + 1]],
                        [coordinates[i][0], coordinates[i][1], z_values[i]],
                        first_value,
                    ]
                )
            )
        return faces
