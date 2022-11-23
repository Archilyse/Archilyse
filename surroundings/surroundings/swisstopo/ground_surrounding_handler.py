from typing import Optional

from shapely.geometry import Point, Polygon

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from common_utils.logger import logger
from surroundings.base_ground_surrounding_handler import BaseGroundSurroundingHandler
from surroundings.constants import (
    BOUNDING_BOX_EXTENSION_ALTI,
    BOUNDING_BOX_EXTENSION_MOUNTAINS,
)
from surroundings.swisstopo.raster_window_triangulator import (
    SwissTopoGroundsTriangulator,
    SwissTopoMountainsTriangulator,
)
from surroundings.utils import get_surroundings_bounding_box


class SwissTopoGroundSurroundingHandler(BaseGroundSurroundingHandler):
    raster_window_triangulator_cls = SwissTopoGroundsTriangulator

    @property
    def GROUND_OFFSET(self):
        return (
            0.0
            if self.simulation_version
            in {SIMULATION_VERSION.EXPERIMENTAL, SIMULATION_VERSION.PH_2022_H1}
            else -2.0
        )


class SwissTopoMountainSurroundingHandler:
    GROUND_OFFSET = -10

    def __init__(
        self,
        location: Point,
        simulation_version: SIMULATION_VERSION,
        bounding_box_extension: Optional[float] = BOUNDING_BOX_EXTENSION_ALTI,
        region: Optional[REGION] = REGION.CH,
        mountain_bounding_box_extension: Optional[
            float
        ] = BOUNDING_BOX_EXTENSION_MOUNTAINS,
    ):
        self.location = location
        self.simulation_version = simulation_version
        self.exclusion_footprint = get_surroundings_bounding_box(
            x=location.x, y=location.y, bounding_box_extension=bounding_box_extension
        )
        self.raster_window_triangulator = SwissTopoMountainsTriangulator(
            region=region,
            ground_offset=self.GROUND_OFFSET,
            bounding_box=get_surroundings_bounding_box(
                x=location.x,
                y=location.y,
                bounding_box_extension=mountain_bounding_box_extension,
            ),
        )

    def get_triangles(self):
        for triangle in self.raster_window_triangulator.create_triangles():
            if not Polygon(triangle).intersects(self.exclusion_footprint):
                yield SurroundingType.MOUNTAINS, triangle
        logger.info(f"Mountains successfully calculated for location {self.location}")
