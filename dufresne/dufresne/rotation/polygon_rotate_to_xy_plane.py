import numpy as np
from shapely.geometry import Polygon

from dufresne.points import get_points
from dufresne.rotation.get_perpendicular_planevec import get_perpendicular_planevec
from dufresne.rotation.quaternion_build import get_quaternion
from dufresne.rotation.quaternion_rotate_vector import rotate_vector_with_quaternion
from dufresne.rotation.vectors_get_angle import get_angle_between_vectors


def rotate_polygon_to_xy_plane(polygon: Polygon) -> np.array:
    """rotates a polygon to the xy plane

    Args:
        polygon (Polygon): [description]

    Returns:
        np.array: [description]
    """
    # gets the points and direction
    poly_points = get_points(polygon)
    exteriors = np.asarray(poly_points[0])
    interiors = []
    if len(poly_points) > 1:
        interiors = np.asarray(poly_points[1:])
    direction_vector = np.array([0, 0, 1])
    perpendicular_planvec = get_perpendicular_planevec(exteriors)
    # build the quaternion
    angle = get_angle_between_vectors(v1=perpendicular_planvec, v2=direction_vector)
    axis = np.cross(perpendicular_planvec, direction_vector)
    quaternion = get_quaternion(axis=axis, angle=angle)
    # rotate
    rotated_exteriors = [
        rotate_vector_with_quaternion(quaternion, point) for point in exteriors
    ]
    rotated_interiors = []
    for interior_hole in interiors:
        rotated_interiors.append(
            [
                rotate_vector_with_quaternion(quaternion, point).tolist()
                for point in interior_hole
            ]
        )
    return Polygon(rotated_exteriors, rotated_interiors), quaternion
