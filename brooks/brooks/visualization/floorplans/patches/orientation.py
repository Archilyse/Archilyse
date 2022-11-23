from typing import Tuple

from matplotlib.patches import Circle, PathPatch
from matplotlib.path import Path
from numpy import array
from shapely.affinity import rotate, translate
from shapely.geometry import LineString

from .collection import CustomPatchCollection
from .feature import Triangle


class NorthIndicatorPatch(Triangle):
    def __init__(
        self,
        xy: array,
        angle_north: float,
        arrow_length: float,
        side_length: float = 1,
        **kwargs
    ):
        super().__init__(
            xy,
            angle=angle_north,
            arrow_length=arrow_length,
            side_length=side_length,
            **kwargs
        )


class OrientationCirclePatch(Circle):
    def __init__(self, xy, arrow_length, **kwargs):
        super().__init__(xy, arrow_length, **kwargs)


class OrientationLinePatch(PathPatch):
    def __init__(
        self, xy, arrow_length: float, angle_north: float, vert=False, **kwargs
    ):
        dx, dy = 0.0, 0.0
        if vert:
            dy = arrow_length
        else:
            dx = arrow_length

        x0, y0 = xy[0] - dx, xy[1] - dy
        x1, y1 = xy[0] + dx, xy[1] + dy
        line = LineString([(x0, y0), (x1, y1)])
        rotated_line = rotate(geom=line, angle=angle_north, origin=xy)
        path = (
            (rotated_line.coords[0], Path.MOVETO),
            (rotated_line.coords[1], Path.LINETO),
        )

        vertices, codes = zip(*path)
        super().__init__(Path(vertices, codes, closed=False), **kwargs)


class NorthSecondLinePatch(PathPatch):
    def __init__(self, xy: Tuple, arrow_length: float, angle_north: float, **kwargs):
        shift = arrow_length * 0.05

        x0, y0 = xy[0], xy[1]
        x1, y1 = xy[0] + arrow_length, xy[1]

        line = LineString([(x0, y0), (x1, y1)])
        translated_line = translate(geom=line, yoff=shift)
        rotated_line = rotate(geom=translated_line, angle=angle_north, origin=xy)
        path = (
            (rotated_line.coords[0], Path.MOVETO),
            (rotated_line.coords[1], Path.LINETO),
        )

        vertices, codes = zip(*path)
        super().__init__(Path(vertices, codes, closed=False), **kwargs)


class OrientationPatchCollection(CustomPatchCollection):

    COMPASS_CENTERPOINT_OFFSET = 0.1

    def __init__(self, xy, arrow_length, angle_north, **kwargs):
        self._patches = [
            OrientationCirclePatch(
                xy, arrow_length, fill=False, linewidth=0.3, **kwargs
            ),
            OrientationLinePatch(
                xy, arrow_length, angle_north=angle_north, linewidth=0.3, **kwargs
            ),
            OrientationLinePatch(
                xy,
                arrow_length,
                angle_north=angle_north,
                vert=True,
                linewidth=0.3,
                **kwargs
            ),
            NorthSecondLinePatch(
                xy=xy, arrow_length=arrow_length, angle_north=angle_north, linewidth=0.3
            ),
        ]

        super().__init__(self._patches)

    @staticmethod
    def offset_compass_origin(
        origin: Tuple[float, float], by_y: float
    ) -> Tuple[float, float]:
        x, y = origin
        return x, y - by_y
