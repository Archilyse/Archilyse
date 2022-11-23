from typing import Dict, Iterator, List, Optional, Tuple

from shapely.geometry import LineString, MultiPolygon, shape

from common_utils.constants import SurroundingType
from common_utils.logger import logger
from dufresne.linestring_add_width import LINESTRING_EXTENSION
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)

SWISSTOPO_TRUE = {"Wahr", "wahr", "WAHR"}
DEFAULT_WIDTH = 6  # unit is in meters (Dedicated to Tolo)
SWISSTOPO_STREET_TYPES_TO_EXCLUDE = {"Verbindung", "Platz", "Autozug", "Faehre"}
SWISSTOPO_STREET_TYPE_WIDTH = {  # all values in meters
    "Ausfahrt": 3.5,
    "Einfahrt": 3.5,
    "Autobahn": 2 * 3.5,
    "Raststaette": 3.5,
    "Zufahrt": 2 * 3.5,
    "Dienstzufahrt": 4,
    "10m Strasse": 10.20,
    "6m Strasse": 7,
    "4m Strasse": 5,
    "3m Strasse": 3.5,
    "2m Weg": 2,
    "1m Weg": 1,
    "1m Wegfragment": 1,
    "2m Wegfragment": 2,
    "8m Strasse": 9,
    "Autostrasse": 7,
}


class SwissTopoStreetSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):
    _ENTITIES_FILE_PATH = (
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_STRASSEN/swissTLM3D_TLM_STRASSE.{}"
    )

    def get_raw_geometries(self) -> Iterator[LineString]:
        for entity in self.entities():
            if linestring := self._get_raw_geometry(entity=entity):
                yield linestring

    def get_triangles(self) -> Iterator[Tuple[SurroundingType, List[Tuple[float]]]]:
        for street_geometry in filter(None, map(self._get_geometry, self.entities())):
            for geometry in street_geometry.geoms:
                for triangle in self.format_triangles(triangulate_polygon(geometry)):
                    yield SurroundingType.STREETS, triangle
        logger.info(f"Streets successfully calculated for location {self.location}")

    def _get_raw_geometry(self, entity: Dict) -> Optional[LineString]:
        street_type = entity["properties"]["OBJEKTART"]
        if street_type in SWISSTOPO_STREET_TYPES_TO_EXCLUDE:
            return

        linestring = shape(entity["geometry"])
        if not linestring.intersects(self.bounding_box):
            return

        return linestring

    def _get_geometry(self, entity: Dict) -> MultiPolygon:
        if linestring := self._get_raw_geometry(entity=entity):
            lanes_separated = entity["properties"]["RICHTUNGSG"]
            street_type = entity["properties"]["OBJEKTART"]
            street_width = SWISSTOPO_STREET_TYPE_WIDTH.get(street_type, DEFAULT_WIDTH)

            if lanes_separated in SWISSTOPO_TRUE:
                return self.add_width(
                    line=linestring,
                    width=street_width,
                    extension_type=LINESTRING_EXTENSION.RIGHT,
                )

            return self.add_width(line=linestring, width=street_width)
