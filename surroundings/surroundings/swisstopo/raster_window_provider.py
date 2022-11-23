from abc import ABC
from pathlib import Path

from shapely.geometry import Polygon

from common_utils.constants import (
    REGION,
    SWISSTOPO_REQUIRED_FILES_ALTI,
    SWISSTOPO_REQUIRED_FILES_MOUNTAINS,
)
from surroundings.raster_window_provider import RasterWindowProvider
from surroundings.utils import download_swisstopo_if_not_exists


class SwissTopoRasterWindowProvider(RasterWindowProvider, ABC):
    @classmethod
    def file_templates(cls):
        raise NotImplementedError

    @property
    def dataset_crs(self):
        return REGION.CH

    def get_raster_filenames(self, bounding_box: Polygon) -> list[Path]:
        return download_swisstopo_if_not_exists(
            templates=self.file_templates(), bounding_box=bounding_box
        )


class SwissTopoMountainsRasterWindowProvider(SwissTopoRasterWindowProvider):
    @property
    def src_resolution(self):
        return 50.0

    @classmethod
    def file_templates(cls):
        return SWISSTOPO_REQUIRED_FILES_MOUNTAINS


class SwissTopoGroundsRasterWindowProvider(SwissTopoRasterWindowProvider):
    @property
    def src_resolution(self):
        return 10.0

    @classmethod
    def file_templates(cls):
        return SWISSTOPO_REQUIRED_FILES_ALTI
