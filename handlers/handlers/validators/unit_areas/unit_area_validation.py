from functools import cached_property
from operator import itemgetter
from typing import Dict, List, Set

from shapely.geometry import MultiPolygon, Point, Polygon

from brooks import SpaceConnector
from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimLayout, SimOpening, SimSpace
from brooks.models.violation import SpatialEntityViolation, Violation, ViolationType
from brooks.types import AreaType, FeatureType, OpeningType
from brooks.util.geometry_ops import buffer_unbuffer_geometry
from common_utils.exceptions import FeaturesGenerationException
from handlers import AreaHandler, UnitHandler
from handlers.validators.base_plan_validator import BasePlanValidator


class UnitAreaValidator(BasePlanValidator):
    def __init__(
        self,
        plan_id: int,
        new_area_ids: List[int],
        apartment_no: int,
        unit_handler: UnitHandler,
    ):
        super().__init__(plan_id=plan_id)

        self.new_area_ids: Set[int] = set(new_area_ids)
        self.apartment_no = apartment_no
        self.unit_handler = unit_handler

    @cached_property
    def plan_areas(self) -> List[Dict]:
        return self.unit_handler.layout_handler_by_id(
            plan_id=self.plan_id
        ).scaled_areas_db

    @cached_property
    def new_areas(self) -> List[Dict]:
        return sorted(
            [area for area in self.plan_areas if area["id"] in self.new_area_ids],
            key=itemgetter("id"),
        )  # The returned areas are sorted by their database id to guarantee always the same order


class ForeignPlanAreaValidator(UnitAreaValidator):
    """
    Validates, if the unit area IDs do not belong to the provided plan ID.
    """

    def validate(self) -> List[Violation]:
        violations: List[Violation] = []

        plan_area_ids = [a["id"] for a in self.plan_areas]
        for unit_area_id in self.new_area_ids:
            if unit_area_id not in plan_area_ids:
                violations.append(
                    Violation(
                        violation_type=ViolationType.AREA_NOT_IN_PLAN,
                        position=None,
                        object_id=unit_area_id,
                        object_type="area",
                        human_id=self.get_human_id(
                            plan_id=self.plan_id, apartment_no=self.apartment_no
                        ),
                    )
                )

        return violations


class AreasNotDefinedValidator(UnitAreaValidator):
    """
    Validates, if the unit areas do not have the area_type attribute set as "NOT_DEFINED".
    """

    def validate(self) -> List[Violation]:
        violations: List[Violation] = []

        for area in self.new_areas:
            if area["area_type"] == AreaType.NOT_DEFINED.name:
                violations.append(
                    Violation(
                        violation_type=ViolationType.AREA_NOT_DEFINED,
                        position=Point(area["coord_x"], area["coord_y"]),
                        object_id=area["id"],
                        object_type="areas",
                        human_id=self.get_human_id(
                            plan_id=self.plan_id, apartment_no=self.apartment_no
                        ),
                    )
                )

        return violations


class UnitAccessibleValidator(UnitAreaValidator):
    """
    Validates, if the unit has areas, that are accessible.
    """

    def validate(self) -> List[Violation]:
        violations: List[Violation] = []

        unit_layout = self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )
        if not (
            any(
                (
                    True
                    for o in unit_layout.openings
                    if o.type is OpeningType.ENTRANCE_DOOR
                )
            )
            or any(
                (
                    True
                    for f in unit_layout.features
                    if f.type in {FeatureType.ELEVATOR, FeatureType.STAIRS}
                )
            )
            or any(
                (
                    True
                    for a in unit_layout.areas
                    if a.type in {AreaType.STAIRCASE, AreaType.ELEVATOR}
                )
            )
        ):
            position = (
                list(unit_layout.areas)[0].footprint.representative_point()
                if unit_layout.areas
                else None
            )
            violations.append(
                Violation(
                    violation_type=ViolationType.APARTMENT_NOT_ACCESSIBLE,
                    position=position,
                    human_id=self.get_human_id(
                        plan_id=self.plan_id, apartment_no=self.apartment_no
                    ),
                )
            )

        return violations


