from typing import Collection, Iterator

from common_utils.constants import SurroundingType
from surroundings.constants import RAILWAYS_GROUND_OFFSET

from ...base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from ...constants import DEFAULT_RAILWAY_WIDTH
from ...geometry import Geometry
from ...geometry_transformer import GroundCoveringLineStringTransformer
from ..constants import RAILWAY_FILE_TEMPLATES
from ..geometry_provider import OSMGeometryProvider
from ..utils import is_tunnel


class OSMRailwayTransformer(GroundCoveringLineStringTransformer):
    def get_width(self, geometry: Geometry) -> float:
        return DEFAULT_RAILWAY_WIDTH


class OSMRailwayGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return RAILWAY_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not is_tunnel(properties=geometry.properties)


class OSMNoisyRailwayGeometryProvider(OSMRailwayGeometryProvider):
    """Adds the property type to the geometry"""

    def get_geometries(self) -> Iterator[Geometry]:
        for geometry in super(OSMNoisyRailwayGeometryProvider, self).get_geometries():
            geometry.properties["type"] = "rail"
            yield geometry


class OSMRailwayHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMRailwayGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    @property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return OSMRailwayTransformer(
            elevation_handler=self.elevation_handler,
            ground_offset=RAILWAYS_GROUND_OFFSET,
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.RAILROADS
