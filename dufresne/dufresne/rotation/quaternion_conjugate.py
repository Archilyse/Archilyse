import numpy as np
from pyquaternion import Quaternion


def conjugate_quaternion(q: np.ndarray) -> np.ndarray:
    """conjugates a quaternion

    Args:
        q: quaternion

    Returns:
        conjugated quaternion
    """
    return Quaternion(q).conjugate.elements
