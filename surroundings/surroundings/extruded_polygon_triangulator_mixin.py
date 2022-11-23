from typing import Iterator, Tuple, Union

from shapely.geometry import MultiPolygon, Point, Polygon

from dufresne.polygon.polygon_extrude_triangles import (
    get_triangles_from_extruded_polygon,
)
from dufresne.polygon.utils import as_multipolygon
from surroundings.utils import SurrTrianglesType


class ExtrudedPolygonTriangulatorMixin:
    def _get_min_max_ground_levels(self, footprint: Polygon) -> Tuple[float, float]:
        z_values = [
            self.elevation_handler.get_elevation(Point(x, y))
            for x, y in footprint.exterior.coords
        ]
        return min(z_values), max(z_values)

    def extrude_and_triangulate(
        self,
        height: float,
        footprint: Union[Polygon, MultiPolygon],
    ) -> Iterator[SurrTrianglesType]:
        for polygon in as_multipolygon(footprint).geoms:
            min_ground_level, max_ground_level = self._get_min_max_ground_levels(
                footprint=polygon
            )
            yield from (
                (self.surrounding_type, triangle)
                for triangle in get_triangles_from_extruded_polygon(
                    polygon=polygon,
                    ground_level=min_ground_level - 2,  # 2m arbitrary underground
                    height=max_ground_level + height,
                )
            )
