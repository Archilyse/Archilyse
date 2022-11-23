from functools import cached_property, lru_cache
from itertools import product
from typing import Iterator

from rasterio.windows import Window
from shapely.geometry import Polygon, box

from common_utils.constants import SurroundingType
from surroundings.constants import UNMountainClass
from surroundings.raster_window import RasterWindow
from surroundings.raster_window_utils import get_triangle, get_window_for_triangulation
from surroundings.triangle_remover import TriangleRemover
from surroundings.utils import (
    TRIANGLE_OFFSETS,
    Bounds,
    SurrTrianglesType,
    TriangleOffsets,
)
from surroundings.v2.grounds.un_mountains_classifier import UNMountainsClassifier


class UNMountainsHandler:
    def __init__(self, raster_window: RasterWindow, exclusion_bounds: Bounds):
        self.raster_window = raster_window
        self.exclusion_bounds = exclusion_bounds

    @cached_property
    def _exclusion_footprint(self) -> Polygon:
        return box(*self.exclusion_bounds)

    @cached_property
    def _mountains_classifier(self) -> UNMountainsClassifier:
        return UNMountainsClassifier(
            grid_values=self.raster_window.grid_values,
            resolution_in_meters=self.raster_window.transform.a,
        )

    # NOTE the size is 1 row of the downscaled raster
    @lru_cache(maxsize=480)
    def _classify(self, row: int, col: int) -> int:
        return self._mountains_classifier.classify(position=(row, col)).value

    def _get_surrounding_type(
        self, row: int, col: int, triangle_offsets: TriangleOffsets
    ) -> SurroundingType:
        mountains_cls = UNMountainClass(
            min(
                self._classify(row=row + row_off, col=col + col_off)
                for row_off, col_off in triangle_offsets
            )
        )
        if mountains_cls == UNMountainClass.GROUNDS:
            return SurroundingType.GROUNDS
        return SurroundingType[f"MOUNTAINS_{mountains_cls.name}"]

    @cached_property
    def _exclusion_window(self) -> Window:
        return get_window_for_triangulation(
            transform=self.raster_window.transform, bounds=self.exclusion_bounds
        )

    def _outside_of_exclusion_area(self, row: int, col: int) -> bool:
        window = self._exclusion_window
        return not (
            window.row_off <= row <= window.row_off + window.height - 2
            and window.col_off <= col <= window.col_off + window.width - 2
        )

    def _row_or_col_touches_borders_of_exclusion_area(self, row: int, col: int) -> bool:
        window = self._exclusion_window
        return (
            row == window.row_off
            or row == window.row_off + window.height - 2
            or col == window.col_off
            or col == window.col_off + window.width - 2
        )

    def get_triangles(self) -> Iterator[SurrTrianglesType]:
        for row, col, triangle_offsets in product(
            range(self.raster_window.height - 1),
            range(self.raster_window.width - 1),
            TRIANGLE_OFFSETS,
        ):
            surrounding_type = self._get_surrounding_type(
                row=row, col=col, triangle_offsets=triangle_offsets
            )
            triangle = get_triangle(
                raster_window=self.raster_window,
                row=row,
                col=col,
                triangle_offsets=triangle_offsets,
            )
            if self._outside_of_exclusion_area(row=row, col=col):
                yield surrounding_type, triangle
            elif self._row_or_col_touches_borders_of_exclusion_area(row=row, col=col):
                for triangle_part in TriangleRemover.triangle_difference(
                    triangle=triangle,
                    footprint=self._exclusion_footprint,
                ):
                    yield surrounding_type, triangle_part
