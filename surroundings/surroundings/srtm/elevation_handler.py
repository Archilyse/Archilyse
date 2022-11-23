from surroundings.base_elevation_handler import TriangleElevationHandler
from surroundings.constants import BOUNDING_BOX_EXTENSION_ALTI

from .raster_window_provider import SRTMRasterWindowProvider


class SRTMElevationHandler(TriangleElevationHandler):
    GROUND_OFFSET = 0.1
    BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_ALTI

    @property
    def raster_window_provider(self) -> SRTMRasterWindowProvider:
        return SRTMRasterWindowProvider(region=self.region, bounds=self.bounds)
