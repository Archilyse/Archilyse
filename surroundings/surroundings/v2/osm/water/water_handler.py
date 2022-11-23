from functools import cached_property
from typing import Collection

from common_utils.constants import SurroundingType
from surroundings.constants import WATER_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import GroundCoveringPolygonTransformer
from surroundings.v2.osm.constants import WATER_FILE_TEMPLATES
from surroundings.v2.osm.geometry_provider import OSMGeometryProvider

WATER_TYPES = {
    "riverbank": SurroundingType.RIVERS,
    "river": SurroundingType.RIVERS,
    "water": SurroundingType.LAKES,
    "pond": SurroundingType.LAKES,
    "reservoir": SurroundingType.LAKES,
    "lake": SurroundingType.LAKES,
}


class OSMWaterGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return WATER_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["fclass"] in WATER_TYPES


class OSMWaterHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMWaterGeometryProvider(
            bounding_box=self.bounding_box, region=self.region, clip_geometries=True
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return WATER_TYPES[geometry.properties["fclass"]]

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return GroundCoveringPolygonTransformer(
            elevation_handler=self.elevation_handler, ground_offset=WATER_GROUND_OFFSET
        )
