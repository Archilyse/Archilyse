from typing import List, Tuple

from shapely.geometry import Polygon

from dufresne.polygon.extruder import Extruder


def get_triangles_from_extruded_polygon(
    polygon: Polygon, ground_level: float, height: float
) -> List[Tuple[float, float, float]]:
    """gets the triangles from an extruded polygon with height

    Args:
        polygon: footprint of the extruded thing
        ground_level: ground level of the thing e.g. 300 m
        height: top level of the thing e.g. 320 m ...
                        this would mean the object itself is 20 m high
    """
    triangles = Extruder.get_triangles(
        polygon=polygon, ground_level=ground_level, height=height
    )
    return [triangle[:3] for triangle in triangles]
