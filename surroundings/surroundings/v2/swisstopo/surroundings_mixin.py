from itertools import chain

from shapely.geometry import Polygon

from common_utils.constants import REGION
from surroundings.v2.base import BaseElevationHandler, BaseSurroundingsMixin
from surroundings.v2.swisstopo import (
    SwissTopoBuildingsHandler,
    SwissTopoForestHandler,
    SwissTopoParksHandler,
    SwissTopoRailwayHandler,
    SwissTopoRiverLinesHandler,
    SwissTopoStreetsHandler,
    SwissTopoTreeHandler,
    SwissTopoWaterHandler,
)


class SwissTopoSurroundingsMixin(BaseSurroundingsMixin):
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
            SwissTopoRiverLinesHandler(**common_args).get_triangles(),
            SwissTopoStreetsHandler(**common_args).get_triangles(),
            SwissTopoRailwayHandler(**common_args).get_triangles(),
            SwissTopoParksHandler(**common_args).get_triangles(),
            SwissTopoBuildingsHandler(**common_args).get_triangles(),
            SwissTopoTreeHandler(**common_args).get_triangles(),
            SwissTopoForestHandler(**common_args).get_triangles(),
        )

    @staticmethod
    def generate_big_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ):
        yield from SwissTopoWaterHandler(
            bounding_box=bounding_box,
            region=region,
            elevation_handler=elevation_handler,
        ).get_triangles()
