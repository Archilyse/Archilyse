import numpy as np


def get_quaternion(axis: np.ndarray, angle: float) -> np.ndarray:
    """builds a quaternion

    Args:
        axis ([type]): [description]
        angle ([type]): [description]

    Returns:
        [type]: [description]
    """
    quaternion = np.zeros(4)
    quaternion[0] = 1
    axis_length = np.linalg.norm(axis)
    if axis_length > 0.00001:
        axis = axis / axis_length
        quaternion[0] = np.cos(angle / 2)
        quaternion[1:] = np.sin(angle / 2) * axis
    return quaternion
