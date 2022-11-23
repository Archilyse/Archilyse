import typing
from collections import Counter
from typing import Dict

from handlers.plan_handler import PlanHandlerSiteCacheMixin


class GeoreferencingValidator(PlanHandlerSiteCacheMixin):
    def georeferencing_errors(
        self,
    ) -> Dict[str, str]:
        errors_by_plan = self._georef_errors_by_plan()

        errors_msg = {
            f"plan {plan_id}": f"Plan does not match in georeferencing with {plan_errors} plans of the same building"
            for plan_id, plan_errors in errors_by_plan.items()
            if plan_errors
        }

        return errors_msg

    def _georef_errors_by_plan(
        self,
    ) -> Dict[int, int]:
        errors_by_plan: typing.Counter = Counter()
        for _, plan_ids in self.plan_ids_per_building.items():
            all_footprints = {}
            for plan_id in plan_ids:
                plan_handler = self.layout_handler_by_id(plan_id=plan_id)
                # If the validator is called from the api and the rest of the plans are not georeferenced yet
                # we ignore the check over the rest of the plans
                all_footprints[plan_id] = plan_handler.get_georeferenced_footprint()

            for plan_id_a, footprint_a in all_footprints.items():
                for plan_id_b, footprint_b in all_footprints.items():
                    if plan_id_a != plan_id_b and not footprint_a.intersects(
                        footprint_b
                    ):
                        errors_by_plan[plan_id_a] += 1
        return errors_by_plan
