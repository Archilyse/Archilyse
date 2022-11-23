import numpy as np
from matplotlib.patches import PathPatch
from matplotlib.patches import Polygon as PolygonPatch
from matplotlib.path import Path
from shapely.geometry import Polygon

from brooks.util.geometry_ops import get_center_line_from_rectangle


class WindowCenterLinePatch(PathPatch):
    def __init__(self, rectangle: Polygon, line_distance=0.035, **kwargs):
        centerline = get_center_line_from_rectangle(
            polygon=rectangle, only_longest=True
        )[0]
        p1, p2 = [np.array(c) for c in centerline.coords]

        vec = p2 - p1
        normal = np.array((-vec[1], vec[0]))
        normal /= np.linalg.norm(normal, ord=2)

        path = (
            (p1 + line_distance / 2 * normal, Path.MOVETO),
            (p2 + line_distance / 2 * normal, Path.LINETO),
            (p1 - line_distance / 2 * normal, Path.MOVETO),
            (p2 - line_distance / 2 * normal, Path.LINETO),
        )

        vertices, codes = zip(*path)
        super().__init__(Path(vertices, codes, closed=False), **kwargs)


class WindowPatch(PolygonPatch):
    pass
