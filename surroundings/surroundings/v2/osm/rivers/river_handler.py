from typing import Collection

from common_utils.constants import SurroundingType
from surroundings.constants import WATER_GROUND_OFFSET

from ...base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from ...geometry import Geometry
from ...geometry_transformer import RiverLinesGeometryTransformer
from ..constants import RIVER_FILE_TEMPLATES
from ..geometry_provider import OSMGeometryProvider

RIVER_TYPES = {"river", "oxbow"}


class OSMRiverGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return RIVER_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["fclass"] in RIVER_TYPES


class OSMRiverHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMRiverGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    @property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return RiverLinesGeometryTransformer(
            elevation_handler=self.elevation_handler, ground_offset=WATER_GROUND_OFFSET
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.RIVERS
