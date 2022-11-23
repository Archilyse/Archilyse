from typing import List, Optional

import numpy as np
import triangle as tr
from shapely.geometry import Polygon

from dufresne.dimension_from3dto2d import from3dto2d
from dufresne.points import get_points
from dufresne.rotation.polygon_rotate_to_xy_plane import rotate_polygon_to_xy_plane
from dufresne.rotation.quaternion_conjugate import conjugate_quaternion
from dufresne.rotation.quaternion_rotate_vector import rotate_vector_with_quaternion


def _triangulate_polygon_2d(
    polygon: Polygon, mode: Optional[str] = "pqa"
) -> List[Polygon]:
    """
    triangulate library returns a dictionary where the original vertices given are still present
    and then under triangles we have indexes that references the original vertices.

    Note: triangulate library crashes if the polygon contains z values

    Example:
        Given the exterior coords as [(5607.1, -4007.0),
                                        (5607.1, -4014.0),
                                        (5544.9, -4014.0),
                                        (5544.9, -4007.0),
                                        (5607.1, -4007.0)]

        The output of triangulate is partially as follows:
        {'vertices': array([[ 5607.1, -4007. ],
                            [ 5607.1, -4014. ],
                            [ 5544.9, -4014. ],
                            [ 5544.9, -4007. ],
                            [ 5607.1, -4007. ]]),
        'triangles': array([[3, 2, 1],
                            [1, 4, 3]], dtype=int32)
        }

        So we can index the vertices array using the triangles array of indexes.
    """
    vertex_dict = {}
    vertices = []
    segments = []
    holes = []

    count = 0
    #: Retrieve vertices, segments from polygon exterior
    coords = polygon.exterior.coords
    for i in range(len(coords)):  # pylint: disable=C0200
        vertex = coords[i][:2]
        if vertex not in vertex_dict:
            vertex_dict[vertex] = count
            vertices.append(vertex)
            count += 1
        if i > 0:
            i1 = vertex_dict[coords[(i - 1) % len(coords)][:2]]
            i2 = vertex_dict[vertex]
            segments.append((i1, i2))

    #: Retrieve vertices, segments, holes from polygon interior
    for interior in polygon.interiors:
        if Polygon(interior).area < 1e-5:
            continue

        coords = interior.coords
        for i in range(len(coords)):  # pylint: disable=C0200
            vertex = coords[i][:2]
            if vertex not in vertex_dict:
                vertex_dict[vertex] = count
                vertices.append(vertex)
                count += 1
            if i >= 0:
                i1 = vertex_dict[coords[(i - 1) % len(coords)]]
                i2 = vertex_dict[vertex]
                segments.append((i1, i2))
        hole = np.array(Polygon(interior).representative_point().coords).flatten()
        holes.append(hole)

    #: Set triangulation parameters for triangle.h
    triangulation_parameters = {
        "vertices": list(map(np.asarray, vertices)),
        "segments": segments,
    }
    if holes:
        triangulation_parameters["holes"] = holes

    #: Execute triangulation
    triangulated = tr.triangulate(triangulation_parameters, mode)
    return [
        Polygon(coords)
        for coords in triangulated["vertices"][triangulated["triangles"]]
    ]


def triangulate_polygon(polygon: Polygon, mode="pqa") -> List[List[np.ndarray]]:
    """triangulates a z-polygon into a list of nd.arrays

    Args:
        polygon (Polygon): a arbitrary (also concave possible) polygon
        mode (str): The triangulation mode for triangle.c see https://www.cs.cmu.edu/~quake/triangle.switch.html

    Returns:
        List[np.ndarray]: list of triangles [[[x1,y1,z1],[x2,y2,z2],[x3,y3,z3]],..]
    """

    points = get_points(polygon)
    # 2d case
    if len(points[0][0]) == 2:
        triangles = []
        for t in _triangulate_polygon_2d(polygon, mode=mode):
            triangles.append(t.exterior.coords[:3])
        return triangles

    # already a triangle
    if len(points[0]) == 4:
        output = [list(map(np.array, points[0][:3]))]
        return output

    rotated_polygon, quaternion = rotate_polygon_to_xy_plane(polygon)
    result = get_points(rotated_polygon)
    z_coordinate = result[0][0][2]

    rotated_2d_polygon = from3dto2d(rotated_polygon)
    if not rotated_2d_polygon.is_valid:
        return []

    triangles = _triangulate_polygon_2d(rotated_2d_polygon, mode=mode)
    back_triangles = []
    for tri in triangles:
        points = np.array(tri.exterior.coords)
        back_points = []
        for point in points[:3]:
            point = np.append(point, z_coordinate)
            back_point = rotate_vector_with_quaternion(
                conjugate_quaternion(quaternion), point
            )
            back_points.append(back_point)
        back_triangles.append(back_points)
    return back_triangles
