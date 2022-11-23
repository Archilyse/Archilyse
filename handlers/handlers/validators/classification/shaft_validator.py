from typing import List

from brooks.models.violation import SpatialEntityViolation, ViolationType
from brooks.types import AreaType, FeatureType, OpeningType
from handlers.validators.classification import PlanClassificationValidator


class PlanClassificationShaftValidator(PlanClassificationValidator):
    def validate(self) -> List[SpatialEntityViolation]:
        violations: List[SpatialEntityViolation] = []
        for area in self.plan_layout.areas:
            if (
                FeatureType.SHAFT in {feature.type for feature in area.features}
                and area.type
                not in self.classification_scheme.AREA_TYPES_ACCEPTING_SHAFTS
            ):
                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.NON_SHAFT_WITH_SHAFT_FEATURE,
                        entity=area,
                        text=f"plan {self.plan_id} contains an area with a {FeatureType.SHAFT.name}"
                        f" that has been classified as {area.type.name}",
                    )
                )

            if area.type is AreaType.SHAFT:
                if FeatureType.SHAFT not in {feature.type for feature in area.features}:
                    violations.append(
                        SpatialEntityViolation(
                            entity=area,
                            violation_type=ViolationType.SHAFT_WITHOUT_SHAFT_FEATURE,
                            text=f"plan {self.plan_id} has been classified as SHAFT but there is no shaft feature in it",
                        )
                    )
                if len(openings := self.plan_layout.areas_openings[area.id]) > 0:
                    violations.append(
                        SpatialEntityViolation(
                            entity=area,
                            violation_type=ViolationType.SHAFT_HAS_OPENINGS,
                            text=f"plan {self.plan_id} has shaft with openings",
                            is_blocking=False
                            if {opening._type for opening in openings}
                            == {OpeningType.WINDOW}
                            else True,
                        )
                    )

        return violations
