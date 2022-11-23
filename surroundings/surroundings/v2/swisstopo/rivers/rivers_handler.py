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
from surroundings.v2.geometry_transformer import RiverLinesGeometryTransformer
from surroundings.v2.swisstopo.constants import RIVER_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)


class SwissTopoRiverLinesGeometryProvider(SwissTopoShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return RIVER_FILE_TEMPLATES

    @staticmethod
    def is_underground(geometry: Geometry):
        """Returns true if the river is underground"""
        return "Unterirdisch" in str(geometry.properties.get("VERLAUF", ""))

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not self.is_underground(geometry=geometry)


class SwissTopoRiverLinesHandler(BaseSurroundingHandler):
    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return RiverLinesGeometryTransformer(
            elevation_handler=self.elevation_handler, ground_offset=WATER_GROUND_OFFSET
        )

    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoRiverLinesGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.RIVERS
