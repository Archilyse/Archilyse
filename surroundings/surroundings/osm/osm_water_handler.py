from typing import Dict

from shapely.geometry import LineString, MultiPolygon

from common_utils.constants import SurroundingType
from surroundings.base_linear_surrounding_handler_mixin import (
    BaseLinearOSMEntitiesMixin,
)
from surroundings.base_polygon_surrounding_handler_mixin import (
    BasePolygonSurroundingHandlerMixin,
)
from surroundings.constants import (
    BOUNDING_BOX_EXTENSION_LAKES,
    BOUNDING_BOX_EXTENSION_RIVERS,
)
from surroundings.utils import FilteredPolygonEntity

from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler


class OSMRiversHandler(BaseLinearOSMEntitiesMixin, BaseEntityOSMSurroundingHandler):
    # Rivers as lines, but anything carrying water in lines, even small water streams
    _ENTITIES_FILE_PATH = "gis_osm_waterways_free_1.shp"
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_RIVERS
    DEFAULT_RIVER_WIDTH = 3  # meters

    VALID_ENTITY_TYPES = {"river", "oxbow"}

    surrounding_type = SurroundingType.RIVERS

    def custom_entity_validity_check(self, entity: Dict) -> bool:
        return entity["properties"]["fclass"] in self.VALID_ENTITY_TYPES

    def _apply_width(
        self, line: LineString, entity: FilteredPolygonEntity
    ) -> MultiPolygon:
        return self.add_width(line=line, width=self.DEFAULT_RIVER_WIDTH)


class OSMRiversPolygonsHandler(
    BasePolygonSurroundingHandlerMixin, BaseEntityOSMSurroundingHandler
):
    # Contains big rivers
    _ENTITIES_FILE_PATH = "gis_osm_water_a_free_1.shp"
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_RIVERS

    VALID_ENTITY_TYPES = {"riverbank", "river"}

    surrounding_type = SurroundingType.RIVERS

    def custom_entity_validity_check(self, entity: Dict) -> bool:
        return entity["properties"]["fclass"] in self.VALID_ENTITY_TYPES


class OSMLakesHandler(
    BasePolygonSurroundingHandlerMixin, BaseEntityOSMSurroundingHandler
):
    """https://wiki.openstreetmap.org/wiki/Key:water"""

    VALID_ENTITY_TYPES = {"water", "pond", "reservoir", "lake"}

    # Provides polygons for rivers and lakes
    _ENTITIES_FILE_PATH = "gis_osm_water_a_free_1.shp"

    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_LAKES

    surrounding_type = SurroundingType.LAKES

    def custom_entity_validity_check(self, entity: Dict) -> bool:
        return entity["properties"]["fclass"] in self.VALID_ENTITY_TYPES
