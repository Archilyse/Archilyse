from pathlib import Path
from unittest.mock import PropertyMock

import pytest

from common_utils.constants import GOOGLE_CLOUD_OSM, REGION
from surroundings.constants import OSM_DIR, OSM_REGIONS_FILENAMES
from surroundings.v2.osm.geometry_provider import OSMGeometryProvider
from tests.unittests.test_surroundings.test_v2.test_geometry_provider import (
    _TestShapeFileGeometryProvider,
)


class _TestOSMGeometryProvider(_TestShapeFileGeometryProvider):
    instance_cls = OSMGeometryProvider

    def test_dataset_crs(self):
        assert self.get_instance().dataset_crs == REGION.LAT_LON

    @pytest.mark.parametrize("region, expected_path", OSM_REGIONS_FILENAMES.items())
    def test_osm_directory(self, region, expected_path):
        assert self.get_instance(region=region).osm_directory == expected_path

    def test_get_source_filenames(self, mocked_gcp_download, mocker):
        # Given
        from surroundings.v2.osm import geometry_provider

        fake_template = "Fake Template"
        fake_osm_directory = Path("Fake Dir")

        mocker.patch.object(
            self.instance_cls,
            "file_templates",
            PropertyMock(return_value=[fake_template]),
        )
        mocker.patch.object(
            self.instance_cls,
            "osm_directory",
            PropertyMock(return_value=fake_osm_directory),
        )
        spy_download_shapefile_if_not_exists = mocker.spy(
            geometry_provider, "download_shapefile_if_not_exists"
        )

        geometry_provider = self.get_instance()

        # When
        source_filenames = geometry_provider.get_source_filenames()

        # Then
        assert source_filenames == [
            OSM_DIR.joinpath(
                fake_osm_directory.joinpath(fake_template).with_suffix(".shp")
            )
        ]
        spy_download_shapefile_if_not_exists.assert_called_once_with(
            local=OSM_DIR.joinpath(fake_osm_directory).joinpath(fake_template),
            remote=GOOGLE_CLOUD_OSM.joinpath(fake_osm_directory).joinpath(
                fake_template
            ),
        )
