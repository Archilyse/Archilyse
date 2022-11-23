from typing import Collection

from common_utils.constants import SurroundingType

from ...base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from ...constants import DEFAULT_TREE_HEIGHT
from ...geometry import Geometry
from ...geometry_transformer import TreeGeometryTransformer
from ..constants import TREE_FILE_TEMPLATES
from ..geometry_provider import OSMGeometryProvider


class OSMTreeGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return TREE_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["fclass"] == "tree"


class OSMTreeGeometryTransformer(TreeGeometryTransformer):
    def get_height(self, geometry: Geometry):
        return DEFAULT_TREE_HEIGHT


class OSMTreeHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMTreeGeometryProvider(
            region=self.region, bounding_box=self.bounding_box
        )

    @property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return OSMTreeGeometryTransformer(elevation_handler=self.elevation_handler)

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.TREES
