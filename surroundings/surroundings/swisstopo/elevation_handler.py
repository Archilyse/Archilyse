from surroundings.base_elevation_handler import TriangleElevationHandler
from surroundings.constants import BOUNDING_BOX_EXTENSION_ALTI
from surroundings.raster_window_provider import RasterWindowProvider
from surroundings.swisstopo.raster_window_provider import (
    SwissTopoGroundsRasterWindowProvider,
)


class SwisstopoElevationHandler(TriangleElevationHandler):
    BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_ALTI

    @property
    def raster_window_provider(self) -> RasterWindowProvider:
        return SwissTopoGroundsRasterWindowProvider(
            region=self.region, bounds=self.bounds
        )
