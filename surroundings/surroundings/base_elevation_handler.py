from abc import ABC, abstractmethod
from functools import cached_property, partial
from typing import Optional, Union

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import transform

from common_utils.constants import REGION, SIMULATION_VERSION
from surroundings.raster_window import RasterWindow
from surroundings.raster_window_utils import get_triangle, get_triangle_offsets
from surroundings.utils import (
    Bounds,
    get_interpolated_height,
    get_surroundings_bounding_box,
)


def get_elevation_handler(
    region: REGION,
    location: Point,
    simulation_version: SIMULATION_VERSION,
    bounding_box_extension: Optional[float] = None,
):
    from surroundings.srtm import SRTMElevationHandler
    from surroundings.swisstopo import SwisstopoElevationHandler

    elevation_handler = {
        REGION.CH: SwisstopoElevationHandler,
        REGION.MC: ZeroElevationHandler,
        REGION.US_PENNSYLVANIA: ZeroElevationHandler,
        REGION.DK: ZeroElevationHandler,
    }.get(region, SRTMElevationHandler)
    return elevation_handler(
        location=location,
        region=region,
        bounding_box_extension=bounding_box_extension,
        simulation_version=simulation_version,
    )


class BaseElevationHandler(ABC):
    def __init__(self, *args, **kwargs):
        pass

    def _apply_ground_height_func(self, x, y, offset: float = 0.0):
        if not isinstance(x, float):
            z = (
                self.get_elevation(point=Point(_x, _y)) + offset for _x, _y in zip(x, y)
            )
            return x, y, tuple(z)

        new_z = self.get_elevation(point=Point(x, y)) + offset
        return (
            x,
            y,
            new_z,
        )

    def apply_ground_height(
        self, geom: Union[Point, LineString, Polygon], offset: float = 0.0
    ) -> Union[Point, LineString, Polygon]:
        func = partial(self._apply_ground_height_func, offset=offset)
        transformed = transform(func, geom)
        return transformed

    @classmethod
    @abstractmethod
    def get_elevation(cls, point: Point) -> float:
        raise NotImplementedError()


class ZeroElevationHandler(BaseElevationHandler):
    def __init__(self, *args, **kwargs):
        pass

    def get_elevation(self, point: Point) -> float:
        return 0.0


class TriangleElevationHandler(BaseElevationHandler, ABC):
    BOUNDING_BOX_EXTENSION: int
    GROUND_OFFSET: float = 0.0

    def __init__(
        self,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        location: Optional[Point] = None,
        bounding_box_extension: Optional[float] = None,
        bounds: Optional[Bounds] = None,
    ):
        if bounds and (location or bounding_box_extension):
            raise ValueError(
                "Argument bounds is mutually exclusive with arguments location and bounding_box_extension."
            )
        elif not (bounds or location):
            raise ValueError("Argument location or bounds are required.")

        self.region = region
        self.simulation_version = simulation_version
        self.bounds = (
            bounds
            or get_surroundings_bounding_box(
                x=location.x,
                y=location.y,
                bounding_box_extension=bounding_box_extension
                or self.BOUNDING_BOX_EXTENSION,
            ).bounds
        )

    @property
    def raster_window_provider(self):
        raise NotImplementedError

    @cached_property
    def _raster_window(self) -> RasterWindow:
        return self.raster_window_provider.get_raster_window()

    def get_elevation(self, point: Point) -> float:
        x, y = point.x, point.y
        triangle_offsets = get_triangle_offsets(
            x=x,
            y=y,
            transform=self._raster_window.transform,
            src_width=self._raster_window.width,
            src_height=self._raster_window.height,
        )
        return (
            get_interpolated_height(
                x=x,
                y=y,
                from_triangle=get_triangle(self._raster_window, *triangle_offsets),
            )
            + self.GROUND_OFFSET
        )
