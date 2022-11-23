import math
from itertools import combinations
from typing import Dict, List, Union

from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
)

from brooks.util.geometry_ops import get_line_strings
from common_utils.utils import pairwise


class CreateAreaSplitterFromSpaces:
    @staticmethod
    def _get_space_borders(
        separators: MultiPolygon, spaces_by_id: Dict[int, Polygon]
    ) -> List[Union[LineString, MultiLineString]]:
        """
        Detects borders between spaces and returns the line strings separating each border, so that they could be
        directly used later to create area splitters.
        """

        spaces_buffered = {
            space_id: space.buffer(  # make those spaces thicker so that there are as many potential space overlaps
                distance=1, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
            )
            for (space_id, space) in spaces_by_id.items()
        }
        # erode buffered spaces with separators to get spaces that may only overlap with each other
        spaces_buffered_eroded = {
            space_id: space_buffered.difference(
                separators.buffer(
                    distance=1e-2,
                    cap_style=CAP_STYLE.square,
                    join_style=JOIN_STYLE.mitre,
                )
            )
            for space_id, space_buffered in spaces_buffered.items()
        }
        space_borders: List[Union[LineString, MultiLineString]] = []
        for (space_a_id, space_a), (space_b_id, space_b) in combinations(
            spaces_buffered_eroded.items(), 2
        ):
            if space_a.intersects(space_b):
                space_overlap: Polygon = space_a.intersection(space_b)
                # here we're checking if there's a nested area within another - if so we need the exterior of the former
                # because we need to ensure that intersection of space_overlap with selected space exterior produces a
                # valid line for the area splitter
                space_exterior = (
                    spaces_by_id[space_a_id].exterior
                    if space_a.within(space_b)
                    else spaces_by_id[space_b_id].exterior
                )
                area_splitter = space_exterior.intersection(space_overlap)
                space_borders.append(area_splitter)
        return space_borders

    @classmethod
    def create_area_splitters(
        cls, separators: MultiPolygon, spaces: List[Polygon]
    ) -> List[Polygon]:
        spaces_indexed = {space_id: polygon for space_id, polygon in enumerate(spaces)}
        space_borders: List[
            Union[MultiLineString, LineString]
        ] = cls._get_space_borders(separators=separators, spaces_by_id=spaces_indexed)

        space_boundary_lines: List[LineString] = [
            linestring
            for space_border in space_borders
            for linestring in get_line_strings(space_border)
        ]

        # complex lines need to be simplified by breaking them down to (x, y) pairs so that each is just a straight line
        # and so that then those simple lines can be correctly converted to area splitter polygons
        space_boundary_lines_split: List[LineString] = [
            LineString([coord_a, coord_b])
            for linestring in space_boundary_lines
            for coord_a, coord_b in pairwise(linestring.coords[:])
            if Point(coord_a).distance(Point(coord_b)) > 0.1
        ]

        space_boundaries_polygonized: List[Polygon] = [
            line.buffer(0.1, join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.square)
            for line in space_boundary_lines_split
        ]
        area_splitters: List[Polygon] = [
            b
            for b in space_boundaries_polygonized
            if not math.isclose(b.area, 0, abs_tol=1e-3)
        ]
        return area_splitters
