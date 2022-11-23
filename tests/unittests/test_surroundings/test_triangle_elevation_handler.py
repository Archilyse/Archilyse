from abc import ABC
from typing import Callable, ContextManager, Dict, Tuple, Type

import pytest
from shapely.geometry import Point

from common_utils.constants import REGION
from surroundings.base_elevation_handler import TriangleElevationHandler
from surroundings.srtm import SRTMElevationHandler
from surroundings.swisstopo import SwisstopoElevationHandler
from tests.constants import ELEVATION_BY_POINT
from tests.utils import random_simulation_version


class TriangleElevationHandlerTest(ABC):
    RESAMPLING_ERROR = 0

    @pytest.fixture
    def tiles_and_coords(self) -> Dict[str, Tuple[float, float, float]]:
        """A tuple of connected tiles and locations, e.g.:
        (
            ("n46_e007_1arc_v3", (2604710.31, 1149856.04, 2361.09)),
            ("n46_e008_1arc_v3", (2681473.38, 1150404.76, 1473.09)),
        )
        """
        raise NotImplementedError

    @pytest.fixture
    def elevation_handler_cls(self) -> Type[TriangleElevationHandler]:
        raise NotImplementedError

    @pytest.fixture
    def mocked_tiles(self) -> Callable[[str], ContextManager[str]]:
        raise NotImplementedError

    def test_get_elevation_single_tile(
        self, mocked_tiles, tiles_and_coords, elevation_handler_cls
    ):
        for tile, (x, y, expected_z) in tiles_and_coords:
            with mocked_tiles(tile):
                tile_centroid = Point(x, y)
                elevation = elevation_handler_cls(
                    region=REGION.CH,
                    location=tile_centroid,
                    bounding_box_extension=100,
                    simulation_version=random_simulation_version(),
                ).get_elevation(tile_centroid)
                assert elevation == pytest.approx(expected_z, abs=1e-2)

    def test_get_elevation_merging_multiple_tiles(
        self, mocked_tiles, tiles_and_coords, elevation_handler_cls
    ):
        xs = [c[0] for _, c in tiles_and_coords]
        ys = [c[1] for _, c in tiles_and_coords]
        tiles = set(t for t, _ in tiles_and_coords)
        tiles_merged_bounds = (
            min(xs) - 100,
            min(ys) - 100,
            max(xs) + 100,
            max(ys) + 100,
        )

        elevation_handler = elevation_handler_cls(
            region=REGION.CH,
            bounds=tiles_merged_bounds,
            simulation_version=random_simulation_version(),
        )

        with mocked_tiles(*tiles):
            for _, (x, y, expected_z) in tiles_and_coords:
                elevation = elevation_handler.get_elevation(Point(x, y))
                assert elevation == pytest.approx(
                    expected_z, abs=1e-2 + self.RESAMPLING_ERROR
                )


class TestSRTMElevationHandler(TriangleElevationHandlerTest):
    RESAMPLING_ERROR = 0.5

    @pytest.fixture
    def tiles_and_coords(self):
        return (
            ("n46_e007_1arc_v3", (2641942.677658631, 1204473.4454756852, 924.5489)),
            ("n46_e008_1arc_v3", (2643464.0545876776, 1204484.3202372536, 1058.1395)),
            ("n47_e007_1arc_v3", (2641927.0685918336, 1206696.8254845182, 1089.4025)),
            ("n47_e008_1arc_v3", (2643447.8783658296, 1206707.6961888347, 859.4071)),
        )

    @pytest.fixture
    def elevation_handler_cls(self):
        return SRTMElevationHandler

    @pytest.fixture
    def mocked_tiles(self, mocked_srtm_tiles):
        return mocked_srtm_tiles


class TestSwisstopoElevationHandler(TriangleElevationHandlerTest):
    @pytest.fixture
    def tiles_and_coords(self):
        return (
            ("swiss_1187_4", (2615625.0, 1185000.0, 908.7691)),
            ("swiss_1188_3", (2624375.0, 1185000.0, 926.4924)),
            ("swiss_1187_2", (2615625.0, 1191000.0, 826.5089)),
            ("swiss_1188_1", (2624375.0, 1191000.0, 946.8165)),
            *[
                ("swiss_1188_1", (x, y, elevation))
                for (x, y), elevation in ELEVATION_BY_POINT.items()
            ],
        )

    @pytest.fixture
    def elevation_handler_cls(self):
        return SwisstopoElevationHandler

    @pytest.fixture
    def mocked_tiles(self, mocked_swisstopo_esri_ascii_grid):
        return mocked_swisstopo_esri_ascii_grid