class UnitKitchenCountValidator(UnitAreaValidator):
    """
    Validates, if the unit has multiple kitchen areas
    """

    def validate(self) -> List[Violation]:
        violations: List[Violation] = []

        unit_layout = self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )
        num_kitchens = len(
            {
                area
                for area in unit_layout.areas
                if area.type in UnifiedClassificationScheme().RESIDENTIAL_KITCHEN_AREAS
            }
        )

        if num_kitchens > 1:
            position = (
                list(sorted(unit_layout.areas, key=lambda x: x.footprint.area))[
                    0
                ].footprint.representative_point()
                if unit_layout.areas
                else None
            )
            violations.append(
                Violation(
                    violation_type=ViolationType.APARTMENT_MULTIPLE_KITCHENS,
                    position=position,
                    human_id=self.get_human_id(
                        plan_id=self.plan_id, apartment_no=self.apartment_no
                    ),
                )
            )

        return violations


class SpacesConnectedValidator(UnitAreaValidator):
    """
    Validates, if the unit areas area owned by spaces, that are connected to each other.
    """

    def validate(self) -> List[Violation]:
        violations: List[Violation] = []
        plan_layout = self.unit_handler.layout_handler_by_id(
            plan_id=self.plan_id
        ).get_layout(classified=True, scaled=True, postprocessed=False)

        areas_connection_is_required = [
            area
            for area in self.new_areas
            if area["area_type"]
            not in {
                area.name
                for area in self.classification_scheme.AREA_TYPES_NO_CONNECTION_NEEDED
            }
        ]

        if not areas_connection_is_required:
            return []

        areas_spaces_matching: Dict[str, SimSpace] = {
            area["id"]: space
            for area in areas_connection_is_required
            for space in plan_layout.spaces
            if space.footprint.contains(Point(area["coord_x"], area["coord_y"]))
        }

        for area in areas_connection_is_required:
            if area["id"] not in areas_spaces_matching.keys():
                violations.append(
                    Violation(
                        violation_type=ViolationType.AREA_MISSING_SPACE,
                        position=None,
                        object_id=area["id"],
                        object_type="areas",
                        human_id=self.get_human_id(
                            plan_id=self.plan_id, apartment_no=self.apartment_no
                        ),
                    )
                )

        spaces_indexed: Dict[str, SimSpace] = {
            space.id: space for space in areas_spaces_matching.values()
        }
        spaces_to_traverse = (
            spaces_indexed.keys()
            - plan_layout.outdoor_spaces_connected_by_entrance_door
        )
        if spaces_to_traverse:
            start_space_id = list(
                sorted(
                    spaces_to_traverse,
                    key=lambda x: spaces_indexed[x].footprint.area,
                )
            )[-1]

            self.connectivity_violations(
                apartment_no=self.apartment_no,
                area_spaces=spaces_indexed,
                plan_id=self.plan_id,
                plan_layout=plan_layout,
                start_space_id=start_space_id,
                violations=violations,
            )

        return violations

    def connectivity_violations(
        self,
        apartment_no: int,
        area_spaces: Dict[str, SimSpace],
        plan_id: int,
        violations: List[Violation],
        plan_layout: SimLayout,
        start_space_id: str,
    ):
        space_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=plan_layout.openings_by_type[OpeningType.DOOR],
            spaces_or_areas=plan_layout.spaces,
        )
        connected_spaces = SpacesConnectedValidator._traverse_connected_spaces_dfs(
            next_space_id=start_space_id,
            connections=space_connections,
            discovered_spaces=set(),
        )
        # Remove SHAFTS here too
        connected_spaces = {
            space.id: space
            for space in plan_layout.spaces
            for area in space.areas
            if area.type
            not in self.classification_scheme.AREA_TYPES_NO_CONNECTION_NEEDED
            and space.id in connected_spaces
        }

        unit_layout = self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )
        outdoor_spaces = unit_layout.outdoor_spaces_connected_by_entrance_door
        self.spaces_not_connected_violations(
            apartment_no=apartment_no,
            area_spaces=area_spaces,
            connected_spaces={**connected_spaces, **outdoor_spaces},
            plan_id=plan_id,
            violations=violations,
        )
        self.spaces_connected_missing_violations(
            apartment_no=apartment_no,
            area_spaces=area_spaces,
            connected_spaces=connected_spaces,
            plan_id=plan_id,
            violations=violations,
        )

    @classmethod
    def spaces_connected_missing_violations(
        cls,
        apartment_no: int,
        area_spaces: Dict[str, SimSpace],
        connected_spaces: Dict[str, SimSpace],
        plan_id: int,
        violations: List[Violation],
    ):
        for space_id in set(connected_spaces.keys()) - set(area_spaces.keys()):
            space = connected_spaces[space_id]
            violations.append(
                SpatialEntityViolation(
                    violation_type=ViolationType.CONNECTED_SPACES_MISSING,
                    entity=space,
                    human_id=cls.get_human_id(
                        plan_id=plan_id, apartment_no=apartment_no
                    ),
                )
            )

    @classmethod
    def spaces_not_connected_violations(
        cls,
        apartment_no: int,
        area_spaces: Dict[str, SimSpace],
        connected_spaces: Dict[str, SimSpace],
        plan_id: int,
        violations: List[Violation],
    ):
        for space_id in set(area_spaces.keys()) - set(connected_spaces.keys()):
            space = area_spaces[space_id]
            violations.append(
                SpatialEntityViolation(
                    violation_type=ViolationType.UNIT_SPACES_NOT_CONNECTED,
                    entity=space,
                    human_id=cls.get_human_id(
                        plan_id=plan_id, apartment_no=apartment_no
                    ),
                )
            )

    @staticmethod
    def _traverse_connected_spaces_dfs(
        next_space_id: str, connections: Dict, discovered_spaces: Set
    ):
        door_spaces = connections[next_space_id]
        discovered_spaces.add(next_space_id)
        for door_space in door_spaces:
            for _, space_id in door_space.items():
                if space_id not in discovered_spaces:
                    SpacesConnectedValidator._traverse_connected_spaces_dfs(
                        next_space_id=space_id,
                        connections=connections,
                        discovered_spaces=discovered_spaces,
                    )
        return discovered_spaces


