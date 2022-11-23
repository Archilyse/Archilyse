from unittest.mock import PropertyMock

import pytest
from shapely.geometry import box

from common_utils.constants import REGION, SWISSTOPO_DIR
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_provider import (
    _TestShapeFileGeometryProvider,
)


class _TestSwissTopoShapeFileGeometryProvider(_TestShapeFileGeometryProvider):
    instance_cls = SwissTopoShapeFileGeometryProvider

    def test_dataset_crs(self):
        assert self.get_instance().dataset_crs == REGION.CH

    @pytest.fixture
    def fake_file_templates(self, mocker):
        fake_template = "Fake Template"
        return mocker.patch.object(
            self.instance_cls,
            "file_templates",
            PropertyMock(return_value=[fake_template]),
        )

    def test_get_source_filenames_calls_download_swisstopo_if_not_exists(
        self, mocker, mocked_gcp_download, fake_file_templates
    ):
        # Given
        from surroundings.v2.swisstopo import geometry_provider

        spy_download_swisstopo_if_not_exists = mocker.spy(
            geometry_provider, "download_swisstopo_if_not_exists"
        )
        bounding_box = box(2682905.0, 1243137.5, 2683905.0, 1244137.5)

        # When
        self.get_instance(
            bounding_box=bounding_box,
            region=REGION.CH,
        ).get_source_filenames()

        # Then
        spy_download_swisstopo_if_not_exists.assert_called_once_with(
            bounding_box=bounding_box,
            templates=[
                f"{fake_template}.{extension}"
                for fake_template in fake_file_templates.return_value
                for extension in ("shp", "shx", "prj", "dbf")
            ],
        )

    def test_get_source_filenames(self, mocked_gcp_download, fake_file_templates):
        bounding_box = box(2682905.0, 1243137.5, 2683905.0, 1244137.5)
        assert self.get_instance(
            region=REGION.CH, bounding_box=bounding_box
        ).get_source_filenames() == [
            SWISSTOPO_DIR.joinpath(fake_template).with_suffix(".shp")
            for fake_template in fake_file_templates.return_value
        ]
