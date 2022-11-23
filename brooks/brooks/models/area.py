from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Optional, Set, Tuple

from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, Polygon
from shapely.ops import unary_union

from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from brooks.util.io import BrooksSerializable
from brooks.utils import get_default_element_lower_edge, get_default_element_upper_edge

from .spatial_entity import SpatialEntity

if TYPE_CHECKING:
    from brooks.models import SimFeature


class SimArea(SpatialEntity, BrooksSerializable):
    __serializable_fields__ = (
        "type",
        "id",
        "footprint",
        "height",
        "position",
        "angle",
        "children",
    )

    def __init__(
        self,
        footprint: Polygon,
        height: Optional[Tuple[float, float]] = None,
        area_id: Optional[str] = None,
        db_area_id: int = 0,  # FIXME: this can lead to errors depending on the external usage
        area_type: AreaType = AreaType.NOT_DEFINED,
    ):
        height = height or (
            get_default_element_lower_edge(SeparatorType.WALL),
            get_default_element_upper_edge(SeparatorType.WALL),
        )
        super().__init__(footprint=footprint, height=height, entity_id=area_id)
        self._type: AreaType = area_type
        self.features: Set[SimFeature] = set()
        self.db_area_id: int = db_area_id

    @property
    def children(self):
        return self.features

    def absolute_to_relative_coordinates(self, absolute_parent_position: Point):
        self.footprint_absolute_to_relative_coordinates(absolute_parent_position)
        absolute_position = Point(
            absolute_parent_position.x + self.position.x,
            absolute_parent_position.y + self.position.y,
        )

        for feature in self.features:
            feature.absolute_to_relative_coordinates(absolute_position)

    @cached_property
    def area_without_stairs(self) -> float:
        stairs = unary_union(
            [f.footprint for f in self.features if f.type is FeatureType.STAIRS]
        )
        return self.footprint.difference(stairs).area

    @property
    def has_toilet(self) -> bool:
        return FeatureType.TOILET in {feature.type for feature in self.features}

    @property
    def surface_area(self) -> float:
        return self.footprint.exterior.length * (self.height[1] - self.height[0])

    def wall_surface_area(self, layout) -> float:
        # NOTE: We are removing openings, railings, area_splitters
        #       from the surface area (i.e. cladding) of the area.
        wall_surface_area = self.surface_area
        for non_envelope_element in layout.openings | {
            separator
            for separator in layout.separators
            if separator.type in {SeparatorType.RAILING, SeparatorType.AREA_SPLITTER}
        }:
            intersection_length = self.footprint.exterior.intersection(
                non_envelope_element.footprint.buffer(
                    1e-6, join_style=JOIN_STYLE.mitre, cap_style=CAP_STYLE.square
                )
            ).length

            if intersection_length > 0:
                if non_envelope_element.type in OpeningType:
                    wall_surface_area -= (
                        non_envelope_element.height[1] - non_envelope_element.height[0]
                    ) * intersection_length
                else:
                    wall_surface_area -= (
                        self.height[1] - self.height[0]
                    ) * intersection_length

        return wall_surface_area
