import numpy as np
import pytest
from affine import Affine
from shapely.affinity import translate
from shapely.geometry import box

from common_utils.constants import REGION
from common_utils.exceptions import RasterNotIntersectingException, SurroundingException
from surroundings.raster_window_provider import (
    RasterWindowProvider,
    get_projected_raster_centroid_bounds,
)
from tests.surroundings_utils import create_raster_file


class _TestRasterWindowProvider:
    instance_cls = RasterWindowProvider

    @pytest.fixture
    def fake_projection(self, mocker):
        import surroundings.raster_window_provider

        def fake_project_geometry(geometry, crs_from, crs_to):
            if crs_from == crs_to:
                return geometry
            elif crs_from == REGION.LAT_LON:
                return translate(geometry, xoff=2, yoff=2)
            elif crs_to == REGION.LAT_LON:
                return translate(geometry, xoff=-2, yoff=-2)

        mocker.patch.object(
            surroundings.raster_window_provider,
            "project_geometry",
            side_effect=fake_project_geometry,
        )

        def fake_project_xy(xs, ys, crs_from, crs_to):
            if crs_from == crs_to:
                return xs, ys
            elif crs_from == REGION.LAT_LON:
                return (np.array(xs) + 2).tolist(), (np.array(ys) + 2).tolist()
            elif crs_to == REGION.LAT_LON:
                return (np.array(xs) - 2).tolist(), (np.array(ys) - 2).tolist()

        mocker.patch.object(
            surroundings.raster_window_provider,
            "project_xy",
            side_effect=fake_project_xy,
        )

    def get_instance(self, bounds=None, region=None, resolution=None):
        return self.instance_cls(bounds=bounds, region=region, resolution=resolution)

    def test_get_filenames_buffered_bounding_box(self, mocker):
        mocker.patch.object(
            self.instance_cls, "src_resolution", mocker.PropertyMock(return_value=1.0)
        )
        mocker.patch.object(
            self.instance_cls, "_get_src_bounds", return_value=(0.0, 0.0, 1.0, 1.0)
        )
        mocked_get_raster_filenames = mocker.patch.object(
            self.instance_cls, "get_raster_filenames"
        )

        filenames = self.get_instance()._get_filenames_buffered_bbox()

        mocked_get_raster_filenames.called_once_with(
            bounding_box=box(-0.5, -0.5, 1.5, 1.5)
        )
        assert filenames is mocked_get_raster_filenames.return_value

    @pytest.mark.parametrize("bounds", [(0.0, 0.0, 1.0, 1.0)])
    @pytest.mark.parametrize(
        "dataset_crs, region, resolution, expected_bbox",
        [
            (REGION.CH, REGION.CH, None, (0.0, 0.0, 1.0, 1.0)),
            (REGION.CH, REGION.CH, 0.5, (-0.25, -0.25, 1.25, 1.25)),
            (
                REGION.LAT_LON,
                REGION.CH,
                None,
                (0.0 - 2.0, 0.0 - 2.0, 1.0 - 2.0, 1.0 - 2.0),
            ),
            (
                REGION.LAT_LON,
                REGION.CH,
                0.5,
                (-0.25 - 2.0, -0.25 - 2.0, 1.25 - 2.0, 1.25 - 2.0),
            ),
            (REGION.CH, REGION.CH, 0.3, (-0.15, -0.35, 1.35, 1.15)),
            (
                REGION.LAT_LON,
                REGION.CH,
                0.3,
                (-0.15 - 2.0, -0.35 - 2.0, 1.35 - 2.0, 1.15 - 2.0),
            ),
        ],
    )
    def test_get_src_bounds_fake_projection(
        self,
        mocker,
        region,
        dataset_crs,
        bounds,
        resolution,
        expected_bbox,
        fake_projection,
    ):
        mocker.patch.object(
            self.instance_cls,
            "dataset_crs",
            mocker.PropertyMock(return_value=dataset_crs),
        )
        mocker.patch.object(
            self.instance_cls, "src_resolution", mocker.PropertyMock(return_value=0.1)
        )

        provider = self.get_instance(
            region=region, bounds=bounds, resolution=resolution
        )

        assert provider._get_src_bounds() == pytest.approx(expected_bbox)

    def test_get_src_bounds(self, mocker):
        mocker.patch.object(
            self.instance_cls,
            "dataset_crs",
            mocker.PropertyMock(return_value=REGION.LAT_LON),
        )
        src_bounds = self.get_instance(
            region=REGION.CH,
            bounds=(
                2623394.594835667 - 50000,
                1128957.0944898939 - 50000,
                2623394.594835667 + 50000,
                1128957.0944898939 + 50000,
            ),
            resolution=300.0,
        )._get_src_bounds()

        assert src_bounds == (
            7.088426948674379,
            45.85510119664875,
            8.403885742451369,
            46.763144766305096,
        )

    @pytest.mark.parametrize(
        "region, bounds, resolution, expected_grid_values, expected_xy_off",
        [
            (
                # same scale + projection
                REGION.CH,
                (1.0 + 2.0, 1.0 + 2.0, 3.0 + 2.0, 3.0 + 2.0),
                None,
                # NOTE: Projection requires resampling
                # therefore the grid values are different to the input
                # (even though in this test source and destination data have the same resolution)
                np.array(
                    [
                        [1.0, 1.5, 2.0],
                        [0.5, 1.0, 2.5],
                        [0.0, 1.5, 3.0],
                    ]
                ),
                (0.5 + 2.0, 3.5 + 2.0),
            ),
            (
                # same scale + no projection
                REGION.LAT_LON,
                (1.0, 1.0, 3.0, 3.0),
                None,
                np.array(
                    [
                        [1.0, 1.0, 2.0, 2.0],
                        [1.0, 1.0, 2.0, 2.0],
                        [0.0, 0.0, 3.0, 3.0],
                        [0.0, 0.0, 3.0, 3.0],
                    ]
                ),
                (0.0, 4.0),
            ),
            (
                # downscaled + no projection
                REGION.LAT_LON,
                (1.0, 1.0, 3.0, 3.0),
                2.0,
                np.array([[1.0, 2.0], [0.0, 3.0]]),
                (0.0, 4.0),
            ),
            (
                # downscaled + projection
                REGION.CH,
                (1.0 + 2.0, 1.0 + 2.0, 3.0 + 2.0, 3.0 + 2.0),
                2.0,
                np.array([[1.0, 2.0], [0.0, 3.0]]),
                (0.0 + 2.0, 4.0 + 2.0),
            ),
        ],
    )
    def test_get_raster_window(
        self,
        region,
        bounds,
        resolution,
        expected_grid_values,
        expected_xy_off,
        fake_projection,
        mocker,
    ):
        dataset_crs = REGION.LAT_LON
        src_resolution = 1.0

        mocker.patch.object(
            self.instance_cls,
            "dataset_crs",
            mocker.PropertyMock(return_value=dataset_crs),
        )
        mocker.patch.object(
            self.instance_cls,
            "src_resolution",
            mocker.PropertyMock(return_value=src_resolution),
        )

        src_data = np.array(
            [
                [
                    [1.0, 1.0, 2.0, 2.0],
                    [1.0, 1.0, 2.0, 2.0],
                    [0.0, 0.0, 3.0, 3.0],
                    [0.0, 0.0, 3.0, 3.0],
                ]
            ]
        )
        with create_raster_file(data=src_data) as raster_file:
            mocker.patch.object(
                self.instance_cls,
                "_get_filenames_buffered_bbox",
                return_value=[raster_file.name],
            )
            raster_window = self.get_instance(
                region=region,
                bounds=bounds,
                resolution=resolution,
            ).get_raster_window()

        expected_res = resolution or src_resolution
        assert np.array_equal(raster_window.grid_values, expected_grid_values)
        assert raster_window.transform == Affine.translation(
            *expected_xy_off
        ) * Affine.scale(expected_res, -expected_res)

    def test_get_raster_window_raises_surrounding_exception(self, mocker):
        import surroundings.raster_window_provider as rwp

        mocker.patch.object(
            rwp, "RasterioRasterWindow", side_effect=RasterNotIntersectingException()
        )
        mocker.patch.object(self.instance_cls, "get_raster_filenames")
        mocker.patch.object(self.instance_cls, "src_resolution", 1.0)
        mocker.patch.object(
            self.instance_cls,
            "dataset_crs",
            mocker.PropertyMock(return_value=REGION.LAT_LON),
        )

        with pytest.raises(
            SurroundingException,
            match="Couldn't find any raster file intersecting with bounding box: .*",
        ):
            self.get_instance(
                bounds=(0.0, 0.0, 1.0, 1.0), region=REGION.LAT_LON
            ).get_raster_window()


def test_project_raster_bounds():
    src_height, src_width = 335, 335
    src_transform = Affine.translation(
        2573244.594835667, 1179107.0944898939
    ) * Affine.scale(300.0, -300.0)
    projected_bounds = get_projected_raster_centroid_bounds(
        src_transform=src_transform,
        src_shape=(src_height, src_width),
        src_crs=REGION.CH,
        dst_crs=REGION.LAT_LON,
    )
    assert projected_bounds == (
        7.090374129891955,
        45.85645052647216,
        8.401938561233793,
        46.761795436481684,
    )
