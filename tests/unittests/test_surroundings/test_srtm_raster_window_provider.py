import pytest

from common_utils.constants import REGION
from surroundings.srtm.raster_window_provider import SRTMRasterWindowProvider
from tests.unittests.test_surroundings.test_raster_window_provider import (
    _TestRasterWindowProvider,
)


class TestSRTMRasterWindowProvider(_TestRasterWindowProvider):
    instance_cls = SRTMRasterWindowProvider

    def test_dataset_crs(self):
        assert self.get_instance().dataset_crs == REGION.LAT_LON

    @pytest.mark.parametrize(
        "lv95_bounds, expected_resolution",
        [
            ((2682957.5, 1246627.5, 2683957.5, 1247627.5), (20.98, 30.88)),
            ((2600000.0, 1200000.0, 2680000.0, 1240000.0), (21.07, 30.88)),
        ],
    )
    def test_get_default_dst_resolution_region_ch(
        self, lv95_bounds, expected_resolution
    ):
        x_res, y_res = self.get_instance(
            bounds=lv95_bounds, region=REGION.CH
        )._get_default_dst_resolution()
        assert (x_res, y_res) == pytest.approx(expected_resolution, abs=0.01)

    def test_get_raster_filenames(self, mocker):
        from surroundings.srtm import SrtmFilesHandler

        mocked_get_srtm_files = mocker.patch.object(SrtmFilesHandler, "get_srtm_files")
        fake_bounding_box = mocker.MagicMock()

        filenames = self.get_instance().get_raster_filenames(
            bounding_box=fake_bounding_box
        )

        mocked_get_srtm_files.assert_called_once_with(bounding_box=fake_bounding_box)
        assert filenames is mocked_get_srtm_files.return_value
