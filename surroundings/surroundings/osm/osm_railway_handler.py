from typing import Dict

from shapely.geometry import LineString, MultiPolygon

from common_utils.constants import SurroundingType
from surroundings.base_linear_surrounding_handler_mixin import (
    BaseLinearOSMEntitiesMixin,
)
from surroundings.constants import BOUNDING_BOX_EXTENSION_RAILROADS
from surroundings.utils import FilteredPolygonEntity

from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler


class OSMRailwayHandler(BaseLinearOSMEntitiesMixin, BaseEntityOSMSurroundingHandler):
    _ENTITIES_FILE_PATH = "gis_osm_railways_free_1.shp"
    DEFAULT_RAILROAD_WIDTH = 2

    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_RAILROADS
    surrounding_type = SurroundingType.RAILROADS

    def custom_entity_validity_check(self, entity: Dict) -> bool:
        return not self._is_tunnel(entity["properties"])

    @staticmethod
    def _is_tunnel(properties: Dict) -> bool:
        """
        metadata for osm railways provide an property whether the railway segment is a tunnel or not
        """
        if properties.get("tunnel") and properties["tunnel"] == "T":
            return True
        return False

    def _apply_width(
        self, line: LineString, entity: FilteredPolygonEntity
    ) -> MultiPolygon:
        return self.add_width(line=line, width=self.DEFAULT_RAILROAD_WIDTH)
