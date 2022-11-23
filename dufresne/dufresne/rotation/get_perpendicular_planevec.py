from typing import List

import numpy as np


def get_perpendicular_planevec(points: List[np.ndarray]) -> np.ndarray:
    """search for perpendicular vectors from points in a plane

    this is done via two vectors on a plane and their crossproduct

    Args:
        points (List[float]): points on a plane
    Returns:
        np.ndarray: two perpendicular vectors on a plane
    """
    for o in range(len(points) - 2):
        po = points[o]
        for i in range(o + 1, len(points) - 1):
            pi = points[i]
            vi = pi - po
            length_vi = np.linalg.norm(vi)
            if length_vi == 0:
                continue
            vi = vi / length_vi
            for k in range(i + 1, len(points)):
                pk = points[k]
                vk = pk - po
                length_vk = np.linalg.norm(vk)
                if length_vk == 0:
                    continue
                vk = vk / length_vk
                dot = np.dot(vk, vi)
                if abs(dot) < 0.9999999:
                    break
            perpendicular_vec = np.cross(vi, vk)
            return perpendicular_vec / np.linalg.norm(perpendicular_vec)
