from brooks.models import SimLayout
from handlers.validators.base_plan_validator import BasePlanValidator


class PlanClassificationValidator(BasePlanValidator):
    def __init__(self, plan_id: int, plan_layout: SimLayout) -> None:
        super().__init__(plan_id=plan_id)

        self.plan_layout = plan_layout
