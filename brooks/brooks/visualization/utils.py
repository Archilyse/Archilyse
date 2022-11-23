from enum import Enum
from typing import Union

from shapely.affinity import scale
from shapely.geometry import LinearRing, MultiPolygon, Point, Polygon

from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.exceptions import RectangleNotCalculatedException
from dufresne.linestring_add_width import add_width_to_linestring_improved
from simulations.rectangulator import DeterministicRectangulator


class RECTANGLE_SIDE(Enum):
    SHORT_SIDE = "SHORT_SIDE"
    LONG_SIDE = "LONG_SIDE"
    BOTH_SIDE = "BOTH_SIDE"


def shapely_ring_to_svg(path: LinearRing) -> str:
    return f"M {path.coords[0][0]},{path.coords[0][1]} {' '.join(f'L{x:.3f},{y:.3f}' for x, y in path.coords[1:-1])} Z"


def get_visual_center(footprint: Union[Polygon, MultiPolygon]) -> Point:
    if isinstance(footprint, MultiPolygon):
        return footprint.centroid
    try:
        return (
            DeterministicRectangulator(polygon=footprint)
            .get_biggest_rectangle()
            .centroid
        )
    except RectangleNotCalculatedException:
        return footprint.centroid


class ScaleRectangle:
    @classmethod
    def round(
        cls, rectangle: Polygon, applied_to: RECTANGLE_SIDE, ndigits: int = 2
    ) -> Polygon:
        long_centerline, short_centerline = get_center_line_from_rectangle(
            polygon=rectangle, only_longest=False
        )

        if (
            applied_to == RECTANGLE_SIDE.LONG_SIDE
            or applied_to == RECTANGLE_SIDE.BOTH_SIDE
        ):
            scale_factor = (
                round(long_centerline.length, ndigits=ndigits) - long_centerline.length
            ) / long_centerline.length + 1

            long_centerline = scale(
                geom=long_centerline,
                xfact=scale_factor,
                yfact=scale_factor,
                origin="center",
            )

        width = short_centerline.length

        if (
            applied_to == RECTANGLE_SIDE.SHORT_SIDE
            or applied_to == RECTANGLE_SIDE.BOTH_SIDE
        ):
            width = round(short_centerline.length, ndigits=ndigits)

        return add_width_to_linestring_improved(line=long_centerline, width=width)

    @classmethod
    def extend_sides(
        cls,
        rectangle: Polygon,
        applied_to: RECTANGLE_SIDE,
        extension_value: float = 0.001,
    ) -> Polygon:
        long_centerline, short_centerline = get_center_line_from_rectangle(
            polygon=rectangle, only_longest=False
        )
        scale_factor = extension_value / long_centerline.length + 1

        if (
            applied_to == RECTANGLE_SIDE.LONG_SIDE
            or applied_to == RECTANGLE_SIDE.BOTH_SIDE
        ):
            long_centerline = scale(
                geom=long_centerline,
                xfact=scale_factor,
                yfact=scale_factor,
                origin="center",
            )

        width = short_centerline.length

        if (
            applied_to == RECTANGLE_SIDE.SHORT_SIDE
            or applied_to == RECTANGLE_SIDE.BOTH_SIDE
        ):
            width += extension_value

        return add_width_to_linestring_improved(line=long_centerline, width=width)
