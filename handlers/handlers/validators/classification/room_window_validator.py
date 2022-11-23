from typing import Dict, List, Set

from methodtools import lru_cache

from brooks import SpaceConnector
from brooks.models import SimLayout, SimSpace
from brooks.models.violation import SpatialEntityViolation, ViolationType
from brooks.types import AreaType, OpeningType
from handlers.validators.classification import PlanClassificationValidator


class PlanClassificationRoomWindowValidator(PlanClassificationValidator):
    def validate(self) -> List[SpatialEntityViolation]:
        violations: List[SpatialEntityViolation] = []

        for space in self.plan_layout.spaces:
            area_types = self.area_types_requiring_window(space=space)
            if area_types and not (
                self.space_has_window(layout=self.plan_layout, space_id=space.id)
                or self.space_has_door_to_outdoor_area(
                    layout=self.plan_layout,
                    space_id=space.id,
                )
            ):
                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.ROOM_NOT_ENOUGH_WINDOWS,
                        entity=space,
                        text=f"Space with not enough windows that has been classified as {[t.name for t in area_types]}",
                        is_blocking=False,
                    )
                )

        return violations

    def area_types_requiring_window(self, space: SimSpace) -> Set[AreaType]:
        area_types_in_space = set([area.type for area in space.areas])
        return area_types_in_space & self.classification_scheme.AREAS_WINDOW_REQUIRED

    @staticmethod
    def space_has_window(layout: SimLayout, space_id: str) -> bool:
        return (
            len(
                [
                    opening
                    for opening in layout.spaces_openings[space_id]
                    if opening.type == OpeningType.WINDOW
                ]
            )
            > 0
        )

    @lru_cache()
    def space_connections(self, layout: SimLayout) -> Dict[str, List[Dict[str, str]]]:
        space_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=layout.doors,
            spaces_or_areas=layout.spaces,
        )
        return space_connections

    def space_has_door_to_outdoor_area(
        self,
        layout: SimLayout,
        space_id: str,
    ) -> bool:
        spaces_by_id = {space.id: space for space in layout.spaces}
        for connection in self.space_connections(layout=layout).get(space_id, []):
            if any(
                [
                    True
                    for area in spaces_by_id[
                        [value for value in connection.values()][0]
                    ].areas
                    if area.type in self.classification_scheme.OUTDOOR_AREAS
                ]
            ):
                return True

        return False
