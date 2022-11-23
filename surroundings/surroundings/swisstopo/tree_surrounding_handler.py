from typing import Iterator

from shapely.geometry import MultiPolygon, Point

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from common_utils.logger import logger
from surroundings.base_tree_surrounding_handler import StandardTreeGenerator
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import SurrTrianglesType
from surroundings.v2.swisstopo.constants import SWISSTLM3D


class SwissTopoTreeSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):

    # TRANSLATION: einzelbaum gebuesch = individual trees
    _ENTITIES_FILE_PATH = [
        f"{SWISSTLM3D}/TLM_BB/swissTLM3D_TLM_EINZELBAUM_GEBUESCH_{direction}.{{}}"
        for direction in ["OST", "WEST"]
    ]

    def get_triangles(
        self,
        building_footprints: list[MultiPolygon],
        simulation_version: SIMULATION_VERSION = SIMULATION_VERSION.PH_01_2021,
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.entities():
            # No extra checks as all elements are trees and points
            coordinates = entity["geometry"]["coordinates"]
            tree_location = Point(coordinates[0], coordinates[1])
            if not tree_location.within(self.bounding_box):
                continue

            ground_level = self.elevation_handler.get_elevation(point=tree_location)
            for triangle in StandardTreeGenerator(
                simulation_version=self.simulation_version
            ).get_triangles(
                tree_location=tree_location,
                ground_level=ground_level,
                tree_height=coordinates[2] - ground_level,
                building_footprints=building_footprints,
            ):
                yield SurroundingType.TREES, triangle

        logger.info(f"Trees successfully calculated for location {self.location}")
