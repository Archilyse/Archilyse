from itertools import product
from random import random, seed

import pytest

from common_utils.exceptions import OutOfGridException


def test_lk25_conversion(mock_working_dir):
    seed(42)

    from surroundings.constants import LK25_TILE_HEIGHT, LK25_TILE_WIDTH
    from surroundings.utils import lk25_to_lv95, lv95_to_lk25

    expected = {
        1011: (1.29e6, 2.6725e6),
        1159: (1.206e6, 2.8125e6),
        1373: (1.074e6, 2.7075e6),
        1201: (1.170e6, 2.4975e6),
        1186: (1.182e6, 2.585e6),
    }

    for index, coords in expected.items():
        expected_north, expected_east = coords
        actual_north, actual_east = lk25_to_lv95(index)

        assert actual_east == expected_east
        assert actual_north == expected_north

        # now wiggle around a bit within the tile
        for _ in range(5):
            for _ in range(5):
                east = actual_east + LK25_TILE_WIDTH * random()
                north = actual_north + LK25_TILE_HEIGHT * random()

                assert lv95_to_lk25(north, east) == index


def test_lk25_subindex_conversion(mock_working_dir):
    from surroundings.utils import lv95_to_lk25, lv95_to_lk25_subindex

    # and some subindex testing
    expected = {
        1208: {
            11: (2622191.934, 1180505.0055),
            12: (2626564.4765, 1180577.2945),
            13: (2622155.606, 1177501.083),
            14: (2626365.6405, 1177474.778),
            21: (2630877.629, 1180500.0515),
            22: (2635351.9335, 1180305.464),
            23: (2631020.1295, 1177407.717),
            24: (2635305.567, 1177314.9005),
            31: (2622162.542, 1174494.7645),
            32: (2626644.5325, 1174573.72),
            33: (2622192.866, 1171499.3605),
            34: (2626565.8645, 1171483.752),
            41: (2630940.5155, 1174508.0155),
            42: (2635311.5855, 1174490.0795),
            43: (2630956.413, 1171486.401),
            44: (2635301.9085, 1171505.1415),
        }
    }

    for index, subindexes in expected.items():
        for subindex, value in subindexes.items():
            east, north = value

            assert lv95_to_lk25(north, east) == index
            assert lv95_to_lk25_subindex(north, east) == subindex

            #  also test with depth=1
            assert lv95_to_lk25_subindex(north, east, depth=1) == subindex // 10


@pytest.mark.parametrize("x, y", product([0, 10e6], [0, 10e6]))
def test_lk25_conversion_raises_out_of_grid_exception(x, y):
    from surroundings.utils import lv95_to_lk25_subindex

    with pytest.raises(OutOfGridException):
        lv95_to_lk25_subindex(north=y, east=x)
