from typing import List

from brooks.models.violation import SpatialEntityViolation, ViolationType
from handlers.validators.classification import PlanClassificationValidator


class PlanClassificationFeatureConsistencyValidator(PlanClassificationValidator):
    def validate(self) -> List[SpatialEntityViolation]:
        violations = []
        for area in self.plan_layout.areas:
            for feature in area.features:
                if (
                    feature.type
                    in self.classification_scheme.AREA_TYPES_FEATURE_MAPPING
                ):
                    if (
                        area.type
                        not in self.classification_scheme.AREA_TYPES_FEATURE_MAPPING[
                            feature.type
                        ]
                    ):
                        violations.append(
                            SpatialEntityViolation(
                                violation_type=ViolationType.FEATURE_DOES_NOT_MATCH_ROOM_TYPE,
                                entity=area,
                                text=f"plan {self.plan_id} contains an area with a {feature.type.name} "
                                f"that has been classified as {area.type.name}",
                                is_blocking=False,
                            )
                        )

        return violations
