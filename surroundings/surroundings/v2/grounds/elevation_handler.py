import contextlib
from typing import Iterator

from shapely.geometry import Point, Polygon, box

from brooks.util.geometry_ops import get_polygons
from common_utils.exceptions import BaseElevationException
from surroundings.raster_window import RasterWindow
from surroundings.raster_window_utils import (
    get_bounds,
    get_triangle,
    get_triangle_offsets,
    get_triangles,
    get_window_for_triangulation,
)
from surroundings.utils import get_interpolated_height, triangle_intersection
from surroundings.v2.base import BaseElevationHandler


class ElevationHandler(BaseElevationHandler):
    def __init__(self, raster_window: RasterWindow):
        self.raster_window = raster_window

    def get_elevation(self, point: Point) -> float:
        x, y = point.x, point.y
        triangle_offsets = get_triangle_offsets(
            transform=self.raster_window.transform,
            src_width=self.raster_window.width,
            src_height=self.raster_window.height,
            x=x,
            y=y,
        )
        triangle = get_triangle(self.raster_window, *triangle_offsets)
        return get_interpolated_height(
            x=x,
            y=y,
            from_triangle=triangle,
        )

    def project_onto_surface(
        self, polygon: Polygon, ground_offset: float = 0.0
    ) -> Iterator[Polygon]:
        window = get_window_for_triangulation(
            transform=self.raster_window.transform,
            bounds=polygon.bounds,
        ).crop(
            height=self.raster_window.height,
            width=self.raster_window.width,
        )
        if window.width and window.height:
            triangles = get_triangles(
                transform=self.raster_window.transform,
                grid_values=self.raster_window.grid_values,
                window=window,
                z_off=ground_offset,
            )
            yield from (
                triangle_part
                for triangle in triangles
                for triangle_part in triangle_intersection(
                    footprint_2d=polygon, triangle_3d=Polygon(triangle)
                )
            )


class MultiRasterElevationHandler(BaseElevationHandler):
    def __init__(
        self,
        primary_window: RasterWindow,
        secondary_window: RasterWindow,
    ):
        self.elevation_handlers = [
            ElevationHandler(raster_window=primary_window),
            ElevationHandler(raster_window=secondary_window),
        ]

        primary_window_box, secondary_window_box = [
            box(
                *get_bounds(
                    transform=raster_window.transform,
                    width=raster_window.width,
                    height=raster_window.height,
                    centroid=True,
                )
            )
            for raster_window in [primary_window, secondary_window]
        ]
        self.bounding_boxes = [
            primary_window_box,
            secondary_window_box.difference(primary_window_box),
        ]

    def get_elevation(self, point: Point) -> float:
        for elevation_handler in self.elevation_handlers:
            with contextlib.suppress(BaseElevationException):
                return elevation_handler.get_elevation(point=point)
        raise BaseElevationException("No triangle found.")

    def project_onto_surface(
        self, polygon: Polygon, ground_offset: float = 0.0
    ) -> Iterator[Polygon]:
        for bounding_box, elevation_handler in zip(
            self.bounding_boxes, self.elevation_handlers
        ):
            for polygon_part in get_polygons(bounding_box.intersection(polygon)):
                yield from elevation_handler.project_onto_surface(
                    polygon=polygon_part, ground_offset=ground_offset
                )
