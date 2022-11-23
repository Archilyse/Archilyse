import typing
from collections import defaultdict
from functools import cached_property
from math import isclose
from typing import Dict, List, Tuple, Union

from shapely.geometry import GeometryCollection, MultiPolygon, Point, Polygon
from shapely.ops import nearest_points, unary_union

from brooks.types import SeparatorType
from brooks.util.geometry_ops import (
    buffer_unbuffer_geometry,
    ensure_geometry_validity,
    round_geometry,
)
from common_utils.constants import BUFFERING_1CM, GEOMETRIES_PRECISION
from dufresne.polygon.utils import as_multipolygon
from handlers.editor_v2.schema import ReactPlannerData

LINE_EXTENSION = 1000
DISTANCE_1MM = 0.001


class ReactPlannerPostprocessor:
    def __init__(self, data: ReactPlannerData):
        self.data = data

    @cached_property
    def vertices_by_type_and_id(
        self,
    ) -> typing.DefaultDict[SeparatorType, Dict[str, List[Point]]]:
        vertices_by_line: typing.DefaultDict[
            SeparatorType, Dict[str, List[Point]]
        ] = defaultdict(lambda: defaultdict(list))
        for line in self.data.lines_iterator():
            for vertex_id in sorted(
                line.vertices,
                key=lambda v: (
                    self.data.vertices_by_id[v].x,
                    self.data.vertices_by_id[v].y,
                ),
            ):
                vertices_by_line[line.separator_type][line.id].append(
                    Point(
                        self.data.vertices_by_id[vertex_id].x,
                        self.data.vertices_by_id[vertex_id].y,
                    )
                )
        return vertices_by_line

    def process(
        self,
    ) -> Dict[SeparatorType, Tuple[List[Polygon], List[List[str]]]]:
        column_m_polygons, column_ids = self.post_process_react_planner_separator_type(
            separator_type=SeparatorType.COLUMN
        )
        wall_m_polygons, wall_ids = self.post_process_react_planner_separator_type(
            separator_type=SeparatorType.WALL
        )

        (
            railing_m_polygons,
            railing_ids,
        ) = self.post_process_react_planner_separator_type(
            separator_type=SeparatorType.RAILING
        )
        non_overlapped_railings = self.get_non_overlapped_railings(
            railing_polygons=railing_m_polygons,
            wall_polygons=wall_m_polygons,
            column_m_polygons=column_m_polygons,
        )
        new_railing_ids = self.get_line_ids_from_constructed_polygons(
            polygons=non_overlapped_railings,
            separator_type=SeparatorType.RAILING,
        )

        valid_walls = [
            valid_wall
            for polygon in wall_m_polygons.geoms
            for valid_wall in unrol_valid_geometries(geometry=polygon)
        ]

        valid_wall_ids = self.get_line_ids_from_constructed_polygons(
            polygons=valid_walls, separator_type=SeparatorType.WALL
        )

        return {
            SeparatorType.WALL: (valid_walls, valid_wall_ids),
            SeparatorType.COLUMN: (
                [pol for pol in column_m_polygons.geoms],
                column_ids,
            ),
            SeparatorType.RAILING: (non_overlapped_railings, new_railing_ids),
        }

    def post_process_react_planner_separator_type(
        self, separator_type: SeparatorType
    ) -> Tuple[MultiPolygon, List[List[str]]]:
        """Here we are discarding area splitters from all the lines"""

        unified_polygons = self.get_unary_union_of_plan_separators(
            separators_polygons=[
                polygon
                for polygon in self.data.separator_polygons_by_id(
                    separator_type=separator_type
                ).values()
            ]
        )

        unified_polygons = as_multipolygon(
            ensure_geometry_validity(geometry=unified_polygons)
        )

        match_line_ids_with_new_poly = self.get_line_ids_from_constructed_polygons(
            polygons=unified_polygons.geoms, separator_type=separator_type
        )
        return unified_polygons, match_line_ids_with_new_poly

    def get_line_ids_from_constructed_polygons(
        self, polygons: List[Polygon], separator_type: SeparatorType
    ) -> List[List[str]]:

        polygons_indexed = {i: polygon for i, polygon in enumerate(polygons)}
        line_points_by_line_id = self.vertices_by_type_and_id[separator_type]

        lines_ids_by_polygon_id = defaultdict(list)
        for line_id, line_points in line_points_by_line_id.items():
            polygon_id = self.id_matching_polygon(
                line_points=line_points, polygons_indexed=polygons_indexed
            ) or self.id_nearest_polygon(
                line_points=line_points, polygons_indexed=polygons_indexed
            )

            lines_ids_by_polygon_id[polygon_id].append(line_id)

        return [lines_ids_by_polygon_id[i] for i, _ in enumerate(polygons_indexed)]

    def id_matching_polygon(
        self, line_points: List[Point], polygons_indexed: Dict[int, Polygon]
    ) -> typing.Optional[int]:
        for polygon_id, polygon in polygons_indexed.items():
            if all(
                self.shapely_intersects_customized(
                    line_point, polygon, max_distance=0.01
                )
                for line_point in line_points
            ):
                return polygon_id
        return None

    def id_nearest_polygon(
        self, line_points: List[Point], polygons_indexed: Dict[int, Polygon]
    ) -> int:
        distances_to_polygons = []
        for polygon_id, polygon in polygons_indexed.items():
            distance = sum([point.distance(polygon) for point in line_points])
            distances_to_polygons.append((polygon_id, distance))

        return min(distances_to_polygons, key=lambda x: x[1])[0]

    def get_unary_union_of_plan_separators(
        self, separators_polygons: List[Polygon]
    ) -> MultiPolygon:
        unified_polygons = unary_union(
            self._round_geometries_before_unary_union(geometries=separators_polygons)
        )
        return round_geometry(
            as_multipolygon(
                buffer_unbuffer_geometry(
                    buffer=BUFFERING_1CM, geometry=unified_polygons
                )
            )
        )

    @staticmethod
    def shapely_intersects_customized(geom1, geom2, max_distance: float):
        return geom1.distance(geom2) < max_distance

    @staticmethod
    def get_non_overlapped_railings(
        railing_polygons: MultiPolygon,
        wall_polygons: MultiPolygon,
        column_m_polygons: MultiPolygon,
    ) -> List[Polygon]:
        final_polygons = []
        walls_and_columns = wall_polygons.union(column_m_polygons)
        if isclose(walls_and_columns.area, 0, abs_tol=1e-2):
            return railing_polygons.geoms
        for railing_polygon in as_multipolygon(
            railing_polygons.difference(wall_polygons)
        ).geoms:
            # due to precision problems, there could be tiny gaps left in between the railing and the wall
            # leading to all sort of problems with areas, so after the difference we extend the railing
            # exteriors closer to the wall until the wall line.
            modified_railing_polygon = extend_geometry_to_fill_gap_to_another_geom(
                geom_to_extend=railing_polygon, geom_reference=walls_and_columns
            )
            final_polygons.extend(
                unrol_valid_geometries(geometry=modified_railing_polygon)
            )

        return final_polygons

    @staticmethod
    def _round_geometries_before_unary_union(
        geometries: List[Polygon], precision: int = 7
    ) -> MultiPolygon:
        """
        Hack to avoid that the unary union is removing interiors due to some precision
        errors.
        """
        return round_geometry(MultiPolygon(geometries), precision=precision)


