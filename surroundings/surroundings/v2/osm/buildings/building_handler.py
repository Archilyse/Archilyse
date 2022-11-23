from functools import cached_property
from typing import Collection, Dict

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.osm.overpass_api_handler import OverpassAPIHandler
from surroundings.v2.base import (
    BaseElevationHandler,
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import BuildingFootprintTransformer
from surroundings.v2.osm.constants import (
    BUILDING_FILE_TEMPLATES,
    BUILDING_LEVEL_HEIGHT,
    MIN_BUILDING_HEIGHT,
)
from surroundings.v2.osm.geometry_provider import OSMGeometryProvider


class OSMBuildingGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return BUILDING_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not geometry.geom.is_empty


class OSMBuildingFootprintTransformer(BuildingFootprintTransformer):
    def __init__(
        self, elevation_handler: BaseElevationHandler, building_heights_by_osm_id: Dict
    ):
        super().__init__(elevation_handler)
        self.building_heights_by_osm_id = building_heights_by_osm_id

    def get_height(self, geometry: Geometry) -> float:
        building_osm_id = geometry.properties.get("osm_id")
        if not building_osm_id:
            return MIN_BUILDING_HEIGHT

        if height_info := self.building_heights_by_osm_id.get(int(building_osm_id)):
            if tags := height_info.get("tags"):
                if height := tags.get("height"):
                    if height.isdigit():
                        return float(height)
                if levels := tags.get("building:levels"):
                    if levels.isdigit():
                        return BUILDING_LEVEL_HEIGHT * int(levels)

        return MIN_BUILDING_HEIGHT


class OSMBuildingHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMBuildingGeometryProvider(
            region=self.region, bounding_box=self.bounding_box, clip_geometries=True
        )

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        building_heights_by_osm_id = OverpassAPIHandler.get_building_metadata(
            bounding_box=project_geometry(
                self.bounding_box, crs_from=self.region, crs_to=REGION.LAT_LON
            )
        )
        return OSMBuildingFootprintTransformer(
            elevation_handler=self.elevation_handler,
            building_heights_by_osm_id=building_heights_by_osm_id,
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.BUILDINGS
