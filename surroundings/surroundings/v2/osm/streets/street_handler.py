from typing import Collection, Iterator

from common_utils.constants import SurroundingType
from common_utils.exceptions import SurroundingException
from surroundings.constants import STREETS_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.constants import DEFAULT_STREET_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import GroundCoveringLineStringTransformer
from surroundings.v2.osm.constants import STREET_FILE_TEMPLATES
from surroundings.v2.osm.geometry_provider import OSMGeometryProvider
from surroundings.v2.osm.utils import is_tunnel

from .constants import STREET_TYPE_MAPPING, STREET_TYPE_WIDTH
from .utils import is_pedestrian


class OSMStreetGeometryTransformer(GroundCoveringLineStringTransformer):
    def get_width(self, geometry: Geometry) -> float:
        return STREET_TYPE_WIDTH.get(
            geometry.properties.get("fclass"), DEFAULT_STREET_WIDTH
        )


class OSMStreetGeometryProvider(OSMGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return STREET_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not is_tunnel(properties=geometry.properties)


class OSMNoisyStreetsGeometryProvider(OSMStreetGeometryProvider):
    """Filter for pedestrian streets too and
    apply a transformation to the geometries to get the relevant street type"""

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not is_tunnel(properties=geometry.properties) and not is_pedestrian(
            properties=geometry.properties
        )

    def get_geometries(self) -> Iterator[Geometry]:
        """We want to add the 'type: street type' here"""
        for geometry in super(OSMNoisyStreetsGeometryProvider, self).get_geometries():
            raw_street_type = geometry.properties.get("fclass")
            street_type = STREET_TYPE_MAPPING.get(raw_street_type)
            if street_type:
                geometry.properties["type"] = street_type
                yield geometry


class OSMStreetHandler(BaseSurroundingHandler):
    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return OSMStreetGeometryProvider(
            bounding_box=self.bounding_box, region=self.region, clip_geometries=True
        )

    @property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return OSMStreetGeometryTransformer(
            elevation_handler=self.elevation_handler,
            ground_offset=STREETS_GROUND_OFFSET,
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        street_type = geometry.properties.get("fclass")
        if surrounding_type := STREET_TYPE_MAPPING.get(street_type):
            return surrounding_type
        raise SurroundingException(
            f"We don't have a mapping for fclass '{street_type}'. "
            f"Add a mapping to avoid this exception."
        )
