import logging
from collections import defaultdict
from functools import cached_property
from itertools import product
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

import fiona
import numpy as np
import rasterio
from affine import Affine
from contexttimer import timer
from methodtools import lru_cache
from numpy import dtype
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, Polygon, box, shape

from common_utils.constants import (
    REGION,
    SIMULATION_VERSION,
    SWISSTOPO_REQUIRED_FILES_BUILDINGS,
)
from common_utils.logger import logger
from surroundings.swisstopo import SwisstopoElevationHandler
from surroundings.utils import (
    Triangle,
    download_swisstopo_if_not_exists,
    get_interpolated_height,
)

Bounds = Tuple[float, float, float, float]
PixelPosition = Tuple[int, int]


class GridHandler:
    def __init__(self, bounds: Bounds, resolution: float):
        self.resolution = resolution
        self.bounds = bounds
        self.height = int((bounds[3] - bounds[1]) / resolution)
        self.width = int((bounds[2] - bounds[0]) / resolution)

    def get_rows_and_cols(self, bounds: Bounds) -> Iterator[PixelPosition]:
        min_row = int((self.bounds[3] - bounds[3]) / self.resolution)
        max_row = int((self.bounds[3] - bounds[1]) / self.resolution)
        min_col = int((bounds[0] - self.bounds[0]) / self.resolution)
        max_col = int((bounds[2] - self.bounds[0]) / self.resolution)

        if not (
            min_col >= self.width or min_row >= self.height or max_col < 0 > max_row
        ):
            if max_col >= self.width:
                max_col = self.width - 1
            if max_row >= self.height:
                max_row = self.height - 1
            if min_col < 0:
                min_col = 0
            if min_row < 0:
                min_row = 0

            yield from product(range(min_row, max_row + 1), range(min_col, max_col + 1))

    @cached_property
    def transform(self) -> Affine:
        return Affine.translation(self.bounds[0], self.bounds[3]) * Affine.scale(
            self.resolution, -self.resolution
        )

    @lru_cache()
    def get_pixel_centroid(self, row: int, col: int) -> Point:
        x, y = self.transform * (col, row)
        return Point(x + self.resolution / 2, y - self.resolution / 2)


class BuildingRasterizationHandler:
    @staticmethod
    def _get_building_triangles(buildings: Iterator[Dict]) -> Iterator[Polygon]:
        multipolygons = (shape(entity["geometry"]) for entity in buildings)
        yield from (
            polygon
            for multipolygon in multipolygons
            for polygon in multipolygon.geoms
            if polygon.is_valid and polygon.area > 0
        )

    @classmethod
    @timer(logger=logger, level=logging.DEBUG)
    def rasterize_building_triangles(
        cls, buildings: Iterator[Dict], grid_handler: GridHandler
    ) -> Dict[PixelPosition, List[Triangle]]:
        triangles_by_raster_index = defaultdict(list)
        for triangle in cls._get_building_triangles(buildings=buildings):
            if rows_and_cols := tuple(
                grid_handler.get_rows_and_cols(bounds=triangle.bounds)
            ):
                triangle_coords = tuple(triangle.exterior.coords[:3])
                for row_col in rows_and_cols:
                    cell_centroid = grid_handler.get_pixel_centroid(*row_col)
                    if triangle.intersects(cell_centroid):
                        triangles_by_raster_index[row_col].append(triangle_coords)
        return triangles_by_raster_index


class BuildingVolumeHandler:
    def __init__(self, grid_handler: GridHandler):
        self.grid_handler = grid_handler
        self.pixel_area = self.grid_handler.resolution**2

    @cached_property
    def _elevation_handler(self):
        return SwisstopoElevationHandler(
            region=REGION.CH,
            bounds=box(*self.grid_handler.bounds)
            .buffer(10.0, join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.square)
            .bounds,
            simulation_version=SIMULATION_VERSION.PH_01_2021,
        )

    @cached_property
    def _rasterized_building_triangles(self) -> Dict[PixelPosition, List[Triangle]]:
        return BuildingRasterizationHandler.rasterize_building_triangles(
            buildings=get_buildings(self.grid_handler.bounds),
            grid_handler=self.grid_handler,
        )

    @staticmethod
    def _get_min_max_heights_from_building_triangles(
        x: float, y: float, triangles: List[Triangle]
    ) -> Tuple[float, float]:
        heights = tuple(
            get_interpolated_height(x=x, y=y, from_triangle=coords)
            for coords in triangles
        )
        return min(heights), max(heights)

    def _get_volume(self, row: int, col: int, subterranean: bool) -> float:
        building_triangles = self._rasterized_building_triangles.get((row, col))
        if building_triangles is None or len(building_triangles) <= 1:
            return 0.0

        cell_centroid = self.grid_handler.get_pixel_centroid(row, col)
        min_z, max_z = self._get_min_max_heights_from_building_triangles(
            x=cell_centroid.x, y=cell_centroid.y, triangles=building_triangles
        )
        if not (min_z < max_z):
            return 0.0

        ground_z = self._elevation_handler.get_elevation(point=cell_centroid)
        if subterranean:
            if min_z >= ground_z:
                return 0.0
            if max_z > ground_z:
                max_z = ground_z
        else:
            if max_z <= ground_z:
                return 0.0
            if min_z < ground_z:
                min_z = ground_z

        return self.pixel_area * (max_z - min_z)

    @timer(logger=logger, level=logging.DEBUG)
    def get_volumes_grid(self, subterranean: bool) -> np.array:
        return np.asarray(
            tuple(
                tuple(
                    self._get_volume(row, col, subterranean)
                    for col in range(self.grid_handler.width)
                )
                for row in range(self.grid_handler.height)
            ),
            dtype=dtype("float32"),
        )


@timer(logger=logger, level=logging.DEBUG)
def store_as_tif(filename: Path, transform: Affine, volumes_grid: np.array):
    height, width = volumes_grid.shape
    with rasterio.open(
        filename,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        compress="lzw",
        dtype=volumes_grid.dtype,
        crs="EPSG:2056",
        transform=transform,
    ) as new_dataset:
        new_dataset.write(volumes_grid, 1)


def get_buildings(bounds: Bounds) -> Iterator[Dict]:
    bounding_box = box(*bounds)
    for filename in download_swisstopo_if_not_exists(
        templates=SWISSTOPO_REQUIRED_FILES_BUILDINGS,
        bounding_box=bounding_box.buffer(
            10.0, join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.square
        ),
    ):
        if filename.suffix == ".shp":
            with fiona.open(filename) as shp_file:
                if bounding_box.intersects(box(*shp_file.bounds)):
                    yield from shp_file
