from functools import cached_property
from typing import Dict, List, Set, Union

from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy.sql.expression import not_, null

from brooks.models.violation import Violation, ViolationType
from connectors.db_connector import get_db_session_scope
from db_models import BuildingDBModel, FloorDBModel, PlanDBModel
from handlers import PlanLayoutHandler
from handlers.db import (
    FloorDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
)
from handlers.utils import sql_object_as_dict
from handlers.validators.base_plan_validator import BasePlanValidator


class PlanOverlapValidator(BasePlanValidator):
    @cached_property
    def plan_info(self):
        return PlanDBHandler.get_by(id=self.plan_id)

    @cached_property
    def site_info(self):
        return SiteDBHandler.get_by(id=self.plan_info["site_id"])

    @cached_property
    def footprint(self) -> Union[Polygon, MultiPolygon]:
        return PlanLayoutHandler(
            plan_id=self.plan_info["id"],
            plan_info=self.plan_info,
            site_info=self.site_info,
        ).get_georeferenced_footprint()

    @cached_property
    def floor_numbers(self) -> Set[int]:
        return {
            floor["floor_number"]
            for floor in FloorDBHandler.find(
                plan_id=self.plan_id, output_columns=["floor_number"]
            )
        }

    def _overlaps(
        self,
        other_footprint: Union[Polygon, MultiPolygon],
        max_overlap_ratio: float,
    ) -> bool:
        return (
            other_footprint.intersection(self.footprint).area
            > self.footprint.area * max_overlap_ratio
        )

    def validate(self, max_overlap_ratio: float = 0.05) -> List[Violation]:
        """
        Makes sure no georeferenced plans of other buildings in the same floors overlap with this one.

        Args:
            max_overlap_ratio: If this buffer is exceeded by an intersection then a violation is raised
        """
        violations: List[Violation] = []
        georeferenced_plans = (
            self.get_other_georeferenced_plan_ids_by_building_id_and_floor_number()
        )
        planner_projects = {
            project["plan_id"]: project
            for project in ReactPlannerProjectsDBHandler.find_in(
                plan_id=[x["id"] for x in georeferenced_plans]
            )
        }

        for other_plan_info in georeferenced_plans:
            other_footprint = PlanLayoutHandler(
                plan_id=other_plan_info["id"],
                plan_info=other_plan_info,
                plan_data=planner_projects[other_plan_info["id"]],
                site_info=self.site_info,
            ).get_georeferenced_footprint()
            if self._overlaps(
                other_footprint=other_footprint,
                max_overlap_ratio=max_overlap_ratio,
            ):
                violations.append(
                    Violation(
                        violation_type=ViolationType.INTERSECTS_OTHER_BUILDING_PLAN,
                        position=self.footprint.centroid,
                        object_id=self.plan_id,
                        object_type="plan",
                        text=f"plan {self.plan_id} intersects with plan {other_plan_info['id']} "
                        f"(building {other_plan_info['building_id']}, "
                        f"floor {other_plan_info['floor_number']}) by more than {max_overlap_ratio*100}%",
                        is_blocking=False,
                    )
                )

        return violations

    def get_other_georeferenced_plan_ids_by_building_id_and_floor_number(
        self,
    ) -> List[Dict]:
        with get_db_session_scope(readonly=True) as session:
            query = (
                session.query(PlanDBModel, FloorDBModel)
                .join(FloorDBModel)
                .join(BuildingDBModel)
                .filter(not_(PlanDBModel.georef_rot_angle.is_(null())))
                .filter(PlanDBModel.site_id == self.plan_info["site_id"])
                .filter(FloorDBModel.floor_number.in_(self.floor_numbers))
                .filter(BuildingDBModel.id != self.plan_info["building_id"])
            )
            return [
                {
                    **sql_object_as_dict(plan),
                    "floor_number": floor.floor_number,
                }
                for plan, floor in query.all()
            ]
