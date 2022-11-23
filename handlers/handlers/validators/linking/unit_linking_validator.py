from collections import defaultdict
from typing import TYPE_CHECKING, Any, DefaultDict, Dict, List

from shapely.geometry import Point

from brooks.models.violation import Violation, ViolationType
from brooks.types import AREA_TYPE_USAGE, AreaType
from common_utils.constants import UNIT_USAGE

if TYPE_CHECKING:
    from handlers import ReactPlannerHandler


class UnitLinkingValidator:
    @classmethod
    def violations_by_unit_client_id(
        cls, unit_list: List[Dict[str, Any]], plan_id: int
    ) -> DefaultDict[str, List[Violation]]:
        from handlers import ReactPlannerHandler

        if not unit_list:
            return defaultdict(list)

        react_planner_handler = ReactPlannerHandler()
        violations_by_units = defaultdict(list)

        areas_by_unit_id = cls.areas_by_unit_id(
            plan_id=plan_id,
            unit_ids=[unit["id"] for unit in unit_list],
            react_planner_handler=react_planner_handler,
        )

        for unit in unit_list:
            unit_usage = UNIT_USAGE[unit["unit_usage"]]
            for area in areas_by_unit_id[unit["id"]]:
                if not cls.area_type_allowed_for_unit_usage(
                    area=area, unit_usage=unit_usage
                ):
                    violation = Violation(
                        violation_type=ViolationType.AREA_TYPE_NOT_ALLOWED_FOR_UNIT_USAGE_TYPE,
                        position=Point(area["coord_x"], area["coord_y"]),
                    )
                    react_planner_handler.violation_position_to_pixels(
                        violation=violation, plan_id=plan_id
                    )
                    violations_by_units[unit["client_id"]].append(violation)

        return violations_by_units

    @staticmethod
    def areas_by_unit_id(
        unit_ids: List[int], plan_id: int, react_planner_handler: "ReactPlannerHandler"
    ) -> DefaultDict[int, List[Dict]]:
        from handlers import PlanLayoutHandler
        from handlers.db import UnitAreaDBHandler

        unit_areas = UnitAreaDBHandler.find_in(unit_id=unit_ids)
        plan_areas = {
            area["id"]: area
            for area in PlanLayoutHandler(
                plan_id=plan_id, react_planner_handler=react_planner_handler
            ).scaled_areas_db
        }
        areas_by_unit_id = defaultdict(list)
        for unit_area in unit_areas:
            areas_by_unit_id[unit_area["unit_id"]].append(
                plan_areas[unit_area["area_id"]]
            )

        return areas_by_unit_id

    @staticmethod
    def area_type_allowed_for_unit_usage(
        area: Dict,
        unit_usage: UNIT_USAGE,
    ) -> bool:
        if AreaType[area["area_type"]] not in AREA_TYPE_USAGE:
            return True  # When no usage type is defined we assume all are allowed

        return unit_usage in AREA_TYPE_USAGE[AreaType[area["area_type"]]]
