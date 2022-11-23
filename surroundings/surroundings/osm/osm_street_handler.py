from shapely.geometry import LineString, MultiPolygon

from common_utils.constants import SurroundingType
from surroundings.base_linear_surrounding_handler_mixin import (
    BaseLinearOSMEntitiesMixin,
)
from surroundings.utils import FilteredPolygonEntity

from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler

DEFAULT_WIDTH = 2  # meters
OSM_STREET_TYPE_WIDTH = {  # all values in meters
    # national highways
    "motorway": 2 * 3.5,
    "motorway_link": 3.5,
    # express roads
    "trunk": 3.5,
    "trunk_link": 3.5,
    # primary municipal roads
    "primary": 2 * 3,
    "primary_link": 3,
    # secondary municipal roads
    "secondary": 2 * 3,
    "secondary_link": 3,
    # tertiary municipal roads
    "tertiary": 2 * 3,
    "tertiary_link": 3,
    # miscellaneous
    "service": 3.5,
    "residential": 2 * 3.5,
    "living_street": 4,
    "pedestrian": 6,
    "steps": 3,
    "cycleway": 3.5,
    "unknown": 2 * 3,
    "unclassified": 2 * 3,
}


class OSMStreetHandler(BaseLinearOSMEntitiesMixin, BaseEntityOSMSurroundingHandler):
    _ENTITIES_FILE_PATH = "gis_osm_roads_free_1.shp"
    surrounding_type = SurroundingType.STREETS

    def _apply_width(
        self, line: LineString, entity: FilteredPolygonEntity
    ) -> MultiPolygon:
        return self.add_width(
            line=line,
            width=OSM_STREET_TYPE_WIDTH.get(entity.entity_class, DEFAULT_WIDTH),
        )
