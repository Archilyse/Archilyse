import numpy as np
import pytest
from affine import Affine
from rasterio.windows import Window

from common_utils.exceptions import BaseElevationException
from surroundings.raster_window_utils import (
    get_bounds,
    get_pixel,
    get_transform,
    get_triangle_offsets,
    get_triangles,
    get_window_for_triangulation,
    get_xy,
)
from surroundings.utils import TRIANGLE_OFFSETS

transform = Affine.translation(0, 10) * Affine.scale(1, -1)


@pytest.mark.parametrize(
    "xy, expected_pixel",
    [
        ((0, 0), (10, 0)),
        ((10, 10), (0, 10)),
        ((9.5, 9.5), (0, 9)),
    ],
)
def test_get_pixel(xy, expected_pixel):
    assert get_pixel(transform=transform, x=xy[0], y=xy[1]) == expected_pixel


@pytest.mark.parametrize(
    "pixel, expected_xy",
    [
        ((10, 0), (0.5, -0.5)),
        ((0, 10), (10.5, 9.5)),
        ((0, 9), (9.5, 9.5)),
    ],
)
def test_get_xy(pixel, expected_xy):
    assert get_xy(transform=transform, row=pixel[0], col=pixel[1]) == expected_xy


@pytest.mark.parametrize(
    "expected_xy, pixel",
    [
        ((0, 0), (10, 0)),
        ((10, 10), (0, 10)),
        ((9.0, 10.0), (0, 9)),
    ],
)
def test_get_xy_upper_left_corner(pixel, expected_xy):
    assert (
        get_xy(transform=transform, row=pixel[0], col=pixel[1], centroid=False)
        == expected_xy
    )


@pytest.mark.parametrize(
    "col_off, row_off, width, height, centroid, expected_bounds",
    [
        (0, 0, 10, 10, False, (0, 0, 10, 10)),
        (0, 0, 10, 10, True, (0.5, 0.5, 9.5, 9.5)),
        (-10, -10, 30, 30, False, (-10, -10, 20, 20)),
    ],
)
def test_get_bounds(col_off, row_off, width, height, centroid, expected_bounds):
    assert (
        get_bounds(
            transform=transform,
            width=width,
            height=height,
            row_off=row_off,
            col_off=col_off,
            centroid=centroid,
        )
        == expected_bounds
    )


@pytest.mark.parametrize(
    "bounds, expected_window",
    [
        ((0.5, 0.5, 9.5, 9.5), Window(0, 0, 10, 10)),
        ((0.5, 0.5, 9.6, 9.6), Window(0, -1, 11, 11)),
        ((0.4, 0.4, 9.5, 9.5), Window(-1, 0, 11, 11)),
        ((0, 0, 10, 10), Window(-1, -1, 12, 12)),
        ((-10, -10, 10, 10), Window(-11, -1, 22, 22)),
    ],
)
def test_get_window_for_triangulation(bounds, expected_window):
    assert (
        get_window_for_triangulation(transform=transform, bounds=bounds)
        == expected_window
    )


