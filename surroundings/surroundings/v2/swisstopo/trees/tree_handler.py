from functools import cached_property
from typing import Collection

from common_utils.constants import SurroundingType
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import TreeGeometryTransformer
from surroundings.v2.swisstopo.constants import TREES_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)


class SwissTopoTreeGeometryProvider(SwissTopoShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return TREES_FILE_TEMPLATES


class SwissTopoTreeGeometryTransformer(TreeGeometryTransformer):
    def get_height(self, geometry: Geometry):
        ground_level = self.elevation_handler.get_elevation(geometry.geom)
        return geometry.geom.z - ground_level


class SwissTopoTreeHandler(BaseSurroundingHandler):
    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return SwissTopoTreeGeometryTransformer(
            elevation_handler=self.elevation_handler
        )

    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoTreeGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.TREES
