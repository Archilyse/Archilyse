from typing import Iterator, List, Tuple

from shapely.affinity import rotate
from shapely.geometry import JOIN_STYLE, LineString, MultiPolygon, Point, Polygon
from shapely.ops import nearest_points

from common_utils.logger import logger
from common_utils.utils import pairwise
from dufresne.linestring_add_width import (
    LINESTRING_EXTENSION,
    add_width_to_linestring_improved,
)
from dufresne.polygon import get_sides_as_lines_by_length
from handlers.dxf.dxf_constants import (
    DISTANCE_TO_DISCARD_DOOR_ARC_LINES_ASSOCIATION,
    SNAP_DOOR_TO_WALL_THRESHOLD_IN_CM,
)
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_mapper import DXFtoShapelyMapper
from handlers.editor_v2.schema import ReactPlannerDoorSweepingPoints, ReactPlannerName
from handlers.shapely_to_react.editor_ready_entity import (
    EditorReadyEntity,
    EntityProperties,
)


class DXFToShapelyDoorMapper:
    @classmethod
    def get_door_entities(
        cls,
        dxf_to_shapely_mapper: DXFtoShapelyMapper,
        reference_walls: List[Polygon],
        layers: set[str] | None = None,
        block_names: set[str] | None = None,
    ):
        if layers is None:
            layers = dxf_to_shapely_mapper.get_layer_names(
                react_planner_names={
                    ReactPlannerName.DOOR,
                    ReactPlannerName.ENTRANCE_DOOR,
                }
            )

        if block_names is None:
            block_names = dxf_to_shapely_mapper.get_block_names(
                react_planner_names={
                    ReactPlannerName.DOOR,
                    ReactPlannerName.ENTRANCE_DOOR,
                }
            )

        return [
            EditorReadyEntity(
                geometry=door_polygon,
                properties=EntityProperties(
                    door_sweeping_points=cls._create_sweeping_points(
                        axis_point=adjusted_axis_point,
                        closed_point=adjusted_closing_point,
                        extension_type=extension_type,
                        door_width=door_width,
                    )
                ),
            )
            for (
                door_polygon,
                adjusted_axis_point,
                adjusted_closing_point,
                extension_type,
                door_width,
            ) in cls.get_door_geometries_from_arc_and_line(
                dxf_to_shapely_mapper=dxf_to_shapely_mapper,
                reference_walls=reference_walls,
                layers=layers,
                block_names=block_names,
            )
        ]

    @classmethod
    def get_door_geometries_from_arc_and_line(
        cls,
        dxf_to_shapely_mapper: DXFtoShapelyMapper,
        reference_walls: List[Polygon],
        layers: set[str],
        block_names: set[str],
    ) -> Iterator[tuple[Polygon, Point, Point, LINESTRING_EXTENSION, float]]:
        for arc, line in cls._group_arcs_and_lines(
            dxf_to_shapely_mapper=dxf_to_shapely_mapper,
            layers=layers,
            block_names=block_names,
        ):
            opening_point, closing_point = cls._get_arc_opening_and_closing_points(
                arc=arc, line=line
            )

            axis_point = cls._get_axis_point(arc=arc, line=line)

            adjusted_closing_point: Point = cls._snap_point_to_nearest_wall(
                point=closing_point, walls=reference_walls
            )
            adjusted_axis_point: Point = cls._snap_point_to_nearest_wall(
                point=axis_point, walls=reference_walls
            )
            door_width = cls._get_door_width(
                reference_wall=cls._nearest_wall_to_point(
                    point=axis_point, walls=reference_walls
                )
            )
            extension_type: LINESTRING_EXTENSION = cls._get_extension_type(
                axis_point=axis_point,
                closing_point=closing_point,
                opening_point=opening_point,
            )
            door_step_line = LineString([adjusted_axis_point, adjusted_closing_point])
            door_polygon: Polygon = add_width_to_linestring_improved(
                line=door_step_line,
                width=door_width,
                extension_type=extension_type,
            )
            yield (
                door_polygon,
                adjusted_axis_point,
                adjusted_closing_point,
                extension_type,
                door_width,
            )

    @classmethod
    def _group_arcs_and_lines(
        cls,
        dxf_to_shapely_mapper: DXFtoShapelyMapper,
        layers: set[str],
        block_names: set[str],
    ) -> Iterator[Tuple[LineString, LineString]]:

        arcs = []
        for block_name in block_names:
            arcs += dxf_to_shapely_mapper.get_dxf_geometries(
                allowed_layers=layers,
                allowed_geometry_types={"ARC"},
                block_name_prefix=block_name,
            )

        # we only use the raw layers if the blocks are not being used
        if not arcs:
            arcs = dxf_to_shapely_mapper.get_dxf_geometries(
                allowed_layers=layers, allowed_geometry_types={"ARC"}
            )

        lines, polygon_to_avoid = cls._get_lines_for_doors(
            dxf_to_shapely_mapper=dxf_to_shapely_mapper,
            layers=layers,
            block_names=block_names,
        )
        arcs = [arc for arc in arcs if not arc.intersects(polygon_to_avoid)]
        if not len(arcs) == len(lines):
            logger.debug(
                "Error when creating doors from arcs and lines: Number of arcs not matching with number of lines"
            )

        for arc in arcs:
            nearest_line = sorted(
                [(line, arc.distance(line)) for line in lines],
                key=lambda pair: pair[1],
            )[0][0]
            if (
                nearest_line.distance(arc)
                < DISTANCE_TO_DISCARD_DOOR_ARC_LINES_ASSOCIATION
            ):
                yield arc, nearest_line

    @classmethod
    def _get_lines_for_doors(
        cls,
        dxf_to_shapely_mapper: DXFtoShapelyMapper,
        layers: set[str],
        block_names: set[str],
    ) -> Tuple[List[LineString], MultiPolygon]:
        """
        Some users use Polylines to represent a line with 2 points so we include the type but at the same
        time we need to exclude polylines which have more than 2 points as they are not fitting into
        how we create doors
        """
        dxf_lines = []
        for block_name in block_names:
            dxf_lines += dxf_to_shapely_mapper.get_dxf_geometries(
                allowed_layers=layers,
                allowed_geometry_types={"LINE"},
                block_name_prefix=block_name,
            )

        # we only use the raw layers if the blocks are not being used
        if not dxf_lines:
            dxf_lines = dxf_to_shapely_mapper.get_dxf_geometries(
                allowed_layers=layers,
                allowed_geometry_types={"LINE"},
            )

        lines = []
        for line in dxf_lines:
            if not line.length:
                continue
            if len(line.coords) == 2:
                lines.append(line)
            elif len(line.coords) > 2:
                for points in pairwise(line.coords[:]):
                    lines.append(LineString(points))

        door_polygons_to_avoid = []
        for block_name in block_names:
            door_polygons_to_avoid += dxf_to_shapely_mapper.get_dxf_geometries(
                allowed_layers=layers,
                allowed_geometry_types={"LWPOLYLINE"},
                block_name_prefix=block_name,
            )

        # we only use the raw layers if the blocks are not being used
        if not door_polygons_to_avoid:
            door_polygons_to_avoid = dxf_to_shapely_mapper.get_dxf_geometries(
                allowed_layers=layers,
                allowed_geometry_types={"LWPOLYLINE"},
            )

        door_polygons_to_avoid = [
            pol
            for pol in door_polygons_to_avoid
            if isinstance(pol, (Polygon, MultiPolygon))
        ]

        return lines, MultiPolygon(door_polygons_to_avoid)

    @staticmethod
    def _get_door_width(reference_wall: Polygon) -> float:
        return get_sides_as_lines_by_length(reference_wall)[0].length

    @staticmethod
    def _get_extension_type(
        axis_point: Point, closing_point: Point, opening_point: Point
    ) -> LINESTRING_EXTENSION:
        """
        v1 is representing the opening line. If the opening point is on the left side we need to extend to the right side and vice versa.
        To determine on which side the opening point is we can use the cross product between v1 and v2. A positive cross product corresponds to
        the opening beeing on the left side.


        v2
        ^
        .
        .
        .
        .
        .---------------> v1


        """
        v1 = (closing_point.x - axis_point.x, closing_point.y - axis_point.y)
        v2 = (opening_point.x - axis_point.x, opening_point.y - axis_point.y)
        cross_product = v1[0] * v2[1] - v1[1] * v2[0]
        if cross_product > 0:
            return LINESTRING_EXTENSION.RIGHT
        else:
            return LINESTRING_EXTENSION.LEFT

    @staticmethod
    def _get_arc_opening_and_closing_points(
        arc: LineString, line: LineString
    ) -> Tuple[Point, Point]:
        points_sorted_by_distance = sorted(
            arc.coords,
            key=lambda coord: Point(coord).distance(line),
        )
        return (
            Point(points_sorted_by_distance[0]),
            Point(points_sorted_by_distance[-1]),
        )

    @staticmethod
    def _get_axis_point(arc: LineString, line: LineString) -> Point:
        return Point(
            sorted(
                line.coords,
                key=lambda coord: Point(coord).distance(arc),
                reverse=True,
            )[0]
        )

    @classmethod
    def _snap_point_to_nearest_wall(cls, point: Point, walls: List[Polygon]) -> Point:
        nearest_point = nearest_points(MultiPolygon(walls), point)[0]
        if nearest_point.distance(point) < SNAP_DOOR_TO_WALL_THRESHOLD_IN_CM:
            return nearest_point
        else:
            return point

    @staticmethod
    def _nearest_wall_to_point(point: Point, walls: List[Polygon]) -> Polygon:
        return sorted(walls, key=lambda wall: wall.distance(point))[0]

    @classmethod
    def _create_sweeping_points(
        cls,
        axis_point: Point,
        closed_point: Point,
        extension_type: LINESTRING_EXTENSION,
        door_width: float,
    ) -> ReactPlannerDoorSweepingPoints:
        """
        From the dxf arc & line we directly get the axis, closed and opening points but we can not use them as the sweeping points directly for 2 reasons:
        1. The axis, closed point input arguments were snapped to the nearest walls so we have to recompute the opening point from them
        2. In the react editor we have defined the axis and closed point in the middle of the door step geometry whereas in the dxf they are defined at the boundaries

        dxf definition                                         React Editor definition

                          | Opening Point                                         | Opening Point
                          |                                                       |
                          |                                                       |
                          |                                                       |
        Axis...............Closing Point                        ...................
        |                 |                                     |                 |
        |                 |                                     Axis              Closing Point
        |                 |                                     |                 |
        ..................                                      ...................



        """

        axis_point, closed_point = cls._shift_axis_and_closing_point_to_middle_of_door(
            axis_point=axis_point,
            closed_point=closed_point,
            door_width=door_width,
            extension_type=extension_type,
        )
        opened_point = Point(
            rotate(
                geom=LineString([axis_point, closed_point]),
                angle=90 if extension_type == LINESTRING_EXTENSION.RIGHT else -90,
                origin=axis_point,
            ).coords[1]
        )

        return ReactPlannerDoorSweepingPoints(
            angle_point=[axis_point.x, axis_point.y],
            closed_point=[closed_point.x, closed_point.y],
            opened_point=[opened_point.x, opened_point.y],
        )

    @staticmethod
    def _shift_axis_and_closing_point_to_middle_of_door(
        axis_point: Point,
        closed_point: Point,
        extension_type: LINESTRING_EXTENSION,
        door_width: float,
    ) -> Tuple[Point, Point]:

        shifted_points = [
            coord
            for coord in LineString([axis_point, closed_point])
            .parallel_offset(
                distance=door_width * 0.5,
                side="right"
                if extension_type == LINESTRING_EXTENSION.RIGHT
                else "left",
                join_style=JOIN_STYLE.mitre,
                mitre_limit=door_width,
            )
            .coords
        ]

        axis_point, closed_point = (
            (shifted_points[0], shifted_points[1])
            if extension_type == LINESTRING_EXTENSION.LEFT
            else (shifted_points[1], shifted_points[0])
        )  # shapely parallel offset changes order for "right" extension

        return Point(axis_point), Point(closed_point)
