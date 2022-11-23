from typing import Iterator

from shapely.geometry import shape

from common_utils.constants import SurroundingType
from common_utils.logger import logger
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from dufresne.polygon.utils import as_multi_linestring, as_multipolygon
from surroundings.constants import BOUNDING_BOX_EXTENSION_RIVERS
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import SurrTrianglesType

DEFAULT_RIVER_WIDTH = 2

RIVER_WIDTH = {
    "LIMMAT": 40,
    "Limmat": 40,
    "Sihl": 30,
    "SIHL": 30,
    "Schanzengraben": 30,
    "Glatt": 11,
    "Reppisch": 11,
    "Repisch": 11,
    "Töss": 24,
    "Thur": 38,
    "Murg": 14,
    "La Serine": 13,
    "Rietaach": 11,
    "Rheintaler Binnenkanal": 13,
    "Sitter": 30,
    "Goldach": 30,
    "Steinach": 10,
    "Giessen": 7,
    "Werdenberger Binnenkanal": 8,
    "Rhein | Le Rhin | Rein | Rheno": 100,
}


class SwissTopoRiverSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):
    _ENTITIES_FILE_PATH = "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.{}"
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_RIVERS

    def read_detailed_entities(self):
        path = [
            f"2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_BODENBEDECKUNG_{direction}.{{}}"
            for direction in ["ost", "west"]
        ]
        return super(SwissTopoRiverSurroundingHandler, self).load_entities(path)

    def get_detailed_rivers(self):
        detailed_rivers = []  # We need to store them for later comparison
        for entity in self.read_detailed_entities():
            # Fliessgewaesser means Flowing water
            if entity["properties"]["OBJEKTART"] == "Fliessgewaesser":
                river = self.valid_geometry_intersected_without_z(
                    geom=shape(entity["geometry"])
                )
                if river:
                    detailed_rivers.append(river)
        return detailed_rivers

    def get_filtered_entities(self):
        for entity in self.entities():
            if "Unterirdisch" not in str(entity["properties"].get("VERLAUF", "")):
                yield entity

    def get_triangles(
        self,
    ) -> Iterator[SurrTrianglesType]:
        """
        Process Rivers from 2 sources. A detailed one with actually polygons
        and a second one with more rivers but lacking width information.

        returns a list of triangles. Each triangle is a list with 3 points.
        Each point is displayed as a tuple with three float numbers representing x,y,z
        """
        detailed_rivers = self.get_detailed_rivers()
        for detailed_river in detailed_rivers:
            for polygon in as_multipolygon(detailed_river).geoms:
                for triangle in self.get_3d_triangles_from_2d_polygon_with_elevation(
                    polygon=polygon
                ):
                    yield SurroundingType.RIVERS, triangle

        # Contains more rivers, but only as lines, no polygons
        for entity in self.get_filtered_entities():
            river_line = self.valid_geometry_intersected_without_z(
                geom=shape(entity["geometry"])
            )

            if not river_line or any(x.contains(river_line) for x in detailed_rivers):
                continue
            for line in as_multi_linestring(river_line).geoms:
                line = self.elevation_handler.apply_ground_height(geom=line)
                width = RIVER_WIDTH.get(
                    entity["properties"].get("NAME"), DEFAULT_RIVER_WIDTH
                )
                river_polygonized = self.add_width(line=line, width=width)

                for polygon in as_multipolygon(river_polygonized).geoms:
                    for triangle in self.format_triangles(
                        triangulate_polygon(polygon, mode="pa")
                    ):
                        yield SurroundingType.RIVERS, triangle

        logger.info(f"Rivers successfully calculated for location {self.location}")
