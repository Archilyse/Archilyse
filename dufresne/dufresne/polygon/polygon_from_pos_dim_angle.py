from typing import Tuple

import numpy as np
from shapely.geometry import Polygon

from dufresne.polygon.polygon_rotate_translate import rotate_translate_polygon


def get_polygon_from_pos_dim_angle(
    pos: Tuple[float, float],
    dim: Tuple[float, float],
    angle: float,
    centroid=True,
) -> Polygon:
    """Extract a 2d polygon from bounding box parameters

    this aabb starts at the origin like follows:
            dim[0]
            -----
            |    |
            |    | dim[1]
            |    |
            o----
          (0,0)

    Returns:
        Polygon: A shapely polygon
    """
    polygon = get_polygon_from_dim(dim=dim, centroid=centroid)
    polygon = rotate_translate_polygon(
        polygon=polygon, x_off=pos[0], y_off=pos[1], angle=angle
    )
    return polygon


def get_polygon_from_dim(dim: Tuple[float, float], centroid: bool = True) -> Polygon:
    """Extract a 2d polygon from bounding box parameters

    this build starts at the origin - if centroid is true - as follows:
            dim[0]
            ------
            |(0,0)|
            |  o  | dim[1]
            |     |
             -----

    where as centroid is false it is build as follows:

            dim[0]
            -----
            |    |
            |    | dim[1]
            |    |
            o----
            (0,0)

    Args:
        dim ([float]): The 2d dimensions of the bounding box
        centroid: if source is centroid or lower left corner

    Returns:
        Polygon: A shapely polygon
    """
    if centroid:
        points = (
            np.array(
                [
                    [-dim[0], -dim[1]],
                    [dim[0], -dim[1]],
                    [dim[0], dim[1]],
                    [-dim[0], dim[1]],
                ]
            )
            / 2
        )
    else:
        v1 = np.asarray([0, 0])
        v2 = v1 + np.asarray([dim[0], 0])
        v3 = v1 + np.asarray([dim[0], dim[1]])
        v4 = v1 + np.asarray([0, dim[1]])
        points = [v1, v2, v3, v4]

    return Polygon(points)
