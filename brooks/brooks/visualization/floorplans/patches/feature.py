from typing import Tuple

from matplotlib.patches import Patch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path
from numpy import array, asarray, cos, deg2rad, sin
from shapely.affinity import rotate
from shapely.geometry import LineString, Point

from brooks.models import SimFeature
from brooks.types import FeatureType
from brooks.visualization.constants import SANITARY_BUFFER, SANITARY_RADIUS
from common_utils.utils import pairwise

from .collection import CustomPatchCollection
from .utils import make_only_corners_path, make_rounded_path


class Triangle(Polygon):
    def __init__(
        self,
        xy: array,
        angle: float,
        arrow_length: float = 1.0,
        side_length: float = 1.0,
        **kwargs,
    ):
        angle_rad = deg2rad(angle)
        head = (
            xy[0] + arrow_length * cos(angle_rad),
            xy[1] + arrow_length * sin(angle_rad),
        )

        tail_left = (
            xy[0] - side_length * sin(angle_rad),
            xy[1] + side_length * cos(angle_rad),
        )

        tail_right = (
            xy[0] + side_length * sin(angle_rad),
            xy[1] - side_length * cos(angle_rad),
        )

        super().__init__([head, tail_left, tail_right, head], **kwargs)


class SingleSimpleLinePatch(PathPatch):
    def __init__(self, line: LineString, **kwargs):
        path = []
        for pair in pairwise(line.coords[:]):
            path.append((pair[0], Path.MOVETO))
            path.append((pair[1], Path.LINETO))

        vertices, codes = zip(*path)
        super().__init__(Path(vertices, codes, closed=False), **kwargs)


class StairArrowTailPatch(SingleSimpleLinePatch):
    """The tail is defined as a polyline from the centroid of the stairs - half of the length (stairs.dy)
    to the beginning of the head triangle"""

    def __init__(self, stair: SimFeature, **kwargs):
        centroid = stair.footprint.centroid
        tail = rotate(
            geom=Point(
                centroid.x,
                centroid.y - stair.dy,
            ),
            angle=stair.angle,
            origin=centroid,
        )
        triangle_bottom_point = get_stairs_triangle_bottom_point(stair=stair)
        line = LineString((tail, triangle_bottom_point))
        super().__init__(line=line, **kwargs)


def get_stairs_triangle_bottom_point(stair) -> Point:
    centroid = stair.footprint.centroid
    return rotate(
        geom=Point(
            centroid.x,
            centroid.y + 4 * stair.dy / 5,
        ),
        angle=stair.angle,
        origin=centroid,
    )


class StairArrowHeadPatch(Triangle):
    """
          ^
          .
          .
    ..............
    .            .
    .            .
    .            .
    . .dx. .     .
    .      .     .
    .      dy    .
    .      .     .
    ..............

    Definition of a stair Feature in new editor with 0 rotation angle.

    """

    def __init__(self, stair: SimFeature, **kwargs):
        triangle_bottom_point = get_stairs_triangle_bottom_point(stair=stair)
        triangle_width = stair.dx / 2
        triangle_height = stair.dy / 5
        super().__init__(
            asarray([triangle_bottom_point.x, triangle_bottom_point.y]),
            stair.angle + 90,
            triangle_height,
            triangle_width,
            **kwargs,
        )


class GenericFeaturePatch(Rectangle):
    def __init__(
        self,
        xy: Tuple[float, float],
        length: float,
        width: float,
        angle: float,
        feature_type: FeatureType,
        **kwargs,
    ):
        super().__init__(xy, length, width, angle, **kwargs)
        self.feature_type = feature_type


class GenericPolygonFeaturePatch(Polygon):
    def __init__(self, coords, feature_type: FeatureType, **kwargs):
        super().__init__(coords, **kwargs)
        self.feature_type = feature_type


class ScaledRoundedPatch(PathPatch):
    def __init__(self, patch: Patch, radius: float, buffer: float = 0, **kwargs):
        super().__init__(
            path=make_rounded_path(patch=patch, radius=radius, buffer=buffer), **kwargs
        )


class KitchenCornerPatch(PathPatch):
    def __init__(self, patch: Patch, radius: float = 0.15, **kwargs):
        super().__init__(
            path=make_only_corners_path(patch=patch, radius=radius), **kwargs
        )


class FeaturePatchCollection(CustomPatchCollection):
    def __init__(
        self,
        xy: Tuple[float, float],
        length: float,
        width: float,
        angle: float,
        feature_type: FeatureType,
        feature_footprint: Polygon,
        **kwargs,
    ):
        self.feature_type = feature_type
        self._patches = []

        generic_patch = GenericFeaturePatch(
            xy=xy,
            length=length,
            width=width,
            angle=angle,
            feature_type=feature_type,
            **kwargs,
        )
        if feature_type == FeatureType.KITCHEN:
            self._patches.append(KitchenCornerPatch(patch=generic_patch))
        elif feature_type == FeatureType.SHAFT:
            self._patches.append(ShaftFeaturePatch(feature_footprint.exterior.coords))
        else:
            self._patches.append(generic_patch)

        if feature_type in SANITARY_RADIUS.keys():
            self._patches.append(
                ScaledRoundedPatch(
                    patch=self._patches[0],
                    radius=SANITARY_RADIUS[feature_type],
                    buffer=SANITARY_BUFFER[feature_type],
                    **kwargs,
                )
            )

        super().__init__(self._patches)


class AreasPatch(Polygon):
    def __init__(self, coords, **kwargs):
        super().__init__(coords, **kwargs)


class AreasEdgesPatch(Polygon):
    def __init__(self, coords, **kwargs):
        super().__init__(coords, **kwargs)


class ShaftFeaturePatch(AreasPatch):
    pass
