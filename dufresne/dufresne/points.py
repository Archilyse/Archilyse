import numpy as np
from shapely.geometry import Polygon, mapping


def get_points(polygon: Polygon) -> np.array:
    return mapping(polygon)["coordinates"]
