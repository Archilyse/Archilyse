from typing import Tuple

import numpy as np


def rotate_vec_right(vec: Tuple[float, float]) -> np.array:
    """turns a 2d vector to the right

    Returns:
        np.array: right turned vector
    """
    return np.array([vec[1], -vec[0]])