@pytest.mark.parametrize(
    "x, y, row, col, offsets",
    [
        (0.5, 0.5, 1, 0, TRIANGLE_OFFSETS[1]),
        (0.75, 0.75, 1, 0, TRIANGLE_OFFSETS[1]),
        (0.75, 0.625, 1, 0, TRIANGLE_OFFSETS[1]),
        (0.625, 0.75, 1, 0, TRIANGLE_OFFSETS[0]),
        (1.0, 1.0, 1, 1, TRIANGLE_OFFSETS[0]),
        (1.25, 1.25, 0, 1, TRIANGLE_OFFSETS[1]),
        (1.25, 1.125, 0, 1, TRIANGLE_OFFSETS[1]),
        (1.125, 1.25, 0, 1, TRIANGLE_OFFSETS[0]),
        # touching right border
        (2.0, 2.0, 0, 1, TRIANGLE_OFFSETS[1]),
        (2.0, 1.5, 0, 1, TRIANGLE_OFFSETS[1]),
        (2.0, 1.0, 1, 1, TRIANGLE_OFFSETS[1]),
        (2.0, 0.5, 1, 1, TRIANGLE_OFFSETS[1]),
        # touching bottom border
        (0.0, 0.0, 1, 0, TRIANGLE_OFFSETS[1]),
        (0.5, 0.0, 1, 0, TRIANGLE_OFFSETS[1]),
        (1.0, 0.0, 1, 1, TRIANGLE_OFFSETS[1]),
        (1.5, 0.0, 1, 1, TRIANGLE_OFFSETS[1]),
        # touching bottom right corner
        (2.0, 0.0, 1, 1, TRIANGLE_OFFSETS[1]),
    ],
)
def test_get_triangle_offsets(x, y, row, col, offsets):
    assert get_triangle_offsets(
        x=x,
        y=y,
        transform=Affine.translation(-0.5, 2.5) * Affine.scale(1.0, -1.0),
        src_width=3,
        src_height=3,
    ) == (row, col, offsets)


@pytest.mark.parametrize(
    "x, y",
    [
        (-0.25, -0.25),
        (1.25, 1.25),
        (-0.25, 1.25),
        (1.25, -0.25),
        (0.5, 1.25),
        (0.5, -0.25),
        (1.25, 0.5),
        (-0.25, 0.5),
    ],
)
def test_get_triangle_offsets_raises_out_of_grid_exception(x, y):
    with pytest.raises(BaseElevationException, match="No triangle found."):
        get_triangle_offsets(
            x=x,
            y=y,
            transform=Affine.translation(-0.5, 1.5) * Affine.scale(1.0, -1.0),
            src_width=2,
            src_height=2,
        )


@pytest.mark.parametrize(
    "resolution, shape, expected_transform, expected_width, expected_height",
    [
        (None, (2, 2), Affine.translation(0, 1) * Affine.scale(0.5, -0.5), 2, 2),
        (None, (2, 4), Affine.translation(0, 1) * Affine.scale(0.25, 0.5), 4, 2),
        ((0.5, 0.5), None, Affine.translation(0, 1) * Affine.scale(0.5, -0.5), 2, 2),
        ((0.25, 0.5), None, Affine.translation(0, 1) * Affine.scale(0.5, -0.5), 4, 2),
        ((0.3, 0.3), None, Affine.translation(0, 1) * Affine.scale(0.3, -0.3), 4, 4),
    ],
)
def test_get_transform(
    resolution, shape, expected_transform, expected_width, expected_height
):
    assert get_transform(bounds=(0, 0, 1, 1), resolution=resolution, shape=shape)


TRIANGLES_1x1 = np.array(
    [
        [[0.5, 1.5, 1.0], [0.5, 0.5, 1.0], [1.5, 1.5, 1.0]],
        [[0.5, 0.5, 1.0], [1.5, 0.5, 1.0], [1.5, 1.5, 1.0]],
    ],
)


@pytest.mark.parametrize(
    "grid_values, transform, window, expected_triangles",
    [
        (
            np.ones((2, 2)),
            Affine.translation(0, 2) * Affine.scale(1, -1),
            Window(0, 0, 2, 2),
            TRIANGLES_1x1,
        ),
        (
            np.ones((3, 3)),
            Affine.translation(0, 2) * Affine.scale(1, -1),
            Window(0, 0, 2, 2),
            TRIANGLES_1x1,
        ),
        (
            np.ones((2, 2)),
            Affine.translation(0, 2) * Affine.scale(1, -1),
            Window(0, 0, 0, 0),
            np.array([]),
        ),
    ],
)
def test_get_triangles(grid_values, transform, window, expected_triangles):
    triangles = get_triangles(
        grid_values=grid_values, transform=transform, window=window
    )
    assert np.array_equal(
        triangles,
        expected_triangles,
    )
