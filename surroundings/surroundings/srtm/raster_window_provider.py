from pathlib import Path

from shapely.geometry import Polygon

from common_utils.constants import REGION
from surroundings.raster_window_provider import RasterWindowProvider


class SRTMRasterWindowProvider(RasterWindowProvider):
    @property
    def dataset_crs(self):
        return REGION.LAT_LON

    @property
    def src_resolution(self):
        """
        # NOTE pixel size was obtained as below:
        import rasterio
        with rasterio.open(path_to_any_srtm_tile) as dataset:
            print(dataset.transform.a)
        """
        return 0.0002777777777778146

    def get_raster_filenames(self, bounding_box: Polygon) -> list[Path]:
        from surroundings.srtm import SrtmFilesHandler

        return SrtmFilesHandler.get_srtm_files(bounding_box=bounding_box)
