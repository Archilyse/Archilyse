from abc import ABC
from typing import Iterator

from shapely.geometry import Polygon

from dufresne.linestring_add_width import add_width_to_linestring
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import GroundCoveringLineStringTransformer
from surroundings.v2.swisstopo.utils import is_bridge


class StreetAndRailwayTransformer(GroundCoveringLineStringTransformer, ABC):
    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        """To be used to transform swisstopo railway and street geometries"""
        if is_bridge(geometry=geometry):
            # use existing z values
            yield from add_width_to_linestring(
                line=geometry.geom,
                width=self.get_width(geometry),
                extension_type=self.get_extension_type(geometry),
            ).geoms
        else:
            # apply ground height
            yield from super(StreetAndRailwayTransformer, self).transform_geometry(
                geometry
            )
