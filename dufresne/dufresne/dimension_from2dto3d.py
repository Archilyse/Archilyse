from shapely.geometry import MultiPolygon, Point, Polygon

from dufresne.points import get_points
from dufresne.polygon import get_polygon_from_coordinates


def from2dto3d(obj, z_coordinate):

    if isinstance(obj, Point):
        x = obj.x
        y = obj.y
        point = Point(x, y, z_coordinate)
        return point

    if isinstance(obj, Polygon):
        coordinates = get_points(obj)
        polygon_3d = []
        for closed_ring in coordinates:
            closed_ring_3d = []
            for point in closed_ring:
                closed_ring_3d.append((point[0], point[1], z_coordinate))
            polygon_3d.append(closed_ring_3d)

        return get_polygon_from_coordinates(polygon_3d)

    if isinstance(obj, MultiPolygon):
        obj_3d = []
        for polygon in obj:
            coordinates = get_points(polygon)
            polygon_3d = []
            for closed_ring in coordinates:
                closed_ring_3d = []
                for point in closed_ring:
                    closed_ring_3d.append((point[0], point[1], z_coordinate))
                polygon_3d.append(closed_ring_3d)

            obj_3d.append(get_polygon_from_coordinates(polygon_3d))

        return MultiPolygon(obj_3d)
