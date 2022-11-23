from itertools import chain
from typing import Dict, Iterator, List, Optional, Set, Tuple

import numpy
from pygeos import Geometry
from pygeos import area as pygeos_areas
from pygeos import (
    distance,
    from_shapely,
    intersection,
    intersects,
    minimum_rotated_rectangle,
    multipolygons,
    to_shapely,
)
from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry
from shapely.ops import polygonize_full, unary_union

from brooks.constants import THICKEST_WALL_POSSIBLE_IN_M
from brooks.types import AreaType
from dufresne.linestring_add_width import add_width_to_linestring_improved
from dufresne.polygon import get_sides_as_lines_by_length
from dufresne.polygon.utils import as_multipolygon, get_biggest_polygon
from handlers.dxf.dxf_constants import (
    AREA_NAME_TO_TYPE_MAPPING,
    MINIMUM_PERCENTAGE_AREA_ADDITION_TO_NOT_BE_REMOVED,
    POLYGON_DUPLICATED_THRESHOLD_IN_CM2,
    POLYGON_DUPLICATED_THRESHOLD_IN_PERCENTAGE,
)


def is_wall_between_geometries(
    group_centroid: Point,
    element: Polygon,
    walls: MultiPolygon,
) -> bool:

    connecting_line_between_element_and_group = LineString(
        [element.centroid, group_centroid]
    )
    return connecting_line_between_element_and_group.intersects(walls)


def filter_overlapping_or_small_polygons(
    polygons: List[Polygon],
    minimum_size: float = 60 * 60,
    condition: str = "intersects",
) -> List[Polygon]:
    sorted_descending_polygons = sorted(polygons, key=lambda x: x.area, reverse=True)
    current_total_polygon = Polygon()
    final_polygons = []
    for polygon in sorted_descending_polygons:
        # From the skeleton pieces we only include stairs bigger than 60cmx60cm or those that are not intersecting
        # with the bigger pieces of stairs
        if (
            not getattr(polygon, condition)(current_total_polygon)
            and polygon.area >= minimum_size
            and polygon.difference(current_total_polygon).area
            > (polygon.area / MINIMUM_PERCENTAGE_AREA_ADDITION_TO_NOT_BE_REMOVED)
        ):
            final_polygons.append(polygon)
            current_total_polygon = unary_union(final_polygons)
    return final_polygons


def exclude_polygons_split_by_walls(
    wall_polygons: List[Polygon], polygons: List[Polygon | LineString]
) -> List[Polygon]:
    unionized_walls = unary_union(wall_polygons)
    polygons_not_crossing_walls = []
    for polygon in polygons:
        polygon_difference = polygon.difference(unionized_walls)
        if not isinstance(polygon_difference, MultiPolygon):
            polygons_not_crossing_walls.append(
                polygon_difference.minimum_rotated_rectangle
            )
        else:
            biggest = get_biggest_polygon(polygon_difference).minimum_rotated_rectangle
            # Oblique polygons won't pass this check, the minimum rectangle will expand again
            # over the wall
            if not isinstance(biggest.difference(unionized_walls), MultiPolygon):
                polygons_not_crossing_walls.append(biggest)
    return polygons_not_crossing_walls


def _group_geometries_by_distance_threshold(
    index_element_to_group_around: int,
    all_elements_indexed: Dict[int, Polygon],
    distance_to_consider_group: int,
    all_walls_union: MultiPolygon,
) -> Set[int]:
    group_indices = {index_element_to_group_around}
    element_to_group_around = all_elements_indexed[index_element_to_group_around]
    group_elements = [element_to_group_around]

    for i, element in sorted(
        all_elements_indexed.items(),
        key=lambda elem: elem[1].distance(element_to_group_around),
    ):
        if i != index_element_to_group_around:
            if element.distance(element_to_group_around) < distance_to_consider_group:
                if is_wall_between_geometries(
                    group_centroid=unary_union(group_elements).centroid,
                    element=element,
                    walls=all_walls_union,
                ):
                    continue
                group_elements.append(element)
                group_indices.add(i)
    return group_indices


