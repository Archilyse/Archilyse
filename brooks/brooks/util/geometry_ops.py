from operator import itemgetter
from typing import Iterator, Optional, Tuple, Union

from numpy import array, dot, ndarray
from numpy.linalg import linalg
from shapely import wkt
from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.ops import unary_union
from shapely.validation import explain_validity

from common_utils.constants import GEOMETRIES_PRECISION
from common_utils.exceptions import BrooksException, InvalidShapeException
from dufresne.polygon import get_sides_as_lines_by_length


def remove_small_holes_and_lines(
    geometry: Union[Polygon, MultiPolygon, GeometryCollection],
    allow_empty: bool = False,
    min_line_width: Optional[float] = None,
) -> Union[Polygon, MultiPolygon, GeometryCollection]:
    geometry = remove_small_lines_from_geometry(
        geometry=geometry, min_line_width=min_line_width
    )

    if isinstance(geometry, MultiPolygon):
        geometry = MultiPolygon(
            [
                remove_small_holes_from_polygon(polygon=polygon)
                for polygon in geometry.geoms
            ]
        )

    elif isinstance(geometry, Polygon):
        geometry = remove_small_holes_from_polygon(polygon=geometry)

    if isinstance(geometry, GeometryCollection) and geometry.is_empty:
        return Polygon()

    if allow_empty and geometry.is_empty:
        return Polygon()

    return ensure_geometry_validity(geometry=geometry)


def ensure_geometry_validity(
    geometry: Union[LineString, Polygon, MultiPolygon],
    force_single_polygon: bool = False,
) -> Union[LineString, Polygon, MultiPolygon]:
    """Try different strategies to make the geometry valid
    NOTE: These methods _should_ not change the geometry substantially
     but somehow fix invalid geometries sometimes.
     force_single_polygon: If True, the geometry returned should be a  polygon
    """

    def _check_is_polygon_if_necessary(geom: Union[Polygon, MultiPolygon]) -> bool:
        if force_single_polygon and isinstance(geom, MultiPolygon):
            return False
        return True

    def apply_zero_buffer(
        geom: Union[Polygon, MultiPolygon]
    ) -> Union[Polygon, MultiPolygon]:
        return geom.buffer(0)

    def apply_unary_union(
        geom: Union[Polygon, MultiPolygon]
    ) -> Union[Polygon, MultiPolygon]:
        return unary_union(geom)

    def apply_and_reverse_buffer(
        geom: Union[Polygon, MultiPolygon]
    ) -> Union[Polygon, MultiPolygon]:
        geom = geom.buffer(0.1)
        return geom.buffer(-0.1)

    def ignore_small_polygons(
        geom: Union[Polygon, MultiPolygon]
    ) -> Union[Polygon, MultiPolygon]:
        if isinstance(geom, MultiPolygon) and force_single_polygon:
            max_area = max(polygon.area for polygon in geom.geoms)
            for tested_area_percent in (0.001, 0.005, 0.01, 0.05):
                minimum_area = max_area * tested_area_percent
                selected_pols = [p for p in geom.geoms if p.area > minimum_area]
                if len(selected_pols) == 1:
                    return selected_pols[0]

        return geom

    if geometry.is_valid and _check_is_polygon_if_necessary(geometry):
        return geometry

    for strategy in (
        apply_zero_buffer,
        apply_unary_union,
        apply_and_reverse_buffer,
        ignore_small_polygons,
    ):
        new_geom = strategy(geometry)
        if new_geom.is_valid and _check_is_polygon_if_necessary(new_geom):
            break
    else:
        if geometry.is_valid and force_single_polygon:
            raise InvalidShapeException(
                f"Geometry is not valid as it cant be converted to a polygon. Num geoms: {len(geometry.geoms)}"
            )
        raise InvalidShapeException(explain_validity(geometry))
    return new_geom


def get_center_line_from_rectangle(
    polygon: Polygon, only_longest: bool = True
) -> Tuple:
    """Given a rectangle polygon it returns the line starting in the middle of the shorter side and ending
    in the center of the other most short side of the polygon as per the image:

               +-----------------------------------+
               |                                   |
             a +-----------------------------------+ b
               |                                   |
               +-----------------------------------+

    If only longest is False also the shorter centerline is returned

    """
    four_sides = get_sides_as_lines_by_length(polygon=polygon)
    shortest_line = four_sides[0]
    other_sides_sorted_by_most_parallel = sorted(
        [
            (
                other_line,
                abs(
                    dot_product_normalised_linestrings(
                        line_a=shortest_line, line_b=other_line
                    )
                ),
            )
            for other_line in four_sides[1:]
        ],
        key=itemgetter(1),
        reverse=True,
    )
    parallel_side = other_sides_sorted_by_most_parallel[0][0]
    if only_longest:
        return (LineString([shortest_line.centroid, parallel_side.centroid]),)

    return LineString([shortest_line.centroid, parallel_side.centroid]), LineString(
        [
            other_sides_sorted_by_most_parallel[1][0].centroid,
            other_sides_sorted_by_most_parallel[2][0].centroid,
        ]
    )


