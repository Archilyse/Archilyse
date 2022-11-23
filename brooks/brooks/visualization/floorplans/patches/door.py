from enum import Enum
from functools import cached_property
from math import atan2
from typing import Dict, List, Optional, Set, Union

from matplotlib.patches import PathPatch
from matplotlib.patches import Polygon as PolygonPatch
from matplotlib.path import Path
from numpy import array, pi
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import orient

from brooks.models import SimArea

from .feature import Triangle


class DoorStepPatch(PolygonPatch):
    def __init__(self, door: Polygon, **kwargs):
        super().__init__(array(door.exterior.coords), **kwargs)


class EntranceDoorFlagPatch(Triangle):
    def __init__(
        self,
        xy: array,
        angle: float,
        arrow_length: float = 0.20,
        side_length: float = 0.20,
        **kwargs,
    ):
        super().__init__(xy, angle, arrow_length, side_length, **kwargs)


class DoorArcPatch(PathPatch):
    def __init__(self, closed1: array, closed2: array, open2: array, **kwargs):
        ctrl = open2 + closed2 - closed1
        path = Path(
            vertices=[closed1, closed2, ctrl, open2, closed1],
            codes=[Path.MOVETO, Path.LINETO, Path.CURVE3, Path.CURVE3, Path.CLOSEPOLY],
            closed=True,
        )
        super().__init__(path, fill=False, **kwargs)


class DoorOpeningDirection(Enum):
    DOWN = 1
    UP = 2


class DoorPatches:
    """

                    *
                    opening2
                    *
                    *
    D***************cd***************C
    *                                *
    *                                *
    da                               bc
    *                                *
    *                                *
    A***************ab***************B
                    *
                    *
                    opening1
                    *


    """

    def __init__(
        self,
        door: Polygon,
        connecting_areas: List[SimArea],
        public_area_ids: Set[int],
        unit_db_area_ids: Set[int],
        is_entrance: bool = False,
        sweeping_points: Optional[List[Point]] = None,
        is_sliding: bool = False,
    ):
        self.door = door
        self.connecting_areas = connecting_areas
        self.is_entrance = is_entrance
        self.public_area_ids = public_area_ids
        self.unit_db_area_ids = unit_db_area_ids
        self.sweeping_points = sweeping_points
        self.is_sliding = is_sliding
        self.connected_public_area_ids = [
            a.db_area_id
            for a in self.connecting_areas
            if a.db_area_id in public_area_ids
        ]
        self.connected_unit_area_ids = [
            a.db_area_id
            for a in self.connecting_areas
            if a.db_area_id in unit_db_area_ids
        ]
        door_step_patch = DoorStepPatch(
            door=self.door,
        )
        self.patches: List[
            Union[DoorStepPatch, EntranceDoorFlagPatch, DoorArcPatch]
        ] = [door_step_patch]

    def create_entrance_flag(self) -> List[EntranceDoorFlagPatch]:
        if self.door_opening_direction == DoorOpeningDirection.DOWN:
            flag_direction = DoorOpeningDirection.UP
        else:
            flag_direction = DoorOpeningDirection.DOWN

        point = self._door_center_line_direction(direction=flag_direction).centroid
        angle = self.get_angle_from_linestring(
            LineString(self.directed_points[flag_direction])
        )
        return [
            EntranceDoorFlagPatch(
                (point.x, point.y),
                angle=angle + 90,
            )
        ]

    @cached_property
    def door_opening_direction(self) -> DoorOpeningDirection:
        space_door_should_open_into: Union[
            SimArea, None
        ] = self._space_door_should_open_into()

        if space_door_should_open_into is None:
            return DoorOpeningDirection.UP

        direction_intersections = [
            direction
            for direction in DoorOpeningDirection
            if space_door_should_open_into.footprint.intersects(
                self._door_center_line_direction(direction=direction)
            )
        ]

        if not direction_intersections:
            return DoorOpeningDirection.UP

        return direction_intersections[0]

    def _door_center_line_direction(self, direction: DoorOpeningDirection):
        # The central point of the door polygon is required to avoid intersecting issues when
        # the door takes the entire width of the space like in corridors.
        center_point = LineString(self.directed_points[direction]).centroid
        open_wing = LineString(
            [
                center_point,
                (
                    center_point.x
                    + self._normalised_opening_direction(direction=direction).x,
                    center_point.y
                    + self._normalised_opening_direction(direction=direction).y,
                ),
            ]
        )
        return open_wing

    def _space_door_should_open_into(self) -> Union[SimArea, None]:
        if len(self.connecting_areas) == 1:
            # Main building door has only 1 connecting area
            return self.connecting_areas[0]

        if unit_areas := [
            area
            for area in self.connecting_areas
            if area.db_area_id in self.connected_unit_area_ids
        ]:
            return unit_areas[0]
        return None

    def _normalised_opening_direction(self, direction: DoorOpeningDirection) -> Point:
        points_of_rectangle = self.abcd_points
        angle_point = points_of_rectangle[0]
        point_before_angle_point = points_of_rectangle[3]
        point = Point(
            (angle_point.x - point_before_angle_point.x) / self.opening_width,
            (angle_point.y - point_before_angle_point.y) / self.opening_width,
        )

        if direction is DoorOpeningDirection.DOWN:
            return point
        return Point(-point.x, -point.y)

    @cached_property
    def abcd_points(self) -> List[Point]:
        """Description at class level"""
        door_bounding_box = self.door.minimum_rotated_rectangle
        oriented_rectangle = orient(geom=door_bounding_box, sign=1)
        shapely_points = [Point(coord) for coord in oriented_rectangle.exterior.coords]
        if shapely_points[0].distance(shapely_points[1]) < shapely_points[1].distance(
            shapely_points[2]
        ):
            return [
                shapely_points[1],
                shapely_points[2],
                shapely_points[3],
                shapely_points[0],
            ]

        return shapely_points

    @cached_property
    def directed_points(self) -> Dict[DoorOpeningDirection, List[Point]]:
        return {
            DoorOpeningDirection.UP: self.abcd_points[2:4],
            DoorOpeningDirection.DOWN: self.abcd_points[0:2],
        }

    @cached_property
    def opening_length(self) -> float:
        return self.abcd_points[0].distance(self.abcd_points[1])

    @cached_property
    def opening_width(self) -> float:
        return self.abcd_points[1].distance(self.abcd_points[2])

    @staticmethod
    def get_angle_from_linestring(linestring: LineString) -> float:
        coord1, coord2 = list(linestring.coords)
        dx = coord2[0] - coord1[0]
        dy = coord2[1] - coord1[1]
        return atan2(dy, dx) * 360 / (2 * pi)

    def create_door_patches(self) -> List[Union[DoorStepPatch, EntranceDoorFlagPatch]]:
        entrance_door_within_floor = len(self.connected_public_area_ids) == 2
        if self.is_entrance and not entrance_door_within_floor:
            self.patches.extend(self.create_entrance_flag())

        if self.sweeping_points and not self.is_sliding:
            self.patches.extend(
                [
                    DoorArcPatch(
                        closed1=array(self.sweeping_points[0].coords).flatten(),
                        closed2=array(self.sweeping_points[1].coords).flatten(),
                        open2=array(self.sweeping_points[2].coords).flatten(),
                    )
                ]
            )

        return self.patches
