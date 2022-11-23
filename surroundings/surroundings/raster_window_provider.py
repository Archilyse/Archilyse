from abc import abstractmethod
from functools import partial
from itertools import product, starmap
from typing import Collection, Tuple

import numpy as np
from affine import Affine
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, Polygon, box

from brooks.util.projections import project_geometry, project_xy
from common_utils.constants import REGION
from common_utils.exceptions import RasterNotIntersectingException, SurroundingException
from surroundings.raster_window import RasterioRasterWindow, RasterWindow
from surroundings.raster_window_utils import (
    get_bounds,
    get_transform,
    get_triangle,
    get_triangle_offsets,
    get_xy,
)
from surroundings.utils import Bounds, get_interpolated_height


class RasterWindowProvider:
    def __init__(self, region: REGION, bounds: Bounds, resolution: float | None = None):
        self.resolution = resolution
        self.bounds = bounds
        self.region = region

    @property
    def dataset_crs(self) -> REGION:
        raise NotImplementedError

    @property
    def src_resolution(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def get_raster_filenames(self, bounding_box: Polygon) -> Collection[str]:
        raise NotImplementedError

    def _get_default_dst_resolution(self):
        src_min_x, src_min_y, src_max_x, src_max_y = project_geometry(
            box(*self.bounds),
            crs_from=self.region,
            crs_to=self.dataset_crs,
        ).bounds

        src_corners = map(
            Point,
            [
                (src_min_x, src_min_y),
                (src_max_x, src_min_y),
                (src_max_x, src_max_y),
                (src_min_x, src_max_y),
            ],
        )

        dst_bottom_left, dst_bottom_right, dst_top_right, dst_top_left = tuple(
            project_geometry(src_corner, crs_from=self.dataset_crs, crs_to=self.region)
            for src_corner in src_corners
        )

        src_height = (src_max_y - src_min_y) / self.src_resolution
        src_width = (src_max_x - src_min_x) / self.src_resolution

        approx_x_resolution = (
            dst_bottom_left.distance(dst_bottom_right) / src_width
            + dst_top_left.distance(dst_top_right) / src_width
        ) / 2
        approx_y_resolution = (
            dst_bottom_left.distance(dst_top_left) / src_height
            + dst_bottom_right.distance(dst_top_right) / src_height
        ) / 2

        return approx_x_resolution, approx_y_resolution

    def _get_dst_transform(self) -> Tuple[Affine, int, int]:
        x_res, y_res = (
            self._get_default_dst_resolution()
            if not self.resolution
            else (self.resolution, self.resolution)
        )

        min_x, min_y, max_x, max_y = self.bounds
        bounds = (
            min_x - x_res / 2,
            min_y - y_res / 2,
            max_x + x_res / 2,
            max_y + y_res / 2,
        )

        return get_transform(bounds=bounds, resolution=(x_res, y_res))

    @property
    def _scale_factors(self) -> Tuple[float, float] | None:
        if self.resolution:
            x_res, y_res = self._get_default_dst_resolution()
            return x_res / self.resolution, y_res / self.resolution

    def _get_src_bounds(self) -> Bounds:
        if self.region != self.dataset_crs:
            dst_transform, dst_width, dst_height = self._get_dst_transform()
            unscaled_src_bounds = get_projected_raster_centroid_bounds(
                src_transform=dst_transform,
                src_shape=(dst_height, dst_width),
                src_crs=self.region,
                dst_crs=self.dataset_crs,
            )
        elif self.resolution:
            unscaled_src_bounds = get_bounds(
                *self._get_dst_transform(),
                centroid=True,
            )
        else:
            unscaled_src_bounds = self.bounds

        if self.resolution:
            min_x, min_y, max_x, max_y = unscaled_src_bounds
            x_scale, y_scale = self._scale_factors
            y_off = self.src_resolution / 2 / y_scale
            x_off = self.src_resolution / 2 / x_scale
            return min_x - x_off, min_y - y_off, max_x + x_off, max_y + y_off

        return unscaled_src_bounds

    def _get_filenames_buffered_bbox(self):
        buffered_bounding_box = box(*self._get_src_bounds()).buffer(
            # NOTE we add half a pixel into all directions
            # to ensure we have data to generate triangles
            # covering the entire bounding box
            self.src_resolution / 2,
            join_style=JOIN_STYLE.mitre,
            cap_style=CAP_STYLE.square,
        )
        if filenames := self.get_raster_filenames(bounding_box=buffered_bounding_box):
            return filenames
        raise SurroundingException(
            f"Couldn't find any raster file intersecting with bounding box: {self.bounds}"
        )

    def get_raster_window(self) -> RasterWindow:
        src_bounds = self._get_src_bounds()
        filenames = self._get_filenames_buffered_bbox()
        try:
            if self.region == self.dataset_crs:
                return RasterioRasterWindow(
                    *filenames,
                    src_bounds=src_bounds,
                    dst_resolution=self.resolution,
                )

            # NOTE before projecting we scale the raster
            # window to the approximate target resolution
            raster_window = RasterioRasterWindow(
                *filenames,
                src_bounds=src_bounds,
                scale_factors=self._scale_factors,
            )
        except RasterNotIntersectingException as e:
            raise SurroundingException(
                f"Couldn't find any raster file intersecting with bounding box: {self.bounds}"
            ) from e

        dst_transform, dst_width, dst_height = self._get_dst_transform()
        return resample_raster_window(
            src_raster_window=raster_window,
            src_crs=self.dataset_crs,
            dst_crs=self.region,
            dst_transform=dst_transform,
            dst_shape=(dst_height, dst_width),
        )


def resample_raster_window(
    src_raster_window: RasterWindow,
    src_crs: REGION,
    dst_crs: REGION,
    dst_transform: Affine,
    dst_shape: Tuple[int, int],
) -> RasterWindow:
    """
    This method creates a new raster window in dst_crs by resampling the original raster window
    using the grid points defined by dst_transform and dst_shape projected into src_crs.
    To determine the elevations at those points we use triangle interpolation.
    """
    dst_height, dst_width = dst_shape

    get_dst_xy = partial(get_xy, dst_transform, centroid=True)
    dst_xs, dst_ys = zip(
        *starmap(get_dst_xy, product(range(dst_height), range(dst_width)))
    )

    src_xs, src_ys = project_xy(
        xs=dst_xs,
        ys=dst_ys,
        crs_from=dst_crs,
        crs_to=src_crs,
    )

    src_triangle_offsets = partial(
        get_triangle_offsets,
        transform=src_raster_window.transform,
        src_width=src_raster_window.width,
        src_height=src_raster_window.height,
    )

    dst_zs = (
        get_interpolated_height(
            *src_xy,
            from_triangle=get_triangle(
                src_raster_window, *src_triangle_offsets(*src_xy)
            ),
        )
        for src_xy in zip(src_xs, src_ys)
    )

    grid_values_interpolated = np.fromiter(
        iter=dst_zs, dtype=float, count=dst_width * dst_height
    ).reshape(dst_height, dst_width)

    return RasterWindow(transform=dst_transform, grid_values=grid_values_interpolated)


def get_projected_raster_centroid_bounds(
    src_transform: Affine,
    src_shape: Tuple[int, int],
    src_crs: REGION,
    dst_crs: REGION,
) -> Bounds:
    src_height, src_width = src_shape
    get_src_xy = partial(get_xy, src_transform, centroid=True)
    border_src_xys = zip(
        *starmap(get_src_xy, product(range(src_height), [0, src_width - 1])),
        *starmap(get_src_xy, product([0, src_height - 1], range(src_width))),
    )
    dst_xs, dst_ys = project_xy(
        *border_src_xys,
        crs_from=src_crs,
        crs_to=dst_crs,
    )
    return min(dst_xs), min(dst_ys), max(dst_xs), max(dst_ys)
