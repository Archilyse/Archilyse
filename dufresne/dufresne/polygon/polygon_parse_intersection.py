from typing import Optional, Union

from shapely.geometry import GeometryCollection, LineString, MultiLineString


def parse_intersection(
    intersection: Union[MultiLineString, GeometryCollection, LineString]
) -> Optional[LineString]:
    """Returns the first linestring of an intersection geometry, if there is one."""
    if isinstance(intersection, MultiLineString):
        return intersection.geoms[0]
    if isinstance(intersection, GeometryCollection):
        linestrings = [x for x in intersection.geoms if isinstance(x, LineString)]
        if linestrings:
            return linestrings[-1]
    elif isinstance(intersection, LineString):
        return intersection

    return
