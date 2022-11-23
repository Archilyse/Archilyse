"""
Implements the volume computation described in:
    Zhang, Cha, and Tsuhan Chen.
    "Efficient feature extraction for 2D/3D objects in mesh representation."
    In Proceedings 2001 International Conference on Image Processing (Cat. No. 01CH37205),
        vol. 3, pp. 935-938. IEEE, 2001.

First, the view algorithm is used to determine all outside faces by spanning a bounding box
and determining for each face whether the bounding box is visible. Secondly, the formula described
in the paper is used to determine the volume.

Note that the faces have to be disjoint for the algorithm to work properly.
"""
import itertools
import operator
from functools import reduce

import numpy as np

from simulations.view import ViewWrapper


def _get_bbox(triangles, eps=1):
    vertices = reduce(operator.concat, triangles)
    bounds = np.array(
        [np.array(vertices).min(axis=0), np.array(vertices).max(axis=0)]
    ).T
    bbox_vertices = [
        [bounds[s][t] + (2 * t - 1) * eps for s, t in enumerate((i, j, k))]
        for i, j, k in itertools.product([0, 1], repeat=3)
    ]
    bbox_faces = [
        [0, 1, 2],
        [1, 2, 3],
        [1, 3, 5],
        [3, 5, 7],
        [0, 1, 4],
        [1, 4, 5],
        [0, 2, 4],
        [2, 4, 6],
        [2, 3, 6],
        [3, 6, 7],
        [4, 5, 6],
        [5, 6, 7],
    ]

    return [
        (bbox_vertices[i], bbox_vertices[j], bbox_vertices[k]) for i, j, k in bbox_faces
    ]


def _signed_triangle_volume(p1, p2, p3):
    v321 = p3[0] * p2[1] * p1[2]
    v231 = p2[0] * p3[1] * p1[2]
    v312 = p3[0] * p1[1] * p2[2]
    v132 = p1[0] * p3[1] * p2[2]
    v213 = p2[0] * p1[1] * p3[2]
    v123 = p1[0] * p2[1] * p3[2]

    return (-v321 + v231 + v312 - v132 - v213 + v123) / 6


def _get_normal(p1, p2, p3) -> np.ndarray:
    epsilon = 0.000000001
    v1, v2, v3 = (
        np.array(p1, dtype=np.float),
        np.array(p2, dtype=np.float),
        np.array(p3, dtype=np.float),
    )
    N = np.cross(v2 - v1, v3 - v1)
    N /= np.linalg.norm(N) + epsilon
    return N


def compute_volume(triangles, eps: float = 0.00001) -> float:
    """Computes the volume of a closed mesh. Note that the faces have to be disjoint for the algorithm to work properly.

    Args:
        triangles (list): The triangles
        eps (float, optional): Parameter to shift the centroid of each face into a particular direction.
            Defaults to 0.00001.

    Returns:
        float: The volume.
    """
    wrapper = ViewWrapper(resolution=16)
    wrapper.add_triangles(_get_bbox(triangles), group="bbox")
    wrapper.add_triangles(np.array(triangles), group="model")

    faces = []
    for a, b, c in triangles:
        normal = _get_normal(a, b, c)
        centroid = np.array([a, b, c]).mean(axis=0)
        shifted_centroid = centroid + normal * eps
        wrapper.add_observation_point(tuple(shifted_centroid.tolist()))  # type: ignore

        faces.append((a, b, c))

    results = wrapper.run()
    obs_results = [v["simulations"]["area_by_group"]["bbox"] for v in results]

    faces_outside = [
        faces[idx] for idx, result in enumerate(obs_results) if result != 0
    ]
    return abs(sum([_signed_triangle_volume(*t) for t in faces_outside]))
