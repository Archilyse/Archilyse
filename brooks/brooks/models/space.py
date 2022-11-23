from typing import Optional, Set, Tuple

from shapely.geometry import Point, Polygon

from brooks.models.area import SimArea
from brooks.types import SeparatorType, SpaceType
from brooks.util.io import BrooksSerializable
from brooks.utils import get_default_element_lower_edge, get_default_element_upper_edge

from .spatial_entity import SpatialEntity


class SimSpace(SpatialEntity, BrooksSerializable):
    __serializable_fields__ = (
        "id",
        "type",
        "footprint",
        "children",
        "position",
        "angle",
    )

    def __init__(
        self,
        footprint: Polygon,
        space_id: Optional[str] = None,
        position: Optional[Point] = None,
        angle: Optional[float] = None,
        height: Optional[Tuple[float, float]] = None,
        areas: Optional[Set[SimArea]] = None,
    ):
        """initialisation of the object
        space_id (str, optional): Defaults to None. the space id
        """
        height = height or (
            get_default_element_lower_edge(SeparatorType.WALL),
            get_default_element_upper_edge(SeparatorType.WALL),
        )

        super().__init__(
            footprint=footprint,
            entity_id=space_id,
            position=position,
            angle=angle,
            height=height,
        )
        self._type = SpaceType.NOT_DEFINED
        self.areas: Set[SimArea] = areas or set()

    @property
    def children(self):
        return self.areas

    def add_area(self, area: SimArea):
        """add an areas to the space"""
        self.areas.add(area)

    def absolute_to_relative_coordinates(self, absolute_parent_position):
        self.footprint_absolute_to_relative_coordinates(absolute_parent_position)
        absolute_position = Point(
            absolute_parent_position.x + self.position.x,
            absolute_parent_position.y + self.position.y,
        )

        for area in self.areas:
            area.absolute_to_relative_coordinates(absolute_position)

    @property
    def features(self):
        return {feature for area in self.areas for feature in area.features}

    @property
    def has_toilet(self) -> bool:
        return any((area.has_toilet for area in self.areas))
