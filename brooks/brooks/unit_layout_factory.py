from typing import Any, List, Optional, Set

from pygeos import buffer, from_shapely, intersection, intersects, to_shapely, union_all
from shapely.ops import unary_union

from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from dufresne.polygon.utils import as_multipolygon


class UnitLayoutFactory:
    def __init__(self, plan_layout: SimLayout):
        self.plan_layout = plan_layout

    def create_sub_layout(
        self,
        spaces_ids: Set[str],
        area_db_ids: Any = None,
        floor_number: int = 0,
        public_space: bool = False,
    ) -> SimLayout:
        """
        Creates a new layout based on a subset of spaces ids of the layout.
        New separators, openings and features will be generated based on originals
        """
        unit_layout = SimLayout(floor_number=floor_number)

        spaces_to_keep = {
            space for space in self.plan_layout.spaces if space.id in spaces_ids
        }

        self._copy_spaces_and_areas_to_sub_layout(
            spaces_to_keep=spaces_to_keep,
            unit_layout=unit_layout,
            areas_to_keep=area_db_ids,
        )
        self._copy_separators_openings_features_to_sub_layout(
            unit_layout=unit_layout, public_space=public_space
        )
        return unit_layout

    def _copy_separators_openings_features_to_sub_layout(
        self, unit_layout: SimLayout, public_space: bool
    ) -> None:
        """Copy separators, openings and layout based on the spaces of the sub_layout
        provided into it
        """
        union_spaces_buffered = unit_layout.get_spaces_union(
            spaces=unit_layout.areas, public_space=public_space
        )
        union_spaces_no_buffer = union_all(
            from_shapely([space.footprint for space in unit_layout.spaces])
        )
        separator_list = list(self.plan_layout.separators)
        separator_intersects_indexes = intersects(
            buffer(
                from_shapely([sep.footprint for sep in separator_list]),
                radius=0.1,
                cap_style="square",
                join_style="mitre",
            ),
            union_spaces_no_buffer,
        )
        separator_intersections_indexes = intersection(
            from_shapely([sep.footprint for sep in separator_list]),
            from_shapely(union_spaces_buffered),
        )
        for index, separator in enumerate(separator_list):
            if separator_intersects_indexes[index]:
                # NOTE: here we are cutting the original separator such that it does not extend
                # more than the buffered union of all spaces. This is important not to
                # block windows of other units.
                cut_separator_footprint = to_shapely(
                    separator_intersections_indexes[index]
                )

                new_separators = [
                    SimSeparator(
                        footprint=polygon,
                        height=separator.height,
                        separator_type=separator.type,
                        editor_properties=separator.editor_properties,
                    )
                    for polygon in as_multipolygon(cut_separator_footprint).geoms
                ]
                # We have to copy new openings where the reference parent/child is correct
                for opening in separator.openings:
                    for new_separator in new_separators:
                        if self._copy_opening_to_separator(
                            opening=opening, new_separator=new_separator
                        ):
                            break

                unit_layout.separators.update(new_separators)

    @staticmethod
    def _copy_opening_to_separator(
        opening: SimOpening, new_separator: SimSeparator, overlap_threshold: float = 0.6
    ) -> bool:
        if opening.footprint.intersects(new_separator.footprint):
            opening_intersection = opening.footprint.intersection(
                new_separator.footprint
            )
            # The following check is to make sure we don't assign openings to a unit layout when the opening
            # it is just slightly intersecting the unit layout separators
            if (
                opening_intersection.area / opening.footprint.area
            ) >= overlap_threshold:
                new_opening = SimOpening(
                    footprint=opening.footprint,
                    height=opening.height,
                    opening_id=opening.id,
                    opening_type=opening.type,
                    separator=new_separator,
                    sweeping_points=opening.sweeping_points,
                    separator_reference_line=opening.separator_reference_line,
                    geometry_new_editor=opening.geometry_new_editor,
                )
                new_separator.add_opening(new_opening)
                return True
        return False

    @staticmethod
    def _copy_spaces_and_areas_to_sub_layout(
        spaces_to_keep: Set[SimSpace],
        unit_layout: SimLayout,
        areas_to_keep: Optional[List[Set[int]]] = None,
    ) -> None:
        for space in spaces_to_keep:
            new_space = SimSpace(
                space_id=space.id,
                footprint=space.footprint,
                height=space.height,
            )
            for area in space.areas:
                if areas_to_keep and area.db_area_id not in areas_to_keep:
                    continue
                new_area = SimArea(
                    footprint=area.footprint,
                    height=area.height,
                    area_id=area.id,
                    area_type=area.type,
                    db_area_id=area.db_area_id,
                )
                # TODO: redefine all the features to avoid using the same object in different layouts.
                new_area.features.update(area.features)
                new_space.add_area(new_area)
            if {area.id for area in space.areas}.difference(
                {area.id for area in new_space.areas}
            ):

                new_space.footprint = unary_union(
                    [area.footprint for area in new_space.areas]
                )

            unit_layout.spaces.add(new_space)
