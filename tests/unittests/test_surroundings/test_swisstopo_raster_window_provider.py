from common_utils.constants import (
    REGION,
    SWISSTOPO_REQUIRED_FILES_ALTI,
    SWISSTOPO_REQUIRED_FILES_MOUNTAINS,
)
from surroundings.swisstopo.raster_window_provider import (
    SwissTopoGroundsRasterWindowProvider,
    SwissTopoMountainsRasterWindowProvider,
    SwissTopoRasterWindowProvider,
)
from tests.unittests.test_surroundings.test_raster_window_provider import (
    _TestRasterWindowProvider,
)


class _TestSwissTopoRasterWindowProvider(_TestRasterWindowProvider):
    instance_cls = SwissTopoRasterWindowProvider

    def test_dataset_crs(self):
        assert self.get_instance().dataset_crs == REGION.CH

    def test_get_raster_filenames(self, mocker):
        import surroundings.swisstopo.raster_window_provider as rwp

        mocked_download_swisstopo_if_not_exists = mocker.patch.object(
            rwp, "download_swisstopo_if_not_exists"
        )
        mocked_file_templates = mocker.patch.object(self.instance_cls, "file_templates")
        fake_bounding_box = mocker.MagicMock()

        filenames = self.get_instance().get_raster_filenames(
            bounding_box=fake_bounding_box
        )

        mocked_download_swisstopo_if_not_exists.assert_called_once_with(
            templates=mocked_file_templates.return_value, bounding_box=fake_bounding_box
        )
        assert filenames is mocked_download_swisstopo_if_not_exists.return_value


class TestSwissTopoGroundsRasterWindowProvider(_TestSwissTopoRasterWindowProvider):
    instance_cls = SwissTopoGroundsRasterWindowProvider

    def test_src_resolution(self):
        assert self.get_instance().src_resolution == 10.0

    def test_file_templates(self):
        assert self.instance_cls.file_templates() == SWISSTOPO_REQUIRED_FILES_ALTI


class TestSwissTopoMountainsRasterWindowProvider(_TestSwissTopoRasterWindowProvider):
    instance_cls = SwissTopoMountainsRasterWindowProvider

    def test_src_resolution(self):
        assert self.get_instance().src_resolution == 50.0

    def test_file_templates(self):
        assert self.instance_cls.file_templates() == SWISSTOPO_REQUIRED_FILES_MOUNTAINS
