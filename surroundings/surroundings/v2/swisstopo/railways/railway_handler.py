from functools import cached_property

from common_utils.constants import SurroundingType
from surroundings.constants import RAILWAYS_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.constants import DEFAULT_RAILWAY_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.geometry_transformer import StreetAndRailwayTransformer
from surroundings.v2.swisstopo.railways.railway_geometry_provider import (
    SwissTopoRailwayGeometryProvider,
)


class RailwayGeometryTransformer(StreetAndRailwayTransformer):
    def get_width(self, geometry: Geometry) -> float:
        return DEFAULT_RAILWAY_WIDTH


class SwissTopoRailwayHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoRailwayGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return RailwayGeometryTransformer(
            elevation_handler=self.elevation_handler,
            ground_offset=RAILWAYS_GROUND_OFFSET,
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.RAILROADS
