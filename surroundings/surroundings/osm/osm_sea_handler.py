from typing import Collection, Iterator

import fiona
from shapely.geometry import MultiPolygon

from common_utils.constants import GOOGLE_CLOUD_OSM, SurroundingType
from dufresne.polygon.utils import as_multipolygon
from surroundings.constants import BOUNDING_BOX_EXTENSION_SEA, OSM_DIR
from surroundings.utils import SurrTrianglesType, download_shapefile_if_not_exists

from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler


class OSMSeaHandler(BaseEntityOSMSurroundingHandler):
    # Provides polygons for cost lines
    _ENTITIES_FILE_PATH = "water-polygons-split-4326/water_polygons.shp"
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_SEA
    surrounding_type = SurroundingType.SEA

    def load_entities(self, entities_file_path) -> Collection:
        """For coastlines there is no concept of region"""
        remote = GOOGLE_CLOUD_OSM.joinpath(self._ENTITIES_FILE_PATH)
        local_path = OSM_DIR.joinpath(self._ENTITIES_FILE_PATH)
        download_shapefile_if_not_exists(remote=remote, local=local_path)
        return fiona.open(local_path)

    def get_triangles(
        self, building_footprints: list[MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.filtered_entities():
            for polygon in as_multipolygon(entity.geometry).geoms:
                for triangle in self.get_3d_triangles_from_2d_polygon_with_elevation(
                    polygon=polygon
                ):
                    yield self.surrounding_type, triangle
