from dataclasses import dataclass

from shapely.geometry import LineString, MultiPolygon, Point, Polygon


@dataclass
class Geometry:
    geom: Point | LineString | Polygon | MultiPolygon
    properties: dict
