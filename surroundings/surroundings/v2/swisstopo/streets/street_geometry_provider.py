from typing import Collection, Iterator

from shapely.geometry import MultiLineString

from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import STREETS_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)
from surroundings.v2.swisstopo.streets.constants import STREET_TYPES_TO_EXCLUDE
from surroundings.v2.swisstopo.streets.utils import is_pedestrian
from surroundings.v2.swisstopo.utils import is_tunnel


class SwissTopoStreetsGeometryProvider(SwissTopoShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return STREETS_FILE_TEMPLATES

    @staticmethod
    def is_excluded_type(geometry: Geometry) -> bool:
        return geometry.properties["OBJEKTART"] in STREET_TYPES_TO_EXCLUDE

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not is_tunnel(geometry=geometry) and not self.is_excluded_type(
            geometry=geometry
        )

    def get_geometries(self) -> Iterator[Geometry]:
        for geometry in super(SwissTopoStreetsGeometryProvider, self).get_geometries():
            # HACK for whatever reason the streets shape file
            # contains a few multilinestrings which require unpacking
            if isinstance(geometry.geom, MultiLineString):
                yield from (
                    Geometry(geom=line, properties=geometry.properties)
                    for line in geometry.geom.geoms
                )
            else:
                yield geometry


class SwissTopoNoisyStreetsGeometryProvider(SwissTopoStreetsGeometryProvider):
    def geometry_filter(self, geometry: Geometry) -> bool:
        return (
            not is_tunnel(geometry=geometry)
            and not self.is_excluded_type(geometry=geometry)
            and not is_pedestrian(geometry=geometry)
        )
