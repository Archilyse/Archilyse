import numpy as np
from pyquaternion import Quaternion


def hamilton_product(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """builds the hamilton product of two quaternions

    Args:
        a (np.ndarray): a quaternion bevor the hamiltonp
        b (np.ndarray): a quaternion bevor the hamiltonp

    Returns:
        np.ndarray: a quaternion after the hamiltonp
    """
    return (Quaternion(a) * Quaternion(b)).elements
