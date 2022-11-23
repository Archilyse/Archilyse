from typing import TYPE_CHECKING, List, Optional, Tuple, Union

from methodtools import lru_cache
from shapely.geometry import LineString, MultiLineString, Point, Polygon

from brooks.types import OpeningSubType, OpeningType
from brooks.util.io import BrooksSerializable
from brooks.utils import get_default_element_lower_edge, get_default_element_upper_edge
from dufresne.polygon import get_polygon_from_pos_dim_angle
from dufresne.polygon.parameters_minimum_rotated_rectangle import (
    get_parameters_of_minimum_rotated_rectangle,
)
from dufresne.polygon.polygon_get_rectangular_side_vectors import (
    get_parallel_side_lines_to_reference_line,
)

from .spatial_entity import SpatialEntity

if TYPE_CHECKING:
    from brooks.models import SimSeparator
    from handlers.editor_v2.schema import ReactPlannerHoleProperties


class SimOpening(SpatialEntity, BrooksSerializable):
    """An opening is an opening like a door or a window belonging to an area"""

    __serializable_fields__ = (
        "type",
        "id",
        "footprint",
        "height",
        "position",
        "angle",
    )

    def __init__(
        self,
        footprint: Polygon,
        height: Tuple[float, float],
        separator: "SimSeparator",
        separator_reference_line: LineString,
        opening_id: Optional[str] = None,
        opening_type: OpeningType = OpeningType.NOT_DEFINED,
        editor_properties: Optional["ReactPlannerHoleProperties"] = None,
        sweeping_points: Optional[List[Point]] = None,
        opening_sub_type: Optional[OpeningSubType] = None,
        geometry_new_editor: Optional[Polygon] = None,
    ):
        """
        sweeping_points are describing the door opening direction and hinge of a door.
        Point 0: Door Hinge
        Point 1: closed door
        Point 2: open door

        ^ 2
        .   .
        .      .
        .        .
        0........>1

        """
        height = height or (
            get_default_element_lower_edge(opening_type),
            get_default_element_upper_edge(opening_type),
        )
        super().__init__(
            footprint=footprint,
            height=height,
            entity_id=opening_id,
            geometry_new_editor=geometry_new_editor,
        )
        self.separator_reference_line = separator_reference_line
        self._type = opening_type
        self.separator: "SimSeparator" = separator
        self.sweeping_points = sweeping_points
        self.opening_sub_type = opening_sub_type
        self.editor_properties = editor_properties

    def absolute_to_relative_coordinates(self, absolute_parent_position):
        self.footprint_absolute_to_relative_coordinates(absolute_parent_position)

    @property
    def is_door(self) -> bool:
        return self.type in {OpeningType.DOOR, OpeningType.ENTRANCE_DOOR}

    @property
    def is_entrance(self) -> bool:
        return self.type == OpeningType.ENTRANCE_DOOR

    def apply_georef(self, georeferencing_transformation):
        if self.sweeping_points:
            self.sweeping_points = [
                georeferencing_transformation.apply_shapely(point)
                for point in self.sweeping_points
            ]

        if self.separator_reference_line:
            self.separator_reference_line = georeferencing_transformation.apply_shapely(
                self.separator_reference_line
            )

        super().apply_georef(
            georeferencing_transformation=georeferencing_transformation
        )

    @property
    def mid_height_point(self) -> float:
        total_height = self.height[1] - self.height[0]
        return self.height[0] + total_height / 2.0

    @lru_cache()
    def reference_geometry(
        self,
    ) -> Union[MultiLineString, Polygon]:
        """
        Reference geometry to be used when mapping the opening to areas or spaces
        """
        # if the opening footprint has been postprocessed, it could have more than 4 sides, here
        # we convert it to the minimum rotated rectangle in all cases
        rectangle = self.footprint.minimum_rotated_rectangle
        return get_parallel_side_lines_to_reference_line(
            rectangle=rectangle,
            reference_line=self.separator_reference_line,
            offset_in_pct=0.1,
        )

    @classmethod
    def adjust_geometry_to_wall(
        cls, opening: Polygon, wall: Polygon, buffer_width: Optional[float] = None
    ) -> Polygon:
        """Adjust opening to the separator it belongs to prevent the opening from not
        covering completely the separator.
        This is a legacy method used in the old editor, still used for the ifc import.
        """
        opening_intersection = opening.intersection(wall)

        (
            _,
            _,
            _,
            wall_width,
            wall_angle,
        ) = get_parameters_of_minimum_rotated_rectangle(
            polygon=wall,
            rotation_axis_convention="lower_left",
            return_annotation_convention=False,
        )
        if isinstance(opening_intersection, LineString):
            # if they intersect only in the border
            opening_intersection = opening_intersection.buffer(0.01)

        _, _, opening_length, _, _ = get_parameters_of_minimum_rotated_rectangle(
            polygon=opening_intersection,
            rotation_axis_convention="lower_left",
            return_annotation_convention=False,
        )
        new_opening_polygon = get_polygon_from_pos_dim_angle(
            opening_intersection.centroid.coords[0],
            (wall_width * 2, opening_length),  # Makes it extra wide
            -(wall_angle - 90),
            centroid=True,
        )
        new_opening_polygon = new_opening_polygon.intersection(
            wall  # Get again intersection after making it extra wide
        )
        if buffer_width:
            new_opening_polygon = get_polygon_from_pos_dim_angle(
                new_opening_polygon.centroid.coords[0],
                (wall_width * buffer_width, opening_length),  # Buffer width
                -(wall_angle - 90),
                centroid=True,
            )
        return new_opening_polygon
