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
from surroundings.v2.swisstopo.constants import WATER_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)


class SwissTopoWaterGeometryProvider(SwissTopoShapeFileGeometryProvider):
    WATER_TYPES = {"Fliessgewaesser", "Stehende Gewaesser"}

    @property
    def file_templates(self) -> Collection[str]:
        return WATER_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["OBJEKTART"] in self.WATER_TYPES


class SwissTopoWaterHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoWaterGeometryProvider(
            bounding_box=self.bounding_box, region=self.region, clip_geometries=True
        )

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return GroundCoveringPolygonTransformer(
            elevation_handler=self.elevation_handler, ground_offset=WATER_GROUND_OFFSET
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        if geometry.properties["OBJEKTART"] == "Fliessgewaesser":
            return SurroundingType.RIVERS
        return SurroundingType.LAKES
