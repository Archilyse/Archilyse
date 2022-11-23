from typing import Union

from shapely.geometry import LineString, MultiLineString, MultiPolygon, Polygon


def as_multipolygon(any_shape: Union[Polygon, MultiPolygon]) -> MultiPolygon:
    return (
        any_shape if isinstance(any_shape, MultiPolygon) else MultiPolygon([any_shape])
    )


def as_multi_linestring(
    any_shape: Union[LineString, MultiLineString]
) -> MultiLineString:
    return (
        any_shape
        if isinstance(any_shape, MultiLineString)
        else MultiLineString([any_shape])
    )


def get_biggest_polygon(multipolygon: Union[MultiPolygon, Polygon]) -> Polygon:
    if isinstance(multipolygon, Polygon):
        multipolygon = MultiPolygon([multipolygon])

    return sorted(multipolygon.geoms, key=lambda x: x.area)[-1]
