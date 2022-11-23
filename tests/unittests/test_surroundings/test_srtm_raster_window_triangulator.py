import pytest
from shapely.geometry import box

from common_utils.constants import REGION


class TestSRTMRasterWindowTriangulator:
    @pytest.mark.parametrize("bounds", [(0, 0, 1, 1), (1, 1, 2, 2)])
    @pytest.mark.parametrize("region", [REGION.CH, REGION.LAT_LON])
    def test_raster_window_provider(self, mocker, bounds, region):
        import surroundings.srtm.raster_window_triangulator as rwt

        spy_raster_window_provider = mocker.spy(rwt, "SRTMRasterWindowProvider")
        triangulator = rwt.SRTMRasterWindowTriangulator(
            bounding_box=box(*bounds),
            region=region,
        )

        # When
        raster_window_provider = triangulator.raster_window_provider

        # Then
        spy_raster_window_provider.assert_called_once_with(bounds=bounds, region=region)
        assert raster_window_provider is spy_raster_window_provider.spy_return
