import tempfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from shapely.geometry import Point, Polygon, box

from simulations.geometry.bulk_volume_volume import (
    BuildingRasterizationHandler,
    BuildingVolumeHandler,
    GridHandler,
    SwisstopoElevationHandler,
    store_as_tif,
)


class TestGridHandler:
    @pytest.mark.parametrize(
        "resolution, geometry, expected_rows_and_cols",
        [
            (1.0, box(0.5, 0.5, 1.5, 1.5), [(0, 0), (0, 1), (1, 0), (1, 1)]),
            (2.0, box(0.5, 0.5, 1.5, 1.5), [(0, 0)]),
            (1.0, box(-1000, -1000, 1000, 1000), [(0, 0), (0, 1), (1, 0), (1, 1)]),
            (1.0, box(-1000, -1000, -500, -500), []),
            (1.0, box(1000, 1000, 1500, 1500), []),
            (1.0, box(1000, 0.5, 1500, 1.5), []),
            (1.0, box(0.5, 1000, 1.5, 1500), []),
        ],
    )
    def test_get_rows_and_cols(self, resolution, geometry, expected_rows_and_cols):
        bounds = 0.0, 0.0, 2.0, 2.0
        handler = GridHandler(bounds=bounds, resolution=resolution)

        rows_and_cols = list(handler.get_rows_and_cols(bounds=geometry.bounds))

        assert rows_and_cols == expected_rows_and_cols

    @pytest.mark.parametrize(
        "resolution, expected_shape", [(0.1, (20, 20)), (1.0, (2, 2))]
    )
    def test_shape(self, resolution, expected_shape):
        bounds = 0.0, 0.0, 2.0, 2.0
        handler = GridHandler(bounds=bounds, resolution=resolution)
        assert (handler.height, handler.width) == expected_shape

    @pytest.mark.parametrize(
        "resolution, bounds",
        [
            (0.1, (0.0, 0.0, 2.0, 2.0)),
            (1.0, (0.0, 0.0, 2.0, 2.0)),
            (1.0, (-100.0, 100.0, 200.0, 200.0)),
        ],
    )
    def test_transform(self, resolution, bounds):
        handler = GridHandler(bounds=bounds, resolution=resolution)
        assert handler.transform == Affine(
            resolution, 0.0, bounds[0], 0.0, -resolution, bounds[3]
        )

    @pytest.mark.parametrize(
        "row, col, expected_centroid",
        [
            (0, 0, Point(0.5, 1.5)),
            (0, 1, Point(1.5, 1.5)),
            (1, 1, Point(1.5, 0.5)),
            (1, 0, Point(0.5, 0.5)),
        ],
    )
    def test_get_pixel_centroid(self, row, col, expected_centroid):
        resolution = 1.0
        bounds = 0.0, 0.0, 2.0, 2.0
        handler = GridHandler(bounds=bounds, resolution=resolution)
        assert handler.get_pixel_centroid(row, col) == expected_centroid


triangle_1 = ((0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0))
triangle_2 = ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0))
triangle_3 = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0))
triangle_4 = ((0.0, 0.0, 2.0), (0.0, 1.0, 2.0), (1.0, 1.0, 2.0))


class TestBuildingRasterizationHandler:
    buildings = [
        {
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[triangle_1], [triangle_2]],
            }
        }
    ]

    def test_get_building_triangles(self):
        triangles = list(
            BuildingRasterizationHandler._get_building_triangles(self.buildings)
        )
        assert triangles == [Polygon(triangle_1), Polygon(triangle_2)]

    def test_rasterize_building_triangles(self):
        resolution = 0.5
        bounds = 0.0, 0.0, 1.0, 1.0
        grid_handler = GridHandler(bounds=bounds, resolution=resolution)

        triangles_by_row_col = (
            BuildingRasterizationHandler.rasterize_building_triangles(
                buildings=self.buildings, grid_handler=grid_handler
            )
        )

        assert triangles_by_row_col == {
            (0, 0): [triangle_2],
            (1, 0): [triangle_1, triangle_2],
            (1, 1): [triangle_1],
            (0, 1): [triangle_1, triangle_2],
        }


class TestBuildingVolumeHandler:
    @pytest.mark.parametrize(
        "x, y, triangles, expected_min_max",
        [
            (0.1, 0.1, [triangle_1, triangle_3], (0.0, 1.0)),
            (0.1, 0.9, [triangle_2, triangle_4], (0.0, 2.0)),
        ],
    )
    def test_get_min_max_heights_from_building_triangles(
        self, x, y, triangles, expected_min_max
    ):
        assert (
            BuildingVolumeHandler._get_min_max_heights_from_building_triangles(
                x=x, y=y, triangles=triangles
            )
            == expected_min_max
        )

    @pytest.mark.parametrize(
        "subterranean, ground_z, triangles, expected_volume",
        [
            (False, 0.0, [triangle_1, triangle_3], 0.25),
            (False, 0.5, [triangle_1, triangle_3], 0.125),
            (False, 5.0, [triangle_1, triangle_3], 0.0),
            (True, 0.0, [triangle_1, triangle_3], 0.0),
            (True, 0.5, [triangle_1, triangle_3], 0.125),
            (True, 5.0, [triangle_1, triangle_3], 0.25),
            (False, 0.5, [triangle_1], 0.0),
            (False, 0.5, [triangle_1, triangle_1], 0.0),
        ],
    )
    def test_get_volume(
        self, mocker, subterranean, ground_z, triangles, expected_volume
    ):
        grid_handler = GridHandler(bounds=(0.0, 0.0, 1.0, 1.0), resolution=0.5)
        mocker.patch.object(
            BuildingRasterizationHandler,
            "rasterize_building_triangles",
            return_value={(0, 0): triangles},
        )
        mocker.patch.object(
            SwisstopoElevationHandler, "get_elevation", return_value=ground_z
        )

        handler = BuildingVolumeHandler(grid_handler=grid_handler)
        assert (
            handler._get_volume(row=0, col=0, subterranean=subterranean)
            == expected_volume
        )

    def test_get_volumes_grid(self, mocker):
        grid_handler = GridHandler(bounds=(0.0, 0.0, 1.0, 1.0), resolution=0.5)
        mocker.patch.object(
            BuildingRasterizationHandler,
            "rasterize_building_triangles",
            return_value={
                (1, 0): [triangle_1, triangle_3],
                (1, 1): [triangle_1, triangle_3],
                (0, 1): [triangle_1, triangle_3],
            },
        )
        mocker.patch.object(
            SwisstopoElevationHandler, "get_elevation", return_value=0.5
        )

        volumes_grid = BuildingVolumeHandler(
            grid_handler=grid_handler
        ).get_volumes_grid(subterranean=False)

        assert volumes_grid.tolist() == [[0.0, 0.125], [0.125, 0.125]]


def test_store_as_tif():
    grid_handler = GridHandler(bounds=(0.0, 0.0, 1.0, 1.0), resolution=0.5)
    volumes_grid = np.array([[0.0, 0.125], [0.125, 0.125]])

    with tempfile.TemporaryDirectory() as tempdir:
        filename = Path(tempdir).joinpath("Momsfile.tif")
        store_as_tif(
            filename=filename,
            transform=grid_handler.transform,
            volumes_grid=volumes_grid,
        )
        with rasterio.open(filename) as dataset:
            grid_values = dataset.read(1)

    assert grid_values.tolist() == volumes_grid.tolist()
    assert grid_values.shape == (grid_handler.height, grid_handler.width)
    assert dataset.transform == grid_handler.transform