def extend_geometry_to_fill_gap_to_another_geom(
    geom_to_extend: Polygon,
    geom_reference: Polygon,
    distance_tolerance: float = DISTANCE_1MM,
) -> Polygon:
    new_points = []
    for exterior in geom_to_extend.exterior.coords[:]:
        exterior_p = Point(
            round(exterior[0], GEOMETRIES_PRECISION),
            round(exterior[1], GEOMETRIES_PRECISION),
        )
        distance_walls = exterior_p.distance(geom_reference)
        if 0.0 < distance_walls < distance_tolerance:
            near_point_wall = nearest_points(geom_reference, exterior_p)[0]
            new_points.append(near_point_wall)
        else:
            new_points.append(exterior_p)

    return ensure_geometry_validity(Polygon(new_points, holes=geom_to_extend.interiors))


def unrol_valid_geometries(
    geometry: Union[MultiPolygon, GeometryCollection, Polygon]
) -> List[Polygon]:
    final_polygons = []
    if isinstance(geometry, (MultiPolygon, GeometryCollection)):
        for sub_geometry in geometry:
            if sub_geometry.is_valid and sub_geometry.area > 0.0:
                final_polygons.append(sub_geometry)
    else:
        if geometry.is_valid and geometry.area > 0.0:
            final_polygons.append(geometry)
    return final_polygons
