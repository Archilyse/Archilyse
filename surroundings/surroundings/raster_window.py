from contextlib import contextmanager
from pathlib import Path
from typing import ContextManager, Tuple

import numpy as np
import rasterio
from affine import Affine
from rasterio import DatasetReader, MemoryFile
from rasterio.enums import Resampling
from rasterio.fill import fillnodata
from rasterio.merge import merge as dataset_merge
from rasterio.windows import Window

from common_utils.exceptions import (
    RasterNotIntersectingException,
    RasterWindowNoDataException,
)
from surroundings.raster_window_utils import (
    get_bounds,
    get_pixel,
    get_transform,
    get_window_for_triangulation,
    get_xy,
)
from surroundings.utils import Bounds, PixelPosition


class RasterWindow:
    def __init__(self, transform: Affine, grid_values: np.ndarray):
        self.transform = transform
        self.grid_values = grid_values

    @property
    def height(self) -> int:
        return self.grid_values.shape[0]

    @property
    def width(self) -> int:
        return self.grid_values.shape[1]

    def get_value_at_xy(self, x: float, y: float) -> float:
        row, col = get_pixel(self.transform, x, y)
        if not (0 <= row < self.height and 0 <= col < self.width):
            raise RasterNotIntersectingException(
                "Point is outside of the bounds of the raster window."
            )
        return float(self.grid_values[row, col])

    def get_pixel_from_xy(self, x: float, y: float) -> PixelPosition:
        return get_pixel(self.transform, x, y)

    def get_xy_from_pixel(self, row: int, col: int) -> Tuple[float, float]:
        return get_xy(self.transform, row, col)


class RasterioRasterWindow(RasterWindow):
    def __init__(
        self,
        *filenames: Path,
        src_bounds: Bounds,
        fill_nodata: bool = True,
        scale_factors: Tuple[float, float] | None = None,
        dst_resolution: float | None = None,
    ):
        with self._get_dataset(*filenames, bounds=src_bounds) as dataset:
            window: Window = self._create_window(dataset=dataset, bounds=src_bounds)

            dst_transform, dst_width, dst_height = self._get_transform(
                src_transform=dataset.transform,
                src_window=window,
                scale_factors=scale_factors,
                dst_resolution=dst_resolution,
            )
            grid_values = self._get_grid_values(
                dataset=dataset,
                window=window,
                out_shape=(dst_height, dst_width),
                fill_nodata=fill_nodata,
            )

            super(RasterioRasterWindow, self).__init__(
                transform=dst_transform, grid_values=grid_values
            )

    @classmethod
    @contextmanager
    def _get_merged_dataset(
        cls, filenames: Tuple[Path, ...], bounds: Bounds
    ) -> ContextManager[DatasetReader]:
        with rasterio.open(filenames[0]) as dataset:
            nodata = dataset.nodata
            transform = dataset.transform
            crs = dataset.crs

        window = get_window_for_triangulation(transform=transform, bounds=bounds)
        bounds = get_bounds(transform=transform, **window.todict())

        raster, transform = dataset_merge(datasets=filenames, bounds=bounds)
        count, height, width = raster.shape

        with MemoryFile() as m:
            with m.open(
                count=count,
                height=height,
                width=width,
                dtype=raster.dtype,
                transform=transform,
                driver="GTiff",
                nodata=nodata,
                crs=crs,
            ) as dataset:
                dataset.write(raster)
                del raster
                yield dataset

    @classmethod
    @contextmanager
    def _get_dataset(cls, *filenames: Path, bounds: Bounds):
        with (
            cls._get_merged_dataset(filenames, bounds=bounds)
            if len(filenames) > 1
            else rasterio.open(*filenames)
        ) as dataset:
            yield dataset

    @classmethod
    def _create_window(cls, dataset, bounds: Bounds) -> Window:
        window = get_window_for_triangulation(
            transform=dataset.transform, bounds=bounds
        ).crop(height=dataset.height, width=dataset.width)
        if window.height and window.width:
            return window
        raise RasterNotIntersectingException

    @staticmethod
    def _get_dst_shape(
        src_window: Window, scale_factors: Tuple[float, float] | None = None
    ):
        if scale_factors:
            x_scale, y_scale = scale_factors
            return int(src_window.height * y_scale), int(src_window.width * x_scale)
        return src_window.height, src_window.width

    @classmethod
    def _get_transform(
        cls,
        src_transform: Affine,
        src_window: Window,
        scale_factors: Tuple[float, float] | None = None,
        dst_resolution: float | None = None,
    ) -> Tuple[Affine, int, int]:
        if dst_resolution:
            dst_resolution = (dst_resolution, dst_resolution)
        return get_transform(
            bounds=get_bounds(transform=src_transform, **src_window.todict()),
            resolution=dst_resolution,
            shape=cls._get_dst_shape(
                src_window=src_window, scale_factors=scale_factors
            ),
        )

    @classmethod
    def _get_grid_values(
        cls,
        dataset: DatasetReader,
        window: Window,
        out_shape: Tuple[int, int],
        fill_nodata: bool,
    ) -> np.ndarray:
        raster_band = 1
        grid_values_incl_nodata: np.ndarray = dataset.read(
            raster_band,
            window=window,
            out_shape=out_shape,
            resampling=Resampling.average,
        )
        if fill_nodata:
            nodata_mask = dataset.read_masks(
                raster_band, window=window, out_shape=out_shape
            )
            if not np.any(nodata_mask):
                raise RasterWindowNoDataException(
                    "The file contains exclusively NODATA values."
                )
            return fillnodata(
                image=grid_values_incl_nodata,
                mask=nodata_mask,
                max_search_distance=sum(out_shape),
            )
        return grid_values_incl_nodata
