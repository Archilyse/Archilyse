from surroundings.raster_window_triangulator import RasterWindowTriangulator
from surroundings.swisstopo.raster_window_provider import (
    SwissTopoGroundsRasterWindowProvider,
    SwissTopoMountainsRasterWindowProvider,
)


class SwissTopoGroundsTriangulator(RasterWindowTriangulator):
    @property
    def raster_window_provider(self) -> SwissTopoGroundsRasterWindowProvider:
        return SwissTopoGroundsRasterWindowProvider(
            region=self.region, bounds=self.bounding_box.bounds
        )


class SwissTopoMountainsTriangulator(RasterWindowTriangulator):
    @property
    def raster_window_provider(self) -> SwissTopoMountainsRasterWindowProvider:
        return SwissTopoMountainsRasterWindowProvider(
            region=self.region, bounds=self.bounding_box.bounds
        )
