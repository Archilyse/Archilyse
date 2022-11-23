from functools import cached_property
from typing import Collection

from common_utils.constants import SurroundingType
from surroundings.constants import PARKS_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import GroundCoveringPolygonTransformer
from surroundings.v2.osm.constants import PARK_FILE_TEMPLATES
from surroundings.v2.osm.geometry_provider import OSMGeometryProvider

PARK_TYPES = {"park", "recreation_ground"}


class OSMParksGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return PARK_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["fclass"] in PARK_TYPES


class OSMParksHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMParksGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.PARKS

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return GroundCoveringPolygonTransformer(
            elevation_handler=self.elevation_handler, ground_offset=PARKS_GROUND_OFFSET
        )
