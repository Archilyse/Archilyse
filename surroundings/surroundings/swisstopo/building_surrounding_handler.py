from typing import Iterator

import fiona
from shapely.geometry import MultiPolygon, shape

from common_utils.constants import SWISSTOPO_REQUIRED_FILES_BUILDINGS, SurroundingType
from common_utils.logger import logger
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from surroundings.base_building_handler import BaseBuildingSurroundingHandler, Building
from surroundings.constants import BOUNDING_BOX_EXTENSION_BUILDINGS
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import (
    SurrTrianglesType,
    download_swisstopo_if_not_exists,
    get_absolute_building_filepaths,
)


class SwissTopoBuildingSurroundingHandler(
    BaseEntitySwissTopoSurroundingHandler, BaseBuildingSurroundingHandler
):
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_BUILDINGS

    def load_entities(self, entities_file_path):
        download_swisstopo_if_not_exists(
            bounding_box=self.bounding_box, templates=SWISSTOPO_REQUIRED_FILES_BUILDINGS
        )
        for file_path in get_absolute_building_filepaths(self.bounding_box):
            with fiona.open(file_path.as_posix()) as f:
                yield from f

    def get_buildings(self) -> Iterator[Building]:
        yield from self._create_buildings_from_swisstopo()

    def get_triangles(
        self, building_footprints: list[MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        for building in self._create_buildings_from_swisstopo():
            if self._is_target_building(
                building_footprint=building.footprint,
                building_footprints=building_footprints,
            ):
                continue
            else:
                yield from self._triangulate_building(building=building)
        logger.info(f"Buildings successfully calculated for location {self.location}")

    def _create_buildings_from_swisstopo(self) -> Iterator[Building]:
        for entity in self.entities():
            geometry = shape(entity["geometry"])
            if not geometry.intersects(self.bounding_box):
                continue

            try:
                footprint = self._create_building_footprint(geometry=geometry)
            except ValueError as e:
                logger.error(
                    "Footprint Construction failed for Building element."
                    f"ValueError Message: {e}"
                )
                continue

            if not footprint:
                continue
            yield Building(geometry=geometry, footprint=footprint)

    def _triangulate_building(self, building: Building) -> Iterator[SurrTrianglesType]:
        geometry = (
            building.geometry
            if isinstance(building.geometry, MultiPolygon)
            else MultiPolygon([building.geometry])
        )
        for polygon in geometry.geoms:
            for triangle in self.format_triangles(triangulate_polygon(polygon)):
                yield SurroundingType.BUILDINGS, triangle
