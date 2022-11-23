from typing import Iterator

from rasterio.windows import Window
from shapely.geometry import Polygon

from common_utils.constants import SurroundingType
from surroundings.ground_excavator import GroundExcavator
from surroundings.raster_window import RasterWindow
from surroundings.raster_window_utils import get_triangles
from surroundings.utils import SurrTrianglesType

LOWERING_CONSTRUCTION_SITE = 20


class GroundHandler:
    def __init__(self, raster_window: RasterWindow):
        self.raster_window = raster_window

    def get_triangles(
        self, building_footprints: list[Polygon]
    ) -> Iterator[SurrTrianglesType]:
        triangles = get_triangles(
            transform=self.raster_window.transform,
            grid_values=self.raster_window.grid_values,
            window=Window(
                col_off=0,
                row_off=0,
                width=self.raster_window.width,
                height=self.raster_window.height,
            ),
        )
        for triangle in GroundExcavator(
            building_footprints=building_footprints
        ).excavate(
            triangles=triangles, lowering_construction_site=LOWERING_CONSTRUCTION_SITE
        ):
            yield SurroundingType.GROUNDS, triangle
