from typing import List

from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle

from brooks.visualization.polygon_patch import PolygonPatch


class DimensionLinePatch(Rectangle):
    pass


class CustomPatchCollection(PatchCollection):
    _patches: List[DimensionLinePatch] = []

    def get_patches(self):
        return self._patches


class SeparatorPatch(PolygonPatch):
    pass


class RailingPatch(PolygonPatch):
    pass
