from functools import cached_property

from common_utils.constants import SurroundingType
from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.constants import STREETS_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.constants import DEFAULT_STREET_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import SWISSTOPO_TRUE
from surroundings.v2.swisstopo.geometry_transformer import StreetAndRailwayTransformer

from .constants import STREET_TYPE_WIDTH
from .street_classifier import SwissTopoStreetsClassifier
from .street_geometry_provider import SwissTopoStreetsGeometryProvider


class StreetsGeometryTransformer(StreetAndRailwayTransformer):
    def get_width(self, geometry: Geometry) -> float:
        return STREET_TYPE_WIDTH.get(
            geometry.properties["OBJEKTART"], DEFAULT_STREET_WIDTH
        )

    @staticmethod
    def lanes_separated(geometry: Geometry) -> bool:
        return geometry.properties["RICHTUNGSG"] in SWISSTOPO_TRUE

    def get_extension_type(self, geometry: Geometry) -> LINESTRING_EXTENSION:
        return (
            LINESTRING_EXTENSION.RIGHT
            if self.lanes_separated(geometry=geometry)
            else LINESTRING_EXTENSION.SYMMETRIC
        )


class SwissTopoStreetsHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoStreetsGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return StreetsGeometryTransformer(
            elevation_handler=self.elevation_handler,
            ground_offset=STREETS_GROUND_OFFSET,
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType[
            SwissTopoStreetsClassifier.classify(geometry=geometry).name
        ]
