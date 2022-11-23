from typing import Tuple

from shapely.affinity import rotate, translate
from shapely.geometry import Polygon


def rotate_translate_polygon(
    polygon: Polygon,
    x_off: float,
    y_off: float,
    angle: float,
    pivot: Tuple[float, float] = (0, 0),
) -> Polygon:
    if angle:
        polygon = rotate(polygon, -angle, origin=(pivot[0], pivot[1]))
    polygon = translate(polygon, xoff=x_off, yoff=y_off)
    return polygon
