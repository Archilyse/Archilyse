from typing import Dict, Iterator

from shapely.geometry import MultiPolygon, Polygon

from common_utils.constants import SurroundingType
from surroundings.base_tree_surrounding_handler import StandardTreeGenerator

from ..utils import SurrTrianglesType
from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler


class OSMTreesHandler(BaseEntityOSMSurroundingHandler):
    surrounding_type = SurroundingType.TREES

    _ENTITIES_FILE_PATH = "gis_osm_natural_free_1.shp"
    _DEFAULT_TREE_HEIGHT = 8

    def custom_entity_validity_check(self, entity: Dict) -> bool:
        return entity["properties"]["fclass"] == "tree"

    def get_triangles(
        self, building_footprints: list[Polygon, MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.filtered_entities():
            # TODO: geofabrik data doesn't contain additional properties like tree height so we
            #  are using a default value
            ground_level = self.elevation_handler.get_elevation(point=entity.geometry)
            for triangle in StandardTreeGenerator(
                simulation_version=self.simulation_version
            ).get_triangles(
                tree_location=entity.geometry,
                ground_level=ground_level,
                tree_height=self._DEFAULT_TREE_HEIGHT,
                building_footprints=building_footprints,
            ):
                yield self.surrounding_type, triangle
