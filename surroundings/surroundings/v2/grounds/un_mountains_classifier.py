import math
from functools import cached_property

import numpy as np
from scipy.ndimage import minimum_filter

from surroundings.constants import UNMountainClass
from surroundings.utils import PixelPosition


class UNMountainsClassifier:
    RADIUS_IN_METERS = 7e3

    def __init__(self, grid_values: np.array, resolution_in_meters: float):
        self._resolution_in_meters = resolution_in_meters
        self._grid_values = grid_values

    def _get_filter_size(self) -> int:
        return (
            int(math.ceil(self.RADIUS_IN_METERS / self._resolution_in_meters) * 2) + 1
        )

    @cached_property
    def _grid_values_minimum_filtered(self) -> np.array:
        return minimum_filter(self._grid_values, self._get_filter_size())

    def _is_300m_elevated(self, position: PixelPosition) -> bool:
        elevation_range = (
            self._grid_values[position] - self._grid_values_minimum_filtered[position]
        )
        return elevation_range > 300

    def _get_slope(self, position: PixelPosition) -> float:
        """Returns the slope of the current pixel value and the 7km minimum"""
        distance = (self._get_filter_size() - 1) * self._resolution_in_meters / 2
        return (
            self._grid_values[position] - self._grid_values_minimum_filtered[position]
        ) / distance

    def classify(self, position: PixelPosition) -> UNMountainClass:
        """
        Returns mountain class according to UNEP-WCMC definition, Kapos et al. (2000).
        """
        height = self._grid_values[position]
        if height > 4500:
            return UNMountainClass.CLASS_1
        elif height > 3500:
            return UNMountainClass.CLASS_2
        elif height > 2500:
            return UNMountainClass.CLASS_3
        elif 1500 < height <= 2500 and self._get_slope(position) >= 0.02:
            return UNMountainClass.CLASS_4
        elif 1000 < height <= 1500 and (
            self._is_300m_elevated(position=position)
            or self._get_slope(position) >= 0.05
        ):
            return UNMountainClass.CLASS_5
        elif 300 < height <= 1000 and self._is_300m_elevated(position=position):
            return UNMountainClass.CLASS_6
        return UNMountainClass.GROUNDS
