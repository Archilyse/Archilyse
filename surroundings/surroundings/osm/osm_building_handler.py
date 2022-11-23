from typing import Iterator, Optional

from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.strtree import STRtree

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from common_utils.logger import logger
from surroundings.base_building_handler import BaseBuildingSurroundingHandler, Building
from surroundings.constants import BOUNDING_BOX_EXTENSION_BUILDINGS
from surroundings.extruded_polygon_triangulator_mixin import (
    ExtrudedPolygonTriangulatorMixin,
)
from surroundings.osm.base_osm_surrounding_handler import (
    BaseEntityOSMSurroundingHandler,
)

from ..utils import SurrTrianglesType
from .overpass_api_handler import OverpassAPIHandler


class OSMBuildingsHandler(
    BaseEntityOSMSurroundingHandler,
    BaseBuildingSurroundingHandler,
    ExtrudedPolygonTriangulatorMixin,
):
    surrounding_type = SurroundingType.BUILDINGS

    _ENTITIES_FILE_PATH = "gis_osm_buildings_a_free_1.shp"
    _MIN_BUILDING_HEIGHT = 10  # meters
    _BUILDING_LEVEL_HEIGHT = 3.5  # meters
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_BUILDINGS

    def __init__(
        self,
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        bounding_box_extension: Optional[float] = None,
        raster_grid: Optional[STRtree] = None,
        elevation_handler=None,
    ):
        super().__init__(
            location=location,
            region=region,
            bounding_box_extension=bounding_box_extension,
            simulation_version=simulation_version,
            raster_grid=raster_grid,
            elevation_handler=elevation_handler,
        )
        self.building_heights_by_osm_id = OverpassAPIHandler.get_building_metadata(
            bounding_box=self.bounding_box
        )

    def get_triangles(
        self, building_footprints: list[Polygon | MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.filtered_entities():
            if self._is_target_building(
                building_footprint=entity.geometry,
                building_footprints=building_footprints,
            ):
                continue
            yield from self.extrude_and_triangulate(
                footprint=entity.geometry,
                height=self._get_building_height(osm_properties=entity.osm_properties),
            )
        logger.info(f"Buildings successfully calculated for location {self.location}")

    def get_buildings(self) -> Iterator[Building]:
        for entity in self.filtered_entities():
            yield Building(geometry=entity.geometry, footprint=entity.geometry)

    def _get_building_height(self, osm_properties) -> float:
        # Temp code to consider 3D Buildings input
        if height := osm_properties.get("height"):
            return height
        building_osm_id = osm_properties.get("osm_id")
        if not building_osm_id:
            return self._MIN_BUILDING_HEIGHT

        if height_info := self.building_heights_by_osm_id.get(int(building_osm_id)):
            if tags := height_info.get("tags"):
                if height := tags.get("height"):
                    if height.isdigit():
                        return float(height)
                if levels := tags.get("building:levels"):
                    if levels.isdigit():
                        return self._BUILDING_LEVEL_HEIGHT * int(levels)

        return self._MIN_BUILDING_HEIGHT
