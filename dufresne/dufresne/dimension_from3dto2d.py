from typing import Union

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Polygon

from dufresne.points import get_points


def from3dto2d(
    obj: Union[LineString, Polygon, MultiPolygon]
) -> Union[LineString, Polygon, MultiPolygon]:
    """Reduces the dimension of the input object from 3d to 2d. So far the method handles the following type of objects:
        - shapely Linestring, Polygon, Multipolygon

    Args:
        obj (object): any geometrical object

    Returns:
        [object]: object of same type as input object
    """

    if isinstance(obj, LineString):
        coords = np.array(list(obj.coords))
        coords2d = coords[:, :2]
        linestring2d = LineString(coords2d)
        return linestring2d

    elif isinstance(obj, Polygon):
        coords = get_points(obj)
        if len(coords) == 1:
            exterior_points = coords[0]
            exteriors = []
            for point in exterior_points:
                point2d = [point[0], point[1]]
                exteriors.append(point2d)
            return Polygon(exteriors)

        elif len(coords) >= 2:
            exterior_points = coords[0]
            exteriors = []
            for point in exterior_points:
                point2d = [point[0], point[1]]
                exteriors.append(point2d)

            interior_rings = coords[1:]
            interior_rings2d = []
            for ring in interior_rings:
                ring2d = []
                for point in ring:
                    point2d = [point[0], point[1]]
                    ring2d.append(point2d)
                interior_rings2d.append(ring2d)

            return Polygon(exteriors, interior_rings2d)

    elif isinstance(obj, MultiPolygon):
        return MultiPolygon([from3dto2d(polygon) for polygon in obj.geoms])
