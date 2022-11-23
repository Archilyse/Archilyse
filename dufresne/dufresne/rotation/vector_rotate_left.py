from typing import Tuple

import numpy as np


def rotate_vec_left(vec: Tuple[float, float]) -> np.array:
    """turns a 2d vector to the left

    Returns:
        np.array: left turned vector
    """
    return np.array([-vec[1], vec[0]])
