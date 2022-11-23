from itertools import product
from typing import Iterator, Optional

from shapely.geometry import Polygon

from common_utils.constants import REGION
from surroundings.raster_window_provider import RasterWindowProvider
from surroundings.raster_window_utils import get_triangle
from surroundings.utils import TRIANGLE_OFFSETS, Triangle


class RasterWindowTriangulator:
    def __init__(
        self,
        bounding_box: Polygon,
        region: REGION,
        ground_offset: float = 0.0,
        scale_factor: Optional[float] = None,
    ):
        self.region = region
        self.ground_offset = ground_offset
        self.bounding_box = bounding_box
        self.scale_factor = scale_factor or 1

    @property
    def raster_window_provider(self) -> RasterWindowProvider:
        raise NotImplementedError

    def create_triangles(self) -> Iterator[Triangle]:
        window = self.raster_window_provider.get_raster_window()
        for i, j, triangle_offsets in product(
            range(window.height - 1), range(window.width - 1), TRIANGLE_OFFSETS
        ):
            yield get_triangle(window, i, j, triangle_offsets, self.ground_offset)