def get_bounding_boxes_for_groups_of_geometries(
    geometries: List[BaseGeometry], buffer: float = 0.001
) -> List[Polygon]:
    """
    The purpose of this method is to group geometries which are making up an object and return
    its bounding box

    See testcase for an example of why all steps are necessary
    1. we buffer all geometries (slightly) to ensure that all of them are polygons
    2. taking the union of them to merge for example lines
    3. taking the minimum rotated rectangle of all geometries to remove interiors
    4. again take unary union to merge the geometries
    """
    buffered_and_unionized_geometries = as_multipolygon(
        unary_union(
            [
                geom.buffer(
                    distance=buffer,
                    join_style=JOIN_STYLE.mitre,
                    cap_style=CAP_STYLE.square,
                )
                for geom in geometries
            ]
        )
    )
    grouped_geometries = [
        geom.minimum_rotated_rectangle
        for geom in as_multipolygon(
            unary_union(
                [
                    geom.minimum_rotated_rectangle
                    for geom in buffered_and_unionized_geometries.geoms
                ]
            )
        ).geoms
    ]
    return grouped_geometries


def split_polygons_fully_intersected_by_a_wall(
    bounding_boxes: List[Polygon], all_walls_union: MultiPolygon
):
    """In some cases 2 items separated by a wall are merged together, if that is the case we split it"""
    final_geometries = []
    for bounding_box in bounding_boxes:
        sub_bounding_boxes = as_multipolygon(bounding_box.difference(all_walls_union))
        for sub_bounding_box in sub_bounding_boxes.geoms:
            final_geometries.append(sub_bounding_box.minimum_rotated_rectangle)
    return final_geometries


def get_area_type_from_room_stamp(room_stamp: str) -> Optional[AreaType]:
    room_stamp = "".join(
        [
            x
            for x in room_stamp.strip().rstrip()
            if not x.isdigit() and x.isalpha() and not x.isspace()
        ]
    ).upper()
    if room_stamp in AREA_NAME_TO_TYPE_MAPPING:
        return AREA_NAME_TO_TYPE_MAPPING[room_stamp]
    return None


def group_line_and_arcs_into_rectangles(
    distance_to_consider_group: int,
    all_elements: List[LineString],
    all_walls_union: MultiPolygon,
) -> Iterator[Polygon]:
    all_elements_indexed = {i: element for i, element in enumerate(all_elements)}
    while all_elements_indexed:
        # We group here all lines that are close to each other
        new_group_indices = _group_geometries_by_distance_threshold(
            index_element_to_group_around=list(all_elements_indexed.keys())[0],
            all_elements_indexed=all_elements_indexed,
            distance_to_consider_group=distance_to_consider_group,
            all_walls_union=all_walls_union,
        )
        new_group_geometries = [
            all_elements_indexed[index].difference(all_walls_union)
            for index in new_group_indices
        ]
        for index in new_group_indices:
            all_elements_indexed.pop(index)
        # To avoid creating items that can go over the wall, we have to calculate the difference with the walls
        # on each line or polygon of the group. This specially to avoid water connections that are drawn as
        # lines in DXF
        rectangle = unary_union(new_group_geometries).minimum_rotated_rectangle
        if isinstance(rectangle, LineString):
            rectangle = rectangle.buffer(
                1e-6, join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.square
            )
        yield rectangle


def polygon_is_duplicated(existing_polygons: MultiPolygon, polygon: Polygon) -> bool:
    if not polygon.intersects(existing_polygons):
        return False
    pol_intersection = polygon.intersection(existing_polygons)
    if (
        pol_intersection.area / polygon.area
        < POLYGON_DUPLICATED_THRESHOLD_IN_PERCENTAGE
    ):
        return False

    return (
        polygon.difference(existing_polygons).area < POLYGON_DUPLICATED_THRESHOLD_IN_CM2
    )


