import numpy as np


def get_angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """get the angle between vectors

    Args:
        v1 (np.ndarray): a vector
        v2 (np.ndarray): a vector

    Returns:
       float: angle in rad
    """
    length = np.linalg.norm(v1) * np.linalg.norm(v2)
    if not length:
        return None
    cos_alpha = np.dot(v1, v2) / length
    return np.arccos(cos_alpha)
