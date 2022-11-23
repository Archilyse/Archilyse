from shapely.geometry import Polygon


def get_polygon_from_coordinates(coordinates) -> Polygon:
    if len(coordinates) == 1:
        polygon = Polygon(coordinates[0])
    else:
        shell = coordinates[0]
        holes = coordinates[1:]
        try:
            polygon = Polygon(shell=shell, holes=holes)
        except (AttributeError, ValueError):
            try:
                return Polygon(shell=shell[0], holes=holes[0])
            except (AttributeError, ValueError):
                return Polygon(shell=shell[0][0], holes=holes[0][0])
    return polygon
