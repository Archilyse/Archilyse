import math
from typing import Tuple

import numpy as np
from affine import Affine
from rasterio.windows import Window

from common_utils.exceptions import BaseElevationException
from surroundings.utils import (
    TRIANGLE_OFFSETS,
    Bounds,
    PixelPosition,
    Triangle,
    TriangleOffsets,
)


def get_xy(
    transform: Affine, row: int, col: int, centroid: bool = True
) -> Tuple[float, float]:
    offset = 0.5 if centroid else 0.0
    return transform * (col + offset, row + offset)


def get_pixel(transform: Affine, x: float, y: float) -> PixelPosition:
    reverse_transform = ~transform
    col, row = map(math.floor, reverse_transform * (x, y))
    return row, col


def get_bounds(
    transform: Affine,
    width: int,
    height: int,
    row_off: int = 0,
    col_off: int = 0,
    centroid: bool = False,
) -> Bounds:
    left, top = get_xy(transform, row_off, col_off, centroid)
    if centroid:
        row, col = row_off + height - 1, col_off + width - 1
    else:
        row, col = row_off + height, col_off + width
    right, bottom = get_xy(transform, row, col, centroid)
    return left, bottom, right, top


def get_window_for_triangulation(transform: Affine, bounds: Bounds) -> Window:
    target_minx, target_miny, target_maxx, target_maxy = bounds

    window_from_row, window_from_col = get_pixel(transform, target_minx, target_maxy)
    window_to_row, window_to_col = get_pixel(transform, target_maxx, target_miny)

    window_minx, window_miny, window_maxx, window_maxy = get_bounds(
        transform=transform,
        row_off=window_from_row,
        col_off=window_from_col,
        width=window_to_col - window_from_col + 1,
        height=window_to_row - window_from_row + 1,
        centroid=True,
    )

    if window_minx > target_minx:
        window_from_col -= 1
    if window_miny > target_miny:
        window_to_row += 1

    if window_maxy < target_maxy:
        window_from_row -= 1
    if window_maxx < target_maxx:
        window_to_col += 1

    return Window(
        row_off=window_from_row,
        col_off=window_from_col,
        width=window_to_col - window_from_col + 1,
        height=window_to_row - window_from_row + 1,
    )


def get_triangle(
    raster_window,
    row: int,
    col: int,
    triangle_offsets: TriangleOffsets,
    ground_offset: float = 0.0,
) -> Triangle:
    try:
        return tuple(
            (
                *raster_window.get_xy_from_pixel(row=row + row_off, col=col + col_off),
                float(raster_window.grid_values[row + row_off, col + col_off])
                + ground_offset,
            )
            for row_off, col_off in triangle_offsets
        )
    except IndexError as e:
        raise BaseElevationException("No triangle found.") from e


def get_pixel_ratio(transform: Affine) -> float:
    return transform.a / -transform.e


def _within_triangle_bounds(
    pixel: PixelPosition,
    pixel_centroid: Tuple[float, float],
    xy: Tuple[float, float],
    src_shape: Tuple[int, int],
) -> bool:
    height, width = src_shape
    row, col = pixel
    centroid_x, centroid_y = pixel_centroid
    x, y = xy

    within_raster_window_bounds = 0 <= row < height and 0 <= col < width
    return not (
        not within_raster_window_bounds
        or (row == 0 and y > centroid_y)
        or (row == height - 1 and y <= centroid_y)
        or (col == 0 and x < centroid_x)
        or (col == width - 1 and x >= centroid_x)
    )


def get_triangle_offsets(
    x: float, y: float, transform: Affine, src_width: int, src_height: int
) -> Tuple[int, int, TriangleOffsets]:
    """Returns row, col and triangle offsets for a given x, y coordinate pair."""
    row, col = pixel = get_pixel(transform=transform, x=x, y=y)
    pixel_centroid_x, pixel_centroid_y = pixel_centroid = get_xy(
        transform=transform, row=row, col=col
    )
    # NOTE the dataset could have cells which are not squares (!!!)
    pixel_ratio = get_pixel_ratio(transform=transform)

    within_triangle_bounds = _within_triangle_bounds(
        xy=(x, y),
        pixel=pixel,
        pixel_centroid=pixel_centroid,
        src_shape=(src_height, src_width),
    )
    touches_right_border = col == src_width - 1 and x == pixel_centroid_x
    touches_bottom_border = row == src_height - 1 and y == pixel_centroid_y

    if touches_bottom_border and touches_right_border:
        return row - 1, col - 1, TRIANGLE_OFFSETS[1]
    elif touches_bottom_border:
        if x >= pixel_centroid_x:
            return row - 1, col, TRIANGLE_OFFSETS[1]
        return row - 1, col - 1, TRIANGLE_OFFSETS[1]
    elif touches_right_border:
        if y <= pixel_centroid_y:
            return row, col - 1, TRIANGLE_OFFSETS[1]
        return row - 1, col - 1, TRIANGLE_OFFSETS[1]
    elif within_triangle_bounds:
        if x >= pixel_centroid_x:
            if y <= pixel_centroid_y:
                return row, col, TRIANGLE_OFFSETS[0]
            if (y - pixel_centroid_y) * pixel_ratio > (x - pixel_centroid_x):
                return row - 1, col, TRIANGLE_OFFSETS[0]
            return row - 1, col, TRIANGLE_OFFSETS[1]
        elif y > pixel_centroid_y:
            return row - 1, col - 1, TRIANGLE_OFFSETS[1]
        elif (pixel_centroid_y - y) * pixel_ratio >= (pixel_centroid_x - x):
            return row, col - 1, TRIANGLE_OFFSETS[1]
        else:
            return row, col - 1, TRIANGLE_OFFSETS[0]

    raise BaseElevationException("No triangle found.")


def get_transform(
    bounds: Bounds,
    resolution: Tuple[float, float] | None = None,
    shape: Tuple[int, int] | None = None,
) -> Tuple[Affine, int, int]:
    min_x, min_y, max_x, max_y = bounds
    if resolution:
        x_res, y_res = resolution
        width = math.ceil((max_x - min_x) / x_res)
        height = math.ceil((max_y - min_y) / y_res)
    else:
        height, width = shape
        x_res, y_res = (max_x - min_x) / width, (max_y - min_y) / height

    transform = Affine.translation(min_x, max_y) * Affine.scale(x_res, -y_res)
    return transform, width, height


def get_triangles(
    transform: Affine,
    grid_values: np.ndarray,
    window: Window,
    z_off: float = 0.0,
) -> np.ndarray:
    height, width = window.height, window.width
    if not (height and width):
        return np.array([])

    window_slices = window.toslices()
    rows, cols = np.mgrid[window_slices] + 0.5
    z = grid_values[window_slices] + z_off
    x = cols * transform.a + transform.c
    y = rows * transform.e + transform.f

    xyz = np.dstack((x, y, z))

    top_left = xyz[0 : height - 1, 0 : width - 1]
    bottom_left = xyz[1:height, 0 : width - 1]
    top_right = xyz[0 : height - 1, 1:width]
    bottom_right = xyz[1:height, 1:width]

    number_of_triangles = (height - 1) * (width - 1) * 2
    return np.vstack(
        (
            np.dstack((top_left, bottom_left, top_right)),
            np.dstack((bottom_left, bottom_right, top_right)),
        )
    ).reshape((number_of_triangles, 3, 3))
