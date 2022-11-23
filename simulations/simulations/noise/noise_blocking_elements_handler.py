from collections import defaultdict
from typing import Dict, Iterable, List, Union

from shapely.geometry import CAP_STYLE, JOIN_STYLE, MultiPolygon, Polygon
from shapely.ops import unary_union

from brooks.models import SimLayout
from brooks.types import AreaType, SeparatorType
from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.constants import OPENING_BUFFER_TO_CUT_WALLS


class NoiseBlockingElementsHandler:
    def __init__(
        self,
        site_surroundings: Iterable[Union[Polygon, MultiPolygon]],
        site_plans: List[Dict],
    ):
        self.target_buildings = defaultdict(list)

        for site_plan in site_plans:
            self.target_buildings[site_plan["building_id"]].append(
                {
                    "plan_layout": site_plan["plan_layout"],
                    "is_ground_floor": 0 in site_plan["floor_numbers"],
                    "id": site_plan["id"],
                }
            )

        self.blocking_elements_by_plan_id = self._get_blocking_elements(
            site_surroundings=site_surroundings,
            target_buildings=list(self.target_buildings.values()),
        )

    def get_blocking_elements_by_plan_id(self, plan_id: int):
        return self.blocking_elements_by_plan_id[plan_id]

    @classmethod
    def _get_blocking_elements(
        cls,
        site_surroundings: Iterable[Union[Polygon, MultiPolygon]],
        target_buildings: List[List[Dict]],
    ) -> Dict[int, MultiPolygon]:
        """
        Returns a dict with key SimLayout and value list of STRtrees containing 2 items each:
        1. An STRtree containing the site's building footprints
        2. An STRtree containing the building surrounding footprints
        """
        non_intersecting_surroundings = (
            cls._exclude_intersecting_footprints_from_surroundings(
                target_buildings=target_buildings, site_surroundings=site_surroundings
            )
        )

        blocking_elements_by_id = {}
        for i, plans in enumerate(target_buildings):
            # NOTE we use the ground floor as an approximation of the other buildings
            other_buildings = target_buildings[:i] + target_buildings[i + 1 :]
            other_building_footprints = [
                plan["plan_layout"].footprint
                for other_building in other_buildings
                for plan in other_building
                if plan["is_ground_floor"] is True
            ]
            for plan in plans:
                wall_footprint = cls.get_wall_footprint(layout=plan["plan_layout"])
                blocking_elements = ensure_geometry_validity(
                    unary_union(
                        [wall_footprint]
                        + other_building_footprints
                        + non_intersecting_surroundings
                    )
                )

                blocking_elements_by_id[plan["id"]] = blocking_elements
        return blocking_elements_by_id

    @classmethod
    def _exclude_intersecting_footprints_from_surroundings(
        cls,
        target_buildings: List[List[Dict]],
        site_surroundings: Iterable[Union[Polygon, MultiPolygon]],
    ) -> List[Union[Polygon, MultiPolygon]]:
        site_buildings_layout = unary_union(
            [
                plan["plan_layout"].footprint
                for plans in target_buildings
                for plan in plans
            ]
        )
        result = []
        for footprint in site_surroundings:
            if not footprint.intersects(site_buildings_layout):
                result.append(footprint)
        return result

    @staticmethod
    def get_wall_footprint(layout: SimLayout) -> Union[Polygon, MultiPolygon]:
        # NOTE we use the walls footprint excluding railings and loggias windows,
        # to allow for noise to travel through them
        wall_footprint = unary_union(
            [
                separator.footprint
                for separator in layout.separators
                if separator.type in {SeparatorType.COLUMN, SeparatorType.WALL}
            ]
        )
        loggias = layout.areas_by_type[AreaType.LOGGIA]

        loggias_windows = sorted(
            [
                opening.footprint.buffer(
                    OPENING_BUFFER_TO_CUT_WALLS,
                    join_style=JOIN_STYLE.mitre,
                    cap_style=CAP_STYLE.square,
                )  # Currently, openings seems not to match perfectly with the separators
                for area in loggias
                for opening in layout.areas_openings[area.id]
            ],
            key=lambda pol: pol.area,
            reverse=True,
        )

        for opening in loggias_windows:
            # One by one as in some cases the difference of the unary union
            # of the loggias windows produce annoying topological errors :(
            wall_footprint = wall_footprint.difference(opening)

        return wall_footprint
