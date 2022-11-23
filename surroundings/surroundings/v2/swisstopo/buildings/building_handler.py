from functools import cached_property
from typing import Collection

from common_utils.constants import SurroundingType
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import NoTransformer
from surroundings.v2.swisstopo.constants import BUILDINGS_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)


class SwissTopoBuildingsGeometryProvider(SwissTopoShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return BUILDINGS_FILE_TEMPLATES


class SwissTopoBuildingsHandler(BaseSurroundingHandler):
    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return NoTransformer()

    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoBuildingsGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.BUILDINGS
