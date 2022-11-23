from collections import defaultdict
from typing import List

from brooks.models.violation import SpatialEntityViolation, ViolationType
from handlers.validators.classification import PlanClassificationValidator


class PlanClassificationDoorNumberValidator(PlanClassificationValidator):
    def validate(self) -> List[SpatialEntityViolation]:
        violations: List[SpatialEntityViolation] = []
        areas_by_space_id = defaultdict(set)
        space_by_id = {}
        for space in self.plan_layout.spaces:
            for area in space.areas:
                areas_by_space_id[space.id].add(area.type)
                space_by_id[space.id] = space

        for space_id, openings in self.plan_layout.spaces_openings.items():
            area_types = areas_by_space_id[space_id]
            num_doors = len([opening for opening in openings if opening.is_door])

            if (
                len(area_types) == 1
                and len(area_types & self.classification_scheme.STOREROOM_AREAS) == 1
                and num_doors > 1
            ):
                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.STORAGE_ROOM_TOO_MANY_DOORS,
                        entity=space_by_id[space_id],
                        is_blocking=False,
                    )
                )

            if (
                len(area_types) == 1
                and len(area_types & self.classification_scheme.CIRCULATION_AREAS) == 1
                and num_doors < 2
            ):
                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.CORRIDOR_NOT_ENOUGH_DOORS,
                        entity=space_by_id[space_id],
                        is_blocking=False,
                    )
                )

        return violations
