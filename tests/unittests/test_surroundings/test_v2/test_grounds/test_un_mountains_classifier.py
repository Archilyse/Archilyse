from itertools import product

import numpy as np
import pytest

from surroundings.constants import UNMountainClass
from surroundings.v2.grounds.un_mountains_classifier import UNMountainsClassifier


class TestUNMountainsClassifier:
    @pytest.mark.parametrize(
        "grid_values, expected_classes",
        [
            (
                [[301, 1001, 1501], [0, 0, 0], [2501, 3501, 4501]],
                [[6, 5, 4], [8, 8, 8], [3, 2, 1]],
            ),
            (
                [[0, 301, 100], [301, 301, 301], [100, 301, 0]],
                [[8, 6, 8], [6, 6, 6], [8, 6, 8]],
            ),
        ],
    )
    def test_classify(self, grid_values, expected_classes):
        mountains_classifier = UNMountainsClassifier(
            grid_values=np.array(grid_values), resolution_in_meters=7000
        )
        for row, col in product(
            range(len(expected_classes)), range(len(expected_classes))
        ):
            expected_class = expected_classes[row][col]
            assert mountains_classifier.classify((row, col)) == UNMountainClass(
                expected_class
            )

    @pytest.mark.parametrize(
        "grid_values, expected_minimum_filter",
        [
            (
                [[0, 1, 1], [1, 1, 1], [1, 1, 0]],
                [[0, 0, 1], [0, 0, 0], [1, 0, 0]],
            ),
            (
                [[1, 1, 0], [1, 1, 1], [0, 1, 1]],
                [[1, 0, 0], [0, 0, 0], [0, 0, 1]],
            ),
            (
                [[1, 1, 1], [1, 0, 1], [1, 1, 1]],
                [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
            ),
        ],
    )
    def test_grid_values_minimum(self, grid_values, expected_minimum_filter):
        grid_values_minimum_filtered = UNMountainsClassifier(
            grid_values=grid_values, resolution_in_meters=7e3
        )._grid_values_minimum_filtered
        assert grid_values_minimum_filtered.tolist() == expected_minimum_filter

    @pytest.mark.parametrize(
        "resolution_in_meters, expected_filter_size",
        [(7000, 3), (3500, 5), (1000, 15), (300, 49), (150, 95)],
    )
    def test_get_filter_size(self, resolution_in_meters, expected_filter_size, mocker):
        assert (
            UNMountainsClassifier(
                grid_values=mocker.ANY, resolution_in_meters=resolution_in_meters
            )._get_filter_size()
            == expected_filter_size
        )

    def test_is_300m_elevated(self):
        mountains_classifier = UNMountainsClassifier(
            grid_values=np.array([[301, 0, 0]]), resolution_in_meters=7000
        )
        assert mountains_classifier._is_300m_elevated((0, 0))
        assert not mountains_classifier._is_300m_elevated((0, 1))
        assert not mountains_classifier._is_300m_elevated((0, 2))

    @pytest.mark.parametrize(
        "elevation, resolution_in_meters, expected_slope",
        [
            (300, 7000, 300 / 7000),
            (3500, 7000, 0.5),
            (3500, 3500, 0.5),
            (300, 300, 300 / (24 * 300)),
        ],
    )
    def test_get_slope(self, elevation, resolution_in_meters, expected_slope):
        mountains_classifier = UNMountainsClassifier(
            grid_values=np.array([[elevation, 0, 0]]),
            resolution_in_meters=resolution_in_meters,
        )
        assert mountains_classifier._get_slope((0, 0)) == pytest.approx(expected_slope)
        assert mountains_classifier._get_slope((0, 1)) == 0.0
        assert mountains_classifier._get_slope((0, 2)) == 0.0