class SpacesDoorsSinglePolygonValidator(UnitAreaValidator):
    def validate(self) -> List[Violation]:
        unit_layout = self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )
        try:
            unit_layout.get_polygon_of_spaces_and_doors(layout=unit_layout)

        except FeaturesGenerationException:
            return [
                Violation(
                    violation_type=ViolationType.UNIT_SPACES_NOT_CONNECTED,
                    position=unit_layout.footprint.centroid,
                    object_type="areas",
                    human_id=self.get_human_id(
                        plan_id=self.plan_id, apartment_no=self.apartment_no
                    ),
                )
            ]
        return []


class SpacesUnionSinglePolygonValidator(UnitAreaValidator):
    def validate(self) -> List[Violation]:
        unit_layout = self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )
        unit_footprint = unit_layout.footprint
        if isinstance(unit_layout.footprint, MultiPolygon):
            unit_footprint = buffer_unbuffer_geometry(geometry=unit_layout.footprint)

        spaces_union = unit_layout.get_spaces_union(
            spaces=unit_layout.spaces,
            public_space=False,
            clip_to=unit_footprint,
        )
        if not isinstance(
            spaces_union,
            Polygon,
        ):
            return [
                Violation(
                    violation_type=ViolationType.UNIT_SPACES_NOT_CONNECTED,
                    # Highlight the smaller area
                    position=sorted(spaces_union.geoms, key=lambda x: x.area)[
                        0
                    ].centroid,
                    object_type="areas",
                    human_id=self.get_human_id(
                        plan_id=self.plan_id, apartment_no=self.apartment_no
                    ),
                )
            ]
        return []


