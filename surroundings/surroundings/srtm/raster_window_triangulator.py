from surroundings.raster_window_triangulator import RasterWindowTriangulator
from surroundings.srtm.raster_window_provider import SRTMRasterWindowProvider


class SRTMRasterWindowTriangulator(RasterWindowTriangulator):
    @property
    def raster_window_provider(self) -> SRTMRasterWindowProvider:
        return SRTMRasterWindowProvider(
            region=self.region, bounds=self.bounding_box.bounds
        )
