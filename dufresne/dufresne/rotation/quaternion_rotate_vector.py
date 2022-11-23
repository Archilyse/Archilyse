# """ module for rotation operations """
import numpy as np

from dufresne.rotation.quaternion_conjugate import conjugate_quaternion
from dufresne.rotation.quaternion_hamilton_product import hamilton_product


def rotate_vector_with_quaternion(quaternion: np.ndarray, vector: np.ndarray):
    """rotate a vector with a given quaternion

    Args:
        quaternion (np.ndarray): quaternion describing the rotation
        vector (np.ndarray): vector to roate

    Returns:
        np.ndarray: rotated vector
    """
    q_vector = np.zeros(4)
    q_vector[1:] = vector
    return hamilton_product(
        quaternion, hamilton_product(q_vector, conjugate_quaternion(quaternion))
    )[1:]
