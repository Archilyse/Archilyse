import contextlib
from typing import ContextManager, Dict, Iterable, Optional, Tuple

import fiona
import numpy as np
from affine import Affine
from rasterio import DatasetReader, MemoryFile
from shapely.affinity import scale
from shapely.geometry import box, mapping
from shapely.geometry.base import BaseGeometry

from surroundings.raster_window import RasterWindow
from surroundings.utils import Bounds
from surroundings.v2.base import BaseElevationHandler


def get_transform(
    height: int, width: int | None = None, bounds: Bounds | None = None
) -> Affine:
    if bounds:
        x_min, y_min, x_max, y_max = bounds
        return Affine.translation(x_min, y_max) * Affine.scale(
            (x_max - x_min) / width,
            -(y_max - y_min) / height,
        )
    return Affine.translation(0, height) * Affine.scale(1, -1)


@contextlib.contextmanager
def create_raster_file(
    data: np.ndarray,
    bounds: Optional[Bounds] = None,
    crs: Optional[str] = None,
    nodata: float = None,
) -> ContextManager[MemoryFile]:

    count, height, width = data.shape
    transform = get_transform(height=height, width=width, bounds=bounds)

    with MemoryFile() as m:
        with m.open(
            count=count,
            height=height,
            width=width,
            dtype=data.dtype,
            crs=crs or "EPSG:4326",
            transform=transform,
            driver="GTiff",
            nodata=nodata,
        ) as dataset:
            dataset.write(data)
        yield m


@contextlib.contextmanager
def create_rasterio_dataset(*args, **kwargs) -> ContextManager[DatasetReader]:
    with create_raster_file(*args, **kwargs) as file, file.open() as dataset:
        yield dataset


@contextlib.contextmanager
def create_fiona_collection(
    schema: Dict, records: Iterable[Tuple[BaseGeometry, Dict]]
) -> ContextManager[fiona.io.MemoryFile]:
    with fiona.MemoryFile() as mem_file:
        with mem_file.open(driver="ESRI Shapefile", schema=schema) as collection:
            collection.writerecords(
                {"geometry": mapping(geometry), "properties": properties}
                for geometry, properties in records
            )
        yield mem_file


def create_raster_window(
    data: np.ndarray, bounds: Optional[Bounds] = None
) -> RasterWindow:
    _, height, width = data.shape
    transform = get_transform(height=height, width=width, bounds=bounds)

    return RasterWindow(transform=transform, grid_values=data[0])


def flat_elevation_handler(
    bounds: Bounds, elevation: float = 0.0
) -> BaseElevationHandler:
    from surroundings.v2.grounds import ElevationHandler

    return ElevationHandler(
        raster_window=create_raster_window(
            data=np.full((1, 2, 2), elevation),
            bounds=scale(box(*bounds), xfact=2, yfact=2).bounds,
        )
    )
