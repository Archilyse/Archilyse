from typing import TYPE_CHECKING, Optional, Set, Tuple

from shapely.geometry import LineString, Point, Polygon

from brooks.types import SeparatorType
from brooks.util.io import BrooksSerializable
from brooks.utils import get_default_element_lower_edge, get_default_element_upper_edge

from .spatial_entity import SpatialEntity

if TYPE_CHECKING:
    from brooks.models import SimOpening
    from handlers.editor_v2.schema import ReactPlannerLineProperties


class BaseSeparator(SpatialEntity, BrooksSerializable):
    """A separator separates spaces from each other"""

    __serializable_fields__ = (
        "type",
        "id",
        "footprint",
        "height",
        "children",
        "position",
        "angle",
    )

    def __init__(
        self,
        footprint: Polygon,
        height: Tuple[float, float] = None,
        separator_id: Optional[str] = None,
        separator_type: SeparatorType = SeparatorType.NOT_DEFINED,
        editor_properties: Optional["ReactPlannerLineProperties"] = None,
    ):
        height = height or (
            get_default_element_lower_edge(separator_type),
            get_default_element_upper_edge(separator_type),
        )
        super().__init__(
            footprint=footprint,
            height=height,
            entity_id=separator_id,
        )
        self._type = separator_type
        self.openings: Set[SimOpening] = set()
        self.editor_properties = editor_properties

    def add_opening(self, opening: "SimOpening"):
        """add an opening to the existing openings"""
        self.openings.add(opening)

    @property
    def children(self):
        return self.openings

    def absolute_to_relative_coordinates(self, absolute_parent_position):
        self.footprint_absolute_to_relative_coordinates(absolute_parent_position)
        absolute_position = Point(
            absolute_parent_position.x + self.position.x,
            absolute_parent_position.y + self.position.y,
        )
        for opening in self.openings:
            opening.absolute_to_relative_coordinates(absolute_position)

    @property
    def surface_area(self) -> float:
        surface_area = SpatialEntity.surface_area.fget(self)  # type: ignore
        for opening in self.openings:
            surface_area -= opening.surface_area
        return surface_area


class SimSeparator(BaseSeparator):
    def __init__(
        self,
        footprint: Polygon,
        separator_type: SeparatorType,
        editor_properties: Optional["ReactPlannerLineProperties"] = None,
        reference_linestring: Optional[LineString] = None,
        height: Optional[Tuple[float, float]] = None,
        separator_id: Optional[str] = None,
    ):

        super(SimSeparator, self).__init__(
            footprint=footprint,
            height=height
            or (
                get_default_element_lower_edge(separator_type),
                get_default_element_upper_edge(separator_type),
            ),
            separator_id=separator_id,
            separator_type=separator_type,
            editor_properties=editor_properties,
        )

    @property
    def is_wall(self) -> bool:
        return self.type is SeparatorType.WALL