def dot_product_normalised_linestrings(
    line_a: LineString, line_b: LineString
) -> Union[ndarray, float]:
    """
    The returned value is between [-1,1]
    """
    coords_a = line_a.coords
    coords_b = line_b.coords
    a_x1, a_y1, a_x2, a_y2 = (
        coords_a[0][0],
        coords_a[0][1],
        coords_a[1][0],
        coords_a[1][1],
    )
    b_x1, b_y1, b_x2, b_y2 = (
        coords_b[0][0],
        coords_b[0][1],
        coords_b[1][0],
        coords_b[1][1],
    )

    v_a = array([a_x2 - a_x1, a_y2 - a_y1])

    v_b = array([b_x2 - b_x1, b_y2 - b_y1])

    return round(
        dot(v_a / linalg.norm(v_a), v_b / linalg.norm(v_b)), ndigits=6
    )  # rounding is necessary to avoid values below and above 1


def buffer_unbuffer_geometry(
    geometry: Union[Polygon, MultiPolygon],
    buffer: float = 0.1,
    reverse: bool = False,
) -> Union[Polygon, MultiPolygon]:
    for distance in sorted([-buffer, buffer], reverse=not reverse):
        geometry = geometry.buffer(
            distance=distance, join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.square
        )
    return geometry


def get_line_strings(
    geometry: Union[LineString, MultiLineString, Point, MultiPoint, GeometryCollection]
) -> Iterator[LineString]:
    if geometry:
        if isinstance(geometry, LineString):
            yield geometry
        elif isinstance(geometry, (GeometryCollection, MultiLineString)):
            for geom in geometry.geoms:
                yield from get_line_strings(geom)
        elif not isinstance(geometry, (Point, MultiPoint)):
            raise BrooksException(f"Unsupported geometry type {geometry.geom_type}.")


def get_polygons(
    geometry: Union[
        Polygon,
        MultiPolygon,
        LineString,
        MultiLineString,
        Point,
        MultiPoint,
        GeometryCollection,
    ]
) -> Iterator[Polygon]:
    if geometry:
        if isinstance(geometry, Polygon):
            yield geometry
        elif isinstance(geometry, (GeometryCollection, MultiPolygon)):
            for geom in geometry.geoms:
                yield from get_polygons(geom)
        elif not isinstance(geometry, (LineString, MultiLineString, Point, MultiPoint)):
            raise BrooksException(f"Unsupported geometry type {geometry.geom_type}.")


def round_geometry(shapely_geometry, precision: int = GEOMETRIES_PRECISION):
    """
    Applied to avoid floating point precision problems
    """
    return wkt.loads(wkt.dumps(shapely_geometry, rounding_precision=precision))


def buffer_n_rounded(geom: Polygon, buffer, precision: int):
    return ensure_geometry_validity(
        round_geometry(
            geom.buffer(
                distance=buffer,
                join_style=JOIN_STYLE.mitre,
                cap_style=CAP_STYLE.square,
            ),
            precision=precision,
        )
    )


def remove_small_holes_from_polygon(polygon: Polygon) -> Polygon:
    polygon = buffer_unbuffer_geometry(geometry=polygon)
    new_interiors = []
    for interior in polygon.interiors:
        if not Polygon(interior).is_valid:
            continue
        if Polygon(interior).area < 0.01:
            continue
        new_interiors.append(interior)
    return Polygon(shell=polygon.exterior, holes=new_interiors)


def remove_small_lines_from_geometry(
    geometry: Union[Polygon, MultiPolygon, GeometryCollection],
    min_line_width: Optional[float] = None,
) -> Union[Polygon, MultiPolygon, GeometryCollection]:
    if min_line_width is None:
        min_line_width = 0.01

    return buffer_unbuffer_geometry(
        geometry=geometry, buffer=min_line_width, reverse=True
    )


def safe_simplify(geom: Polygon) -> Polygon:
    # returns a safely simplified version of the polygon
    return ensure_geometry_validity(geom.simplify(0.0001, preserve_topology=True))
