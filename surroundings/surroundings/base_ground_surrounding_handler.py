from abc import ABC
from typing import Iterator, Optional, Type

from shapely.geometry import MultiPolygon, Point, Polygon

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from surroundings.constants import BOUNDING_BOX_EXTENSION_ALTI
from surroundings.ground_excavator import GroundExcavator
from surroundings.raster_window_triangulator import RasterWindowTriangulator
from surroundings.utils import SurrTrianglesType, get_surroundings_bounding_box


class BaseGroundSurroundingHandler(ABC):
    SURROUNDING_TYPE: SurroundingType = SurroundingType.GROUNDS
    BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_ALTI
    raster_window_triangulator_cls: Type[RasterWindowTriangulator]

    @property
    def GROUND_OFFSET(self):
        return 0.0

    def __init__(
        self,
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        building_footprints: Optional[list[Polygon | MultiPolygon]] = None,
        bounding_box_extension: Optional[int] = None,
    ):
        self.simulation_version = simulation_version
        self._excavator = None
        self._raster_window_triangulator = self.raster_window_triangulator_cls(
            bounding_box=get_surroundings_bounding_box(
                x=location.x,
                y=location.y,
                bounding_box_extension=bounding_box_extension
                or self.BOUNDING_BOX_EXTENSION,
            ),
            region=region,
            ground_offset=self.GROUND_OFFSET,
        )
        if building_footprints:
            self._excavator = GroundExcavator(building_footprints=building_footprints)

    def get_triangles(self) -> Iterator[SurrTrianglesType]:
        triangles = self._raster_window_triangulator.create_triangles()
        if self._excavator:
            triangles = self._excavator.excavate(triangles=triangles)
        for triangle in triangles:
            yield self.SURROUNDING_TYPE, triangle
