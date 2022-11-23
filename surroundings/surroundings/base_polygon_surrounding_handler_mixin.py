from typing import Iterator

from shapely.geometry import MultiPolygon, Polygon

from dufresne.polygon.utils import as_multipolygon
from surroundings.utils import SurrTrianglesType


class BasePolygonSurroundingHandlerMixin:
    def _triangulate_polygon(self, polygon: Polygon) -> SurrTrianglesType:
        for sub_polygon in self._segment_polygon(polygon):
            for triangle in self.get_3d_triangles_from_2d_polygon_with_elevation(
                polygon=sub_polygon
            ):
                yield self.surrounding_type, triangle

    def get_triangles(
        self, building_footprints: list[MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.filtered_entities():
            for polygon in as_multipolygon(entity.geometry).geoms:
                yield from self._triangulate_polygon(polygon=polygon)
