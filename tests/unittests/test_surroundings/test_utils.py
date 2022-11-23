from pathlib import Path
from unittest.mock import call

import pytest
from shapely.geometry import Polygon, box

from common_utils.constants import GOOGLE_CLOUD_BUCKET
from surroundings.utils import (
    SHAPEFILE_SUFFIX,
    download_shapefile_if_not_exists,
    get_interpolated_height,
    triangle_intersection,
)


@pytest.mark.parametrize(
    "x,y,expected_height",
    [(0.5, 0.5, 0.75), (0.0, 0.0, 0.0), (0.5, 1.0, 1.0), (0.5, 1.0, 1.0)],
)
def test_get_interpolated_height_equilateral_triangle(x, y, expected_height):
    input_triangle = [(0, 0, 0), (1, 0, 1), (0.5, 1, 1)]
    assert get_interpolated_height(x, y, input_triangle) == expected_height


@pytest.mark.parametrize(
    "x,y,expected_height",
    [(0.75, 0.75, 1.5), (0.5, 0, 0.5), (1.0, 1.0, 2.0), (0.99, 0.99, 1.98)],
)
def test_get_interpolated_height_right_triangle(x, y, expected_height):
    input_triangle = [(0, 0, 0), (1, 0, 1), (1, 1, 2)]
    assert get_interpolated_height(x, y, input_triangle) == expected_height


def test_download_shapefile_if_not_exists(mocked_gcp_download):
    path = Path("salpica")

    download_shapefile_if_not_exists(path, path)

    calls = [
        call(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            remote_file_path=path.with_suffix(pattern),
            local_file_name=path.with_suffix(pattern),
        )
        for pattern in SHAPEFILE_SUFFIX
    ]

    mocked_gcp_download.assert_has_calls(calls, any_order=True)


@pytest.mark.parametrize(
    "footprint_2d, triangle_3d, expected_intersection",
    [
        (
            (0, 0, 1, 1),
            [(0, 0, -1), (1, 0, -1), (1, 1, -1), (0, 0, -1)],
            [[(0, 0, -1), (1, 0, -1), (1, 1, -1), (0, 0, -1)]],
        ),
        (
            (0, 0, 1, 1),
            [(0, 0, -1), (2, 0, -1), (2, 2, -1), (0, 0, -1)],
            [[(0, 0, -1), (1, 1, -1), (1, 0, -1), (0, 0, -1)]],
        ),
        (
            (0, 0, 1, 1),
            [(0, 0, 0), (2, 0, -2), (2, 2, -2), (0, 0, 0)],
            [[(0, 0, 0), (1, 1, -1), (1, 0, -1), (0, 0, 0)]],
        ),
    ],
)
def test_triangle_intersection(footprint_2d, triangle_3d, expected_intersection):
    assert (
        list(
            polygon.exterior.coords[:]
            for polygon in triangle_intersection(
                footprint_2d=box(*footprint_2d), triangle_3d=Polygon(triangle_3d)
            )
        )
        == expected_intersection
    )
