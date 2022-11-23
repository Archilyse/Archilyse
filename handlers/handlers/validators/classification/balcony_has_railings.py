from typing import List

from brooks.models.violation import SpatialEntityViolation, ViolationType
from brooks.types import AreaType, SeparatorType
from handlers.validators.classification import PlanClassificationValidator


class PlanClassificationBalconyHasRailingValidator(PlanClassificationValidator):
    def validate(self) -> List[SpatialEntityViolation]:
        violations: List[SpatialEntityViolation] = []
        balcony_areas = [
            a for a in self.plan_layout.areas if a.type == AreaType.BALCONY
        ]

        for area in balcony_areas:
            area_separators = self.plan_layout.areas_separators[area.id]
            has_railings = any(
                r for r in area_separators if r.type == SeparatorType.RAILING
            )
            if not has_railings:
                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.BALCONY_WITHOUT_RAILING,
                        entity=area,
                        is_blocking=False,
                    )
                )
        return violations
