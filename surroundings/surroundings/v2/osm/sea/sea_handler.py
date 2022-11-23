from functools import cached_property
from pathlib import Path
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
from surroundings.v2.osm.constants import SEA_FILE_TEMPLATES
from surroundings.v2.osm.geometry_provider import OSMGeometryProvider


class OSMSeaGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return SEA_FILE_TEMPLATES

    @property
    def osm_directory(self) -> Path:
        return Path()


class OSMSeaHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMSeaGeometryProvider(
            bounding_box=self.bounding_box, region=self.region, clip_geometries=True
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.SEA

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return GroundCoveringPolygonTransformer(
            elevation_handler=self.elevation_handler, ground_offset=WATER_GROUND_OFFSET
        )
