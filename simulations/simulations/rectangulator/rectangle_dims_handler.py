from typing import NamedTuple, Tuple

import numpy as np
from shapely.geometry import LineString, Polygon

from dufresne.polygon import (
    get_polygon_from_pos_dim_angle,
    get_sides_as_lines_by_length,
)


class PolDims(NamedTuple):
    centroid_x: float
    centroid_y: float
    width: float
    height: float
    angle: float


class RectangleDimsHandler:
    @staticmethod
    def _azimuth(point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """azimuth between 2 points (interval 0 - 180)"""
        angle = np.arctan2(point2[0] - point1[0], point2[1] - point1[1])
        return np.degrees(angle) if angle > 0 else np.degrees(angle) + 180

    @classmethod
    def _get_angle(cls, pol: Polygon) -> float:
        """azimuth of minimum_rotated_rectangle"""
        bbox = list(pol.exterior.coords)
        axis1 = LineString([bbox[0], bbox[3]])
        axis2 = LineString([bbox[0], bbox[1]])

        if axis1.length <= axis2.length:
            az = cls._azimuth(bbox[0], bbox[1])
        else:
            az = cls._azimuth(bbox[0], bbox[3])

        return az

    @classmethod
    def polygon_to_dims(cls, pol: Polygon) -> PolDims:
        sides = get_sides_as_lines_by_length(polygon=pol)

        return PolDims(
            centroid_x=pol.centroid.x,
            centroid_y=pol.centroid.y,
            width=sides[0].length,
            height=sides[2].length,
            angle=cls._get_angle(pol),
        )

    @staticmethod
    def dims_to_polygon(dims=PolDims) -> Polygon:
        return get_polygon_from_pos_dim_angle(
            pos=(dims.centroid_x, dims.centroid_y),
            dim=(dims.width, dims.height),
            angle=dims.angle,
            centroid=True,
        )