class AllAreasSpacesSelectedValidator(UnitAreaValidator):
    """
    Validates if the spaces of the areas selected by the user have all the areas selected for the apartment.
    """

    def validate(self) -> List[Violation]:
        violations: List[Violation] = []
        unit_layout = self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )
        if len(unit_layout.areas) != len(self.new_area_ids):
            brooks_area_id_to_area_db_id = (
                AreaHandler.get_index_brooks_area_id_to_area_db_id(
                    layout=unit_layout,
                    db_areas=self.plan_areas,
                )
            )
            set_ids_user = set(self.new_area_ids)
            for area in unit_layout.areas:
                if brooks_area_id_to_area_db_id.get(area.id) not in set_ids_user:
                    violations.append(
                        SpatialEntityViolation(
                            violation_type=ViolationType.SPACE_MISSING_AREA_SELECTION,
                            entity=area,
                            human_id=self.get_human_id(
                                plan_id=self.plan_id, apartment_no=self.apartment_no
                            ),
                        )
                    )
        return violations


class DoorValidator(UnitAreaValidator):
    """
    Validation to ensure that the user used the right types of doors
    - To connect private spaces of a unit , the user must use regular doors (NOT entrance doors)
    - To connect a shared space to private spaces, the user must only use entrance doors
    """

    def validate(self) -> List[SpatialEntityViolation]:
        violations = []

        for door_id, spaces_ids in self.space_connections_by_doors.items():
            door = self.doors_indexed[door_id]
            if door.is_entrance and self.connects_private_spaces(spaces_ids=spaces_ids):
                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.INSIDE_ENTRANCE_DOOR,
                        entity=door,
                        human_id=self.get_human_id(
                            plan_id=self.plan_id, apartment_no=self.apartment_no
                        ),
                    )
                )

            if not door.is_entrance and self._connects_shared_and_private_space(
                spaces_ids=spaces_ids
            ):

                violations.append(
                    SpatialEntityViolation(
                        violation_type=ViolationType.SHARED_SPACE_NOT_CONNECTED_WITH_ENTRANCE_DOOR,
                        entity=door,
                        human_id=self.get_human_id(
                            plan_id=self.plan_id, apartment_no=self.apartment_no
                        ),
                    )
                )

        return violations

    def connects_private_spaces(self, spaces_ids: List[str]) -> bool:
        return len(set(spaces_ids).difference(self.ids_of_shared_spaces)) > 1

    def _connects_shared_and_private_space(self, spaces_ids: List[str]) -> bool:
        if set(spaces_ids).intersection(self.ids_of_shared_spaces) and set(
            spaces_ids
        ).difference(self.ids_of_shared_spaces):
            return True
        return False

    @cached_property
    def plan_layout(self) -> SimLayout:
        return self.unit_handler.layout_handler_by_id(plan_id=self.plan_id).get_layout(
            scaled=True
        )

    @cached_property
    def unit_layout(self) -> SimLayout:
        return self.unit_handler.build_unit_from_area_ids(
            area_ids=self.new_area_ids, plan_id=self.plan_id
        )

    @cached_property
    def doors_indexed(self) -> Dict[str, SimOpening]:
        return {door.id: door for door in self.unit_layout.doors}

    @cached_property
    def space_connections_by_doors(self) -> Dict[str, List[str]]:
        return SpaceConnector.get_connected_spaces_or_areas_per_door(
            doors=self.unit_layout.doors,
            spaces_or_areas=self.unit_layout.spaces,
        )

    @cached_property
    def ids_of_shared_spaces(self) -> Set[str]:
        shared_spaces_ids = set()
        for space in self.unit_layout.spaces:
            if len(space.areas) < len(self.plan_layout.spaces_by_id[space.id].areas):
                shared_spaces_ids.add(space.id)
        return shared_spaces_ids
