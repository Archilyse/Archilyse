from pathlib import Path

import numpy as np
import pytest
from affine import Affine
from numpy import dtype
from rasterio import RasterioIOError
from rasterio.windows import Window

from common_utils.exceptions import (
    RasterNotIntersectingException,
    RasterWindowNoDataException,
)
from surroundings.raster_window import RasterioRasterWindow
from tests.surroundings_utils import create_raster_file, create_rasterio_dataset

NODATA = -9999.0


class TestRasterioRasterWindow:
    @pytest.mark.parametrize(
        "data",
        [
            np.array([[[0.0, 1.0]]]),
            np.array([[[0.0, 1.0]] * 2]),
            np.array([[[0.0, 1.0, 2.0]] * 2]),
            np.array([[[0.0, 1.0, 2.0], [0.0, 1.0, 2.0], [4.0, 1.0, 2.0]]]),
            np.array([[[NODATA, 1.0]]]),
        ],
    )
    def test_get_grid_values(self, data):
        _, height, width = data.shape
        window_entire_grid = Window(0, 0, width, height)
        out_shape_no_resampling = (height, width)

        with create_rasterio_dataset(data, nodata=NODATA) as dataset:
            grid_values = RasterioRasterWindow._get_grid_values(
                dataset=dataset,
                window=window_entire_grid,
                out_shape=out_shape_no_resampling,
                fill_nodata=False,
            )

        assert np.array_equal(data[0], grid_values)

    @pytest.mark.parametrize(
        "data, out_shape, data_scaled",
        [
            (np.array([[[0.0, 1.0]] * 2]), (1, 1), [[0.5]]),
            (np.array([[[NODATA, 1.0], [0.0, 1.0]]]), (1, 1), [[2 / 3]]),
            (np.array([[[NODATA, NODATA], [0.0, 1.0]]]), (1, 1), [[0.5]]),
            (
                np.array([[[NODATA, NODATA, 0.0, 1.0]] * 4]),
                (2, 2),
                [[0.5, 0.5], [0.5, 0.5]],
            ),
            (np.array([[[0.0, 1.0, 0.0, 1.0]] * 4]), (2, 2), [[0.5, 0.5], [0.5, 0.5]]),
        ],
    )
    def test_get_grid_values_scaled(self, data, out_shape, data_scaled):
        _, height, width = data.shape
        window_entire_grid = Window(0, 0, width, height)

        with create_rasterio_dataset(data, nodata=NODATA) as dataset:
            grid_values = RasterioRasterWindow._get_grid_values(
                dataset=dataset,
                window=window_entire_grid,
                out_shape=out_shape,
                fill_nodata=True,
            )

        assert np.allclose(data_scaled, grid_values)

    def test_get_grid_values_raises_nodata_exception(self):
        _, height, width = shape = (1, 2, 2)
        window_entire_grid = Window(0, 0, width, height)
        out_shape_no_resampling = (height, width)

        with create_rasterio_dataset(
            data=np.full(shape, NODATA), nodata=NODATA
        ) as dataset, pytest.raises(RasterWindowNoDataException):
            RasterioRasterWindow._get_grid_values(
                dataset=dataset,
                window=window_entire_grid,
                out_shape=out_shape_no_resampling,
                fill_nodata=True,
            )

    @pytest.mark.parametrize(
        "data, expected_grid_values",
        [
            (np.array([[[1.0, NODATA]]]), np.ones((1, 2))),
            (np.array([[[1.0, 1.0], [NODATA, 1.0]]]), np.ones((2, 2))),
            (np.array([[[1.0, NODATA], [NODATA, 1.0]]]), np.ones((2, 2))),
            (np.array([[[1.0, NODATA], [1.0, NODATA]]]), np.ones((2, 2))),
            (np.array([[[NODATA, NODATA], [1.0, 1.0]]]), np.ones((2, 2))),
            (np.array([[[NODATA, NODATA], [NODATA, 1.0]]]), np.ones((2, 2))),
            (
                np.array([[[NODATA, NODATA], [NODATA, NODATA], [NODATA, 1.0]]]),
                np.ones((3, 2)),
            ),
            (
                np.array([[[NODATA, NODATA, 0.0, 1.0]] * 4]),
                np.array([[0.0, 0.0, 0.0, 1.0]] * 4),
            ),
            (
                np.array([[[NODATA, NODATA, NODATA, 1.0]] + [[NODATA] * 4] * 3]),
                np.ones((4, 4)),
            ),
        ],
    )
    def test_get_grid_values_fill_nodata(self, data, expected_grid_values):
        _, height, width = data.shape
        window_entire_grid = Window(0, 0, width, height)
        out_shape_no_resampling = (height, width)

        with create_rasterio_dataset(data=data, nodata=NODATA) as dataset:
            grid_values = RasterioRasterWindow._get_grid_values(
                dataset=dataset,
                window=window_entire_grid,
                out_shape=out_shape_no_resampling,
                fill_nodata=True,
            )

        assert np.array_equal(grid_values, expected_grid_values)

    def test_init_wrong_filename_raises(self):
        with pytest.raises(RasterioIOError):
            RasterioRasterWindow(Path("salpica"), src_bounds=(0, 0, 1, 1))

    def test_bounds_out_of_raster(self, fixtures_path):
        with create_raster_file(
            data=np.zeros((1, 2, 2)), bounds=(100, 100, 101, 101)
        ) as raster_file, pytest.raises(RasterNotIntersectingException):
            RasterioRasterWindow(raster_file.name, src_bounds=(0, 0, 1, 1))

    def test_get_value_at_xy_out_of_window(self, fixtures_path):
        bounds = (0, 0, 2, 2)
        with create_raster_file(data=np.zeros((1, 2, 2)), bounds=bounds) as raster_file:
            window = RasterioRasterWindow(raster_file.name, src_bounds=bounds)

        with pytest.raises(RasterNotIntersectingException):
            window.get_value_at_xy(-1, -1)

        with pytest.raises(RasterNotIntersectingException):
            window.get_value_at_xy(10**6, 10**6)

    @pytest.mark.parametrize(
        "x, y, z",
        [
            (0.0, 1.0, 0.0),
            (0.0, 2.0, 0.0),
            (1.0, 2.0, 1.0),
            (1.0, 1.0, 0.0),
        ],
    )
    def test_get_value_at_xy_in_window(self, x, y, z):
        with create_raster_file(
            data=np.array([[[0.0, 1.0], [0.0, 0.0]]]), bounds=(0, 0, 2, 2)
        ) as raster_file:
            window = RasterioRasterWindow(
                raster_file.name,
                src_bounds=(0, 0, 2, 2),
            )
        assert window.get_value_at_xy(x=x, y=y) == z

    @pytest.mark.parametrize(
        "row, col, x, y",
        [
            (1, 0, 0.5, 0.5),
            (0, 0, 0.5, 1.5),
        ],
    )
    def test_get_xy_from_pixel(self, row, col, x, y):
        with create_raster_file(
            data=np.zeros((1, 2, 2)), bounds=(0, 0, 2, 2)
        ) as raster_file:
            window = RasterioRasterWindow(
                raster_file.name,
                src_bounds=(0, 0, 2, 2),
            )
        assert window.get_xy_from_pixel(row=row, col=col) == (x, y)

    @pytest.mark.parametrize(
        "x, y, row, col",
        [
            (0.0, 1.0, 1, 0),
            (0.5, 0.5, 1, 0),
            (0.0, 2.0, 0, 0),
        ],
    )
    def test_get_pixel_from_xy(self, x, y, row, col):
        with create_raster_file(
            data=np.zeros((1, 2, 2)), bounds=(0, 0, 2, 2)
        ) as raster_file:
            window = RasterioRasterWindow(
                raster_file.name,
                src_bounds=(0, 0, 2, 2),
            )
        assert window.get_pixel_from_xy(x=x, y=y) == (row, col)

    def test_get_merged_dataset(self):
        nodata = -1.0
        crs_ch = "EPSG:2056"

        with create_raster_file(
            data=np.zeros((1, 2, 2)),
            bounds=(0, 0, 2, 2),
            crs=crs_ch,
            nodata=nodata,
        ) as first_raster_file, create_raster_file(
            data=np.ones((1, 2, 2)), bounds=(4, 0, 6, 2), crs=crs_ch, nodata=nodata
        ) as second_raster_file:
            filenames = (Path(first_raster_file.name), Path(second_raster_file.name))

            with RasterioRasterWindow._get_merged_dataset(
                filenames=filenames,
                bounds=(0.5, 0.5, 7.5, 1.5),
            ) as dataset:
                assert dataset.bounds == (0.0, 0.0, 8.0, 2.0)
                assert dataset.crs == crs_ch
                assert dataset.nodata == nodata
                assert np.array_equal(
                    dataset.read(1),
                    np.array([[0, 0, nodata, nodata, 1.0, 1.0, nodata, nodata]] * 2),
                )
                assert np.array_equal(
                    dataset.read_masks(1),
                    np.array([[255, 255, 0, 0, 255, 255, 0, 0]] * 2),
                )

    @pytest.mark.parametrize(
        "raster_tiles, expected_width, expected_height, expected_bounds, expected_elevation",
        [
            (
                ["swiss_1047_3"],
                875,
                600,
                (2602500.0, 1266000.0, 2611250.0, 1272000.0),
                [(2606875.0, 1269000.0, -9999.0)],
            ),
            (
                ["swiss_1067_1"],
                875,
                600,
                (2602500.0, 1260000.0, 2611250.0, 1266000.0),
                [(2606875.0, 1263000.0, 406.0108)],
            ),
            (
                ["swiss_1047_4"],
                875,
                600,
                (2611250.0, 1266000.0, 2620000.0, 1272000.0),
                [(2615625.0, 1269000.0, 285.6404)],
            ),
            (
                ["swiss_1067_2"],
                875,
                600,
                (2611250.0, 1260000.0, 2620000.0, 1266000.0),
                [(2615625.0, 1263000.0, 319.076)],
            ),
            (
                ["swiss_1047_3", "swiss_1067_1"],
                875,
                1200,
                (2602500.0, 1260000.0, 2611250.0, 1272000.0),
                [(2606875.0, 1269000.0, -9999.0), (2606875.0, 1263000.0, 406.0108)],
            ),
            (
                [
                    "swiss_1047_3",
                    "swiss_1067_1",
                    "swiss_1047_4",
                    "swiss_1067_2",
                ],
                1750,
                1200,
                (2602500.0, 1260000.0, 2620000.0, 1272000.0),
                [
                    (2606875.0, 1269000.0, -9999.0),
                    (2606875.0, 1263000.0, 406.0108),
                    (2615625.0, 1269000.0, 285.6404),
                    (2615625.0, 1263000.0, 319.076),
                ],
            ),
            (
                [
                    "swiss_1047_3",
                    "swiss_1067_1",
                    "swiss_1047_4",
                ],
                1750,
                1200,
                (2602500.0, 1260000.0, 2620000.0, 1272000.0),
                [
                    (2606875.0, 1269000.0, -9999.0),
                    (2606875.0, 1263000.0, 406.0108),
                    (2615625.0, 1269000.0, 285.6404),
                    (2615625.0, 1263000.0, -9999.0),
                ],
            ),
        ],
    )
    def test_get_merged_dataset_using_swisstopo(
        self,
        raster_tiles,
        expected_width,
        expected_height,
        expected_bounds,
        expected_elevation,
        mocked_swisstopo_esri_ascii_grid,
    ):
        with mocked_swisstopo_esri_ascii_grid(*raster_tiles) as mocked_raster_tiles:
            with RasterioRasterWindow._get_merged_dataset(
                mocked_raster_tiles,
                bounds=(
                    expected_bounds[0] + 5,
                    expected_bounds[1] + 5,
                    expected_bounds[2] - 5,
                    expected_bounds[3] - 5,
                ),
            ) as dataset:
                assert dataset.bounds == expected_bounds
                assert dataset.width == expected_width
                assert dataset.height == expected_height
                assert dataset.nodata == NODATA

                grid_values = dataset.read(1)
                for x, y, expected_z in expected_elevation:
                    z = grid_values[dataset.index(x, y)]
                    assert z == pytest.approx(expected_z)

    @pytest.mark.parametrize(
        "window, resolution, expected_transform, expected_shape",
        [
            (
                Window(0, 0, 10, 10),
                1,
                Affine.translation(0, 10) * Affine.scale(1, -1),
                (10, 10),
            ),
            (
                Window(0, 0, 10, 10),
                None,
                Affine.translation(0, 10) * Affine.scale(1, -1),
                (10, 10),
            ),
            (
                Window(0, 0, 10, 10),
                10,
                Affine.translation(0, 10) * Affine.scale(10, -10),
                (1, 1),
            ),
            (
                Window(0, 0, 10, 10),
                2,
                Affine.translation(0, 10) * Affine.scale(2, -2),
                (5, 5),
            ),
            (
                Window(5, 5, 5, 5),
                None,
                Affine.translation(5, 5) * Affine.scale(1, -1),
                (5, 5),
            ),
        ],
    )
    def test_get_transform(
        self, window, resolution, expected_transform, expected_shape
    ):
        dataset_transform = Affine.translation(0, 10) * Affine.scale(1, -1)

        window_transform, width, height = RasterioRasterWindow._get_transform(
            src_transform=dataset_transform,
            src_window=window,
            dst_resolution=resolution,
        )

        assert window_transform == expected_transform
        assert (width, height) == expected_shape

    @pytest.mark.parametrize(
        "bounds, expected_window",
        [
            ((1.5, 0, 3.0, 3.0), Window(row_off=6, col_off=1, height=4, width=3)),
            ((1, 0, 3.0, 3.0), Window(row_off=6, col_off=0, height=4, width=4)),
            ((0, 0, 3.0, 3.0), Window(row_off=6, col_off=0, height=4, width=4)),
            ((0, 0, 10, 5), Window(row_off=4, col_off=0, height=6, width=10)),
            ((0, 0, 10, 10), Window(row_off=0, col_off=0, height=10, width=10)),
            ((-10, -10, 20, 20), Window(row_off=0, col_off=0, height=10, width=10)),
            ((-10, -10, 10, 5), Window(row_off=4, col_off=0, height=6, width=10)),
            ((-10, 5, 5, 20), Window(col_off=0, row_off=0, width=6, height=6)),
        ],
    )
    def test_create_window(self, bounds, expected_window):
        with create_rasterio_dataset(data=np.zeros((1, 10, 10))) as dataset:
            window = RasterioRasterWindow._create_window(dataset=dataset, bounds=bounds)
        assert window == expected_window

    @pytest.mark.parametrize(
        "bounds, resolution, expected_shape, expected_pixel_value, expected_pixel_xy",
        [
            ((0, 0, 4, 4), None, (4, 4), 0.0, (0.5, 3.5)),
            ((0, 0, 4, 4), 2.0, (2, 2), 0.5, (1.0, 3.0)),
            ((0, 0, 4, 4), 4, (1, 1), 1.5, (2.0, 2.0)),
            ((0, 0, 4, 4), 1 + 1 / 3, (3, 3), 0.25, (2 / 3, 4 - 2 / 3)),
            ((2, 0, 4, 2), None, (3, 3), 1.0, (1.5, 2.5)),
            ((2, 0, 4, 2), 3, (1, 1), 2.0, (2.5, 1.5)),
            ((2, 0, 4, 2), 1.5, (2, 2), 1 + 1 / 3, (1.75, 2.25)),
            ((0, 0, 1.9, 1.9), 3, (1, 1), 2.0, (1.5, 1.5)),
            ((-10, -10, 1.9, 1.9), 3, (1, 1), 2.0, (1.5, 1.5)),
            ((-10, -10, 10, 10), None, (4, 4), 0.0, (0.5, 3.5)),
        ],
    )
    def test_downscale(
        self,
        bounds,
        resolution,
        expected_shape,
        expected_pixel_value,
        expected_pixel_xy,
    ):
        grid_values = np.array(
            [[[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2], [3, 3, 3, 3]]],
            dtype=dtype("float64"),
        )

        with create_raster_file(data=grid_values) as raster_file:
            window = RasterioRasterWindow(
                raster_file.name,
                src_bounds=bounds,
                dst_resolution=resolution,
            )

        assert (window.height, window.width) == expected_shape
        assert window.grid_values[0, 0] == pytest.approx(expected_pixel_value)
        assert window.get_xy_from_pixel(0, 0) == expected_pixel_xy
