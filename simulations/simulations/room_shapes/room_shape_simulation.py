from typing import Dict

import numpy as np
from shapely.geometry import Polygon

from dufresne.polygon import get_sides_as_lines_by_length


def get_room_shapes(polygon: Polygon) -> Dict[str, float]:
    line_lengths = [
        line.length for line in get_sides_as_lines_by_length(polygon=polygon)
    ]
    std_walllengths = np.std(line_lengths)
    mean_walllengths = np.mean(line_lengths)
    compactness = get_polygon_compactness(polygon)
    result = {
        "mean_walllengths": float(mean_walllengths),
        "compactness": compactness,
        "std_walllengths": float(std_walllengths),
    }
    return result


def get_polygon_compactness(polygon: Polygon) -> float:
    """Calculates the room- and corridor Index of a polygon

    this _index is based on two things:
        1. how compact is a polygon - the more compact a polygon the more
            likely to be a room - this is in ratio
            (ratio->1 => polygon->room)
        2. if there are strange shapes that might influence the definition
            above - this is in phi

    Args:
        polygon: a shapely polygon
    Returns:
        room_index(float):a number n 0<n<1 describing how compact/round
                            a polygon is (1 is a circle)
    """
    compactness = polygon.area / (polygon.length * polygon.length) * 4 * np.pi
    return compactness
