from itertools import chain

from shapely.geometry import Polygon

from common_utils.constants import REGION
from surroundings.v2.base import BaseElevationHandler, BaseSurroundingsMixin
from surroundings.v2.osm import (
    OSMBuildingHandler,
    OSMForestHandler,
    OSMParksHandler,
    OSMRailwayHandler,
    OSMRiverHandler,
    OSMSeaHandler,
    OSMStreetHandler,
    OSMTreeHandler,
    OSMWaterHandler,
)


class OSMSurroundingsMixin(BaseSurroundingsMixin):
    @staticmethod
    def generate_small_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ):
        common_args = dict(
            bounding_box=bounding_box,
            region=region,
            elevation_handler=elevation_handler,
        )
        yield from chain(
            OSMStreetHandler(**common_args).get_triangles(),
            OSMRailwayHandler(**common_args).get_triangles(),
            OSMParksHandler(**common_args).get_triangles(),
            OSMRiverHandler(**common_args).get_triangles(),
            OSMTreeHandler(**common_args).get_triangles(),
            OSMForestHandler(**common_args).get_triangles(),
            OSMBuildingHandler(**common_args).get_triangles(),
        )

    @staticmethod
    def generate_big_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ):
        common_args = dict(
            bounding_box=bounding_box,
            region=region,
            elevation_handler=elevation_handler,
        )
        yield from chain(
            OSMWaterHandler(**common_args).get_triangles(),
            OSMSeaHandler(**common_args).get_triangles(),
        )
