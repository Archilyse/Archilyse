from typing import List

from numpy import cos, deg2rad, sin

from brooks.visualization.floorplans.patches.collection import DimensionLinePatch

from .collection import CustomPatchCollection


class DimensionIndicatorPatchCollection(CustomPatchCollection):
    def __init__(
        self, xy, length, angle, steps: List[float], indicator_length, **kwargs
    ):
        angle_rad = deg2rad(angle)

        self._patches: List[DimensionLinePatch] = []

        x_positions = list(map(lambda z: z * length, steps))
        for xpos1, xpos2 in zip(x_positions[:-1], x_positions[1:]):
            step_position = (
                xy[0] + cos(angle_rad) * xpos1,
                xy[1] + sin(angle_rad) * xpos1,
            )
            step_patch = DimensionLinePatch(
                step_position, xpos2 - xpos1, 0.02, angle, **kwargs
            )
            self._patches.append(step_patch)

            step_start_position = (
                xy[0] + cos(angle_rad) * xpos1,
                xy[1] + sin(angle_rad) * xpos1,
            )
            orthogonal_indicator_start = DimensionLinePatch(
                step_start_position, indicator_length, 0.02, angle - 90, **kwargs
            )
            self._patches.append(orthogonal_indicator_start)

            step_end_position = (
                xy[0] + cos(angle_rad) * xpos2,
                xy[1] + sin(angle_rad) * xpos2,
            )
            orthogonal_indicator_end = DimensionLinePatch(
                step_end_position, indicator_length, 0.02, angle - 90, **kwargs
            )
            self._patches.append(orthogonal_indicator_end)

        super().__init__(self._patches)
