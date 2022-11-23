from typing import Iterable

from shapely.geometry import LineString

from brooks.util.geometry_ops import get_line_strings
from common_utils.constants import NOISE_SOURCE_TYPE
from surroundings.base_noise_source_geometry_provider import (
    BaseNoiseSourceGeometryProvider,
)
from surroundings.v2.swisstopo.railways.railway_geometry_provider import (
    SwissTopoNoisyRailwayGeometryProvider,
)
from surroundings.v2.swisstopo.streets.street_geometry_provider import (
    SwissTopoNoisyStreetsGeometryProvider,
)


class SwissTopoNoiseSourceGeometryProvider(BaseNoiseSourceGeometryProvider):
    def get_source_geometries(
        self, noise_source_type: NOISE_SOURCE_TYPE
    ) -> Iterable[LineString]:
        surrounding_handlers = {
            NOISE_SOURCE_TYPE.TRAFFIC: SwissTopoNoisyStreetsGeometryProvider,
            NOISE_SOURCE_TYPE.TRAIN: SwissTopoNoisyRailwayGeometryProvider,
        }
        for geometry in surrounding_handlers[noise_source_type](
            region=self.region,
            bounding_box=self.bounding_box,
        ).get_geometries():
            yield from get_line_strings(self.bounding_box.intersection(geometry.geom))