def close_parallel_lines_into_polygons(
    line_strings: List[LineString], distance_threshold: float = 50
) -> Tuple[List[Polygon], List[LineString]]:
    new_polygons = []

    geos_lines = from_shapely(line_strings)
    for i, geos_line in enumerate(geos_lines):
        distances = distance(a=geos_line, b=geos_lines[i:])
        close_lines = [
            line_strings[index + i]
            for index in numpy.where(distances < distance_threshold)[0]
        ]
        for line_b in close_lines:
            line_a = line_strings[i]
            start_a, end_a = Point(line_a.coords[0]), Point(line_a.coords[-1])
            start_b, end_b = Point(line_b.coords[0]), Point(line_b.coords[-1])
            candidates = []
            if (
                start_a.distance(start_b) < distance_threshold
                and end_a.distance(end_b) < distance_threshold
            ):
                candidates = [
                    LineString([start_a, start_b]),
                    LineString([end_a, end_b]),
                ]
            elif (
                start_a.distance(end_b) < distance_threshold
                and start_b.distance(end_a) < distance_threshold
            ):
                candidates = [
                    LineString([start_a, end_b]),
                    LineString([start_b, end_a]),
                ]

            if candidates:
                result, dangles, cuts, invalids = polygonize_full(
                    candidates + [line_a, line_b]
                )
                new_polygons.extend([geom for geom in result.geoms])

    merged_polygons = unary_union(new_polygons)
    remaining_line_strings = [
        line for line in line_strings if not line.intersects(merged_polygons)
    ]
    polygons, leftovers = polygonize_full_lists(line_strings=remaining_line_strings)
    new_polygons.extend(polygons)

    return new_polygons, leftovers


def polygonize_full_lists(
    line_strings: List[LineString],
) -> Tuple[List[Polygon], List[LineString]]:
    new_polygons, dangles, cut_edges, _invalid_rings = polygonize_full(
        lines=line_strings
    )

    return [geom for geom in new_polygons.geoms], [
        geom for geom in chain(cut_edges.geoms, dangles.geoms)
    ]


def lines_to_polygons(line_strings: list[LineString], width: float):
    polygons = []
    for linestring in line_strings:
        polygon = add_width_to_linestring_improved(line=linestring, width=width)
        if not polygon.is_valid:
            continue
        polygons.append(polygon)
    return polygons


def filter_too_big_separators(separator_polygons: List[Polygon]) -> List[Polygon]:
    """This is generally due to the result of polygonize"""
    valid_separators = []
    for separator_polygon in separator_polygons:
        all_sides = get_sides_as_lines_by_length(polygon=separator_polygon)
        if (
            sum(
                1
                for side in all_sides
                if side.length > (THICKEST_WALL_POSSIBLE_IN_M * 100)
            )
            >= 3
        ):
            continue
        valid_separators.append(separator_polygon)
    return valid_separators


def merge_polygons_by_intersection(
    geos_polygons: list[Geometry], intersection_size: float = 10.0
) -> tuple[list[Geometry], bool]:
    for i, polygon in enumerate(geos_polygons):
        intersecting_pols_bool = intersects(
            polygon,
            geos_polygons,
        )
        if intersecting_pols_bool.sum() > 1:
            # here we could compute the intersection only of those that are positively intersecting
            intersections = intersection(polygon, geos_polygons)
            area_intersections = pygeos_areas(intersections)
            polygons_intersecting = [
                geos_polygons[index]
                for index in numpy.where(area_intersections > intersection_size)[0]
            ]
            if len(polygons_intersecting) > 1:
                new_polygon = minimum_rotated_rectangle(
                    geometry=multipolygons(geometries=polygons_intersecting + [polygon])
                )
                remaining_polygons = [
                    geos_polygons[index]
                    for index in numpy.where(area_intersections <= intersection_size)[0]
                    if index != i
                ]
                return remaining_polygons + [new_polygon], False
    return geos_polygons, True


def iteratively_merge_by_intersection(
    polygons: list[Polygon], intersection_size: float = 10.0
) -> list[Polygon]:
    finished = False
    geos_polygons = from_shapely(polygons)

    while not finished:
        geos_polygons, finished = merge_polygons_by_intersection(
            geos_polygons=geos_polygons, intersection_size=intersection_size
        )

    return list(to_shapely(geos_polygons))
