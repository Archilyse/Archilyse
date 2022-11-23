from typing import Iterator

from shapely.affinity import scale
from shapely.geometry import LineString, MultiPolygon
from shapely.ops import unary_union

from brooks.util.geometry_ops import get_polygons
from dufresne.linestring_add_width import LINESTRING_EXTENSION, add_width_to_linestring
from dufresne.polygon.utils import as_multi_linestring
from surroundings.base_polygon_surrounding_handler_mixin import (
    BasePolygonSurroundingHandlerMixin,
)
from surroundings.utils import FilteredPolygonEntity, SurrTrianglesType


class BaseLinearOSMEntitiesMixin(BasePolygonSurroundingHandlerMixin):
    def _apply_width(
        self, line: LineString, entity: FilteredPolygonEntity
    ) -> MultiPolygon:
        raise NotImplementedError()

    @staticmethod
    def add_width(
        line: LineString,
        width: float,
        extension_type: LINESTRING_EXTENSION = LINESTRING_EXTENSION.SYMMETRIC,
    ) -> MultiPolygon:
        return add_width_to_linestring(
            line=line, width=width, extension_type=extension_type
        )

    def get_triangles(
        self, building_footprints: list[MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        layout_grounds = unary_union(
            [
                scale(
                    geom=footprint.minimum_rotated_rectangle,
                    xfact=1.2,
                    yfact=1.2,
                )
                for footprint in building_footprints
            ]
        )
        for entity in self.filtered_entities():
            for line in as_multi_linestring(any_shape=entity.geometry).geoms:
                for polygon in self._apply_width(line, entity=entity).geoms:
                    for cropped_pol in get_polygons(polygon.difference(layout_grounds)):
                        yield from self._triangulate_polygon(cropped_pol)
