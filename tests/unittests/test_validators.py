from collections import defaultdict

import pytest
from shapely.geometry import box

from brooks.classifications import CLASSIFICATIONS
from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.models.violation import ViolationType
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.constants import UNIT_USAGE
from handlers import PlanLayoutHandler, UnitHandler
from handlers.editor_v2 import ReactPlannerHandler
from handlers.validators import (
    PlanClassificationDoorNumberValidator,
    PlanClassificationFeatureConsistencyValidator,
    PlanClassificationRoomWindowValidator,
    PlanClassificationShaftValidator,
    SpacesConnectedValidator,
)
from handlers.validators.classification.balcony_has_railings import (
    PlanClassificationBalconyHasRailingValidator,
)
from handlers.validators.linking.unit_linking_validator import UnitLinkingValidator
from handlers.validators.unit_areas.unit_area_validation import DoorValidator
from tests.utils import _generate_dummy_layout


@pytest.mark.parametrize(
    "area_type_1, area_type_2, requires_windows",
    [
        (AreaType.NOT_DEFINED, AreaType.NOT_DEFINED, False),
        (AreaType.NOT_DEFINED, AreaType.SHAFT, False),
        (AreaType.BATHROOM, AreaType.KITCHEN_DINING, True),
        (AreaType.BATHROOM, AreaType.BEDROOM, True),
        (AreaType.BATHROOM, AreaType.LIVING_ROOM, True),
        (AreaType.NOT_DEFINED, AreaType.ROOM, True),
        (AreaType.NOT_DEFINED, AreaType.LIGHTWELL, True),
    ],
)
def test_space_should_have_window_or_balcony_door(
    area_type_1, area_type_2, requires_windows
):
    area = SimArea(footprint=box(0, 0, 10, 10))
    area2 = SimArea(footprint=box(0, 0, 10, 10))
    space = SimSpace(footprint=area.footprint)
    space.add_area(area=area)
    space.add_area(area=area2)

    area._type = area_type_1
    area2._type = area_type_2
    assert (
        bool(
            PlanClassificationRoomWindowValidator(
                plan_id=1, plan_layout=None
            ).area_types_requiring_window(space=space)
        )
        == requires_windows
    )


@pytest.mark.parametrize(
    "opening_type,has_window", [(OpeningType.WINDOW, True), (OpeningType.DOOR, False)]
)
def test_space_has_window(opening_type, has_window):
    area = SimArea(footprint=box(0, 0, 10, 10))
    space = SimSpace(footprint=area.footprint)
    space.add_area(area=area)
    separator = SimSeparator(
        footprint=box(0, 0, 10, 0.1), separator_type=SeparatorType.WALL
    )
    opening = SimOpening(
        footprint=box(1, 1, 2, 1.1),
        height=(1, 2.5),
        separator=separator,
        separator_reference_line=get_center_line_from_rectangle(separator.footprint)[0],
    )

    separator.add_opening(opening=opening)
    layout = SimLayout(spaces={space}, separators={separator})

    opening._type = opening_type

    assert (
        PlanClassificationRoomWindowValidator.space_has_window(
            layout=layout, space_id=space.id
        )
        == has_window
    )


@pytest.mark.parametrize(
    "area_type,has_door_to_balcony",
    [
        (AreaType.ROOM, False),
        (AreaType.BALCONY, True),
        (AreaType.LOGGIA, True),
        (AreaType.WINTERGARTEN, True),
    ],
)
def test_space_has_door_to_outdoor_area(area_type, has_door_to_balcony):
    area = SimArea(footprint=box(0, 0.2, 10, 10))
    space = SimSpace(footprint=area.footprint)
    space.add_area(area=area)

    area2 = SimArea(footprint=box(0, -10, 10, -0.2), area_type=area_type)
    space2 = SimSpace(footprint=area2.footprint)
    space2.add_area(area=area2)

    separator = SimSeparator(
        footprint=box(0, -0.2, 10, 0.2), separator_type=SeparatorType.WALL
    )
    opening = SimOpening(
        footprint=box(1, -0.2, 2, 0.2),
        height=(1, 2.5),
        separator=separator,
        opening_type=OpeningType.DOOR,
        separator_reference_line=get_center_line_from_rectangle(separator.footprint)[0],
    )
    separator.add_opening(opening=opening)

    layout = SimLayout(spaces={space, space2}, separators={separator})

    assert (
        PlanClassificationRoomWindowValidator(
            plan_id=1, plan_layout=None
        ).space_has_door_to_outdoor_area(
            layout=layout,
            space_id=space.id,
        )
        == has_door_to_balcony
    )


class TestPlanClassificationShaftValidator:
    def test_shaft_without_shaft_feature(self):
        plan_id = -1
        plan_layout = _generate_dummy_layout(area_type=AreaType.SHAFT)

        violations = PlanClassificationShaftValidator(
            plan_id=plan_id, plan_layout=plan_layout
        ).validate()
        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.SHAFT_WITHOUT_SHAFT_FEATURE

    def test_non_shaft_with_shaft_feature(self):
        plan_id = -1
        plan_layout = _generate_dummy_layout(
            area_type=AreaType.ROOM, feature_type=FeatureType.SHAFT
        )

        violations = PlanClassificationShaftValidator(
            plan_id=plan_id, plan_layout=plan_layout
        ).validate()
        assert len(violations) == 1
        assert (
            violations[0].violation_type == ViolationType.NON_SHAFT_WITH_SHAFT_FEATURE
        )

    def test_lightwell_with_shaft_feature_no_violation(self):
        plan_id = -1
        plan_layout = _generate_dummy_layout(
            area_type=AreaType.LIGHTWELL, feature_type=FeatureType.SHAFT
        )

        violations = PlanClassificationShaftValidator(
            plan_id=plan_id, plan_layout=plan_layout
        ).validate()
        assert len(violations) == 0

    @pytest.mark.parametrize(
        "opening_type, expected_violation, is_blocking",
        [
            ([OpeningType.WINDOW], ViolationType.SHAFT_HAS_OPENINGS, False),
            ([OpeningType.DOOR], ViolationType.SHAFT_HAS_OPENINGS, True),
            ([OpeningType.ENTRANCE_DOOR], ViolationType.SHAFT_HAS_OPENINGS, True),
            ([], None, None),
        ],
    )
    def test_shaft_with_shaft_but_with_openings_too(
        self, opening_type, expected_violation, is_blocking
    ):
        plan_id = -1
        plan_layout = _generate_dummy_layout(
            area_type=AreaType.SHAFT,
            feature_type=FeatureType.SHAFT,
            opening_types=opening_type,
        )

        violations = PlanClassificationShaftValidator(
            plan_id=plan_id, plan_layout=plan_layout
        ).validate()
        if expected_violation:
            assert len(violations) == 1
            assert violations[0].violation_type == expected_violation
            assert violations[0].is_blocking == is_blocking
        else:
            assert len(violations) == 0


@pytest.mark.parametrize(
    "area_type, num_doors, expected_violation",
    [
        (AreaType.CORRIDOR, 0, ViolationType.CORRIDOR_NOT_ENOUGH_DOORS),
        (AreaType.CORRIDOR, 1, ViolationType.CORRIDOR_NOT_ENOUGH_DOORS),
        (AreaType.CORRIDOR, 2, None),
        (AreaType.STOREROOM, 1, None),
        (AreaType.STOREROOM, 2, ViolationType.STORAGE_ROOM_TOO_MANY_DOORS),
    ],
)
def test_door_number_validator(area_type, num_doors, expected_violation):
    plan_id = -1
    plan_layout = _generate_dummy_layout(
        area_type=area_type, opening_types=[OpeningType.DOOR] * num_doors
    )
    violations = PlanClassificationDoorNumberValidator(
        plan_id=plan_id, plan_layout=plan_layout
    ).validate()

    if expected_violation:
        assert len(violations) == 1
        assert violations[0].violation_type == expected_violation
    else:
        assert not violations


def test_door_number_validator_space_multiple_areas(
    layout_scaled_classified_wo_db_conn,
):
    """Plan 3489 contains multiple examples of corridors that are part of a bigger space and therefore can't connect
    multiple doors"""
    layout = layout_scaled_classified_wo_db_conn(3489)
    violations = PlanClassificationDoorNumberValidator(
        plan_id=-1, plan_layout=layout
    ).validate()
    assert not violations


@pytest.mark.parametrize(
    "area_type,feature_type,expected_violation",
    [
        (AreaType.BATHROOM, FeatureType.TOILET, None),
        (AreaType.BATHROOM, FeatureType.BATHTUB, None),
        (AreaType.BATHROOM, FeatureType.SHOWER, None),
        (
            AreaType.ROOM,
            FeatureType.TOILET,
            ViolationType.FEATURE_DOES_NOT_MATCH_ROOM_TYPE,
        ),
        (
            AreaType.ROOM,
            FeatureType.BATHTUB,
            ViolationType.FEATURE_DOES_NOT_MATCH_ROOM_TYPE,
        ),
        (
            AreaType.ROOM,
            FeatureType.SHOWER,
            ViolationType.FEATURE_DOES_NOT_MATCH_ROOM_TYPE,
        ),
        (AreaType.KITCHEN, FeatureType.KITCHEN, None),
        (AreaType.KITCHEN_DINING, FeatureType.KITCHEN, None),
        (
            AreaType.ROOM,
            FeatureType.KITCHEN,
            ViolationType.FEATURE_DOES_NOT_MATCH_ROOM_TYPE,
        ),
    ],
)
def test_feature_consistency_validator(area_type, feature_type, expected_violation):
    plan_id = -1
    plan_layout = _generate_dummy_layout(area_type=area_type, feature_type=feature_type)

    violations = PlanClassificationFeatureConsistencyValidator(
        plan_id=plan_id, plan_layout=plan_layout
    ).validate()

    if expected_violation:
        assert len(violations) == 1
        assert violations[0].violation_type == expected_violation
    else:
        assert not violations


def test_balcony_without_railing_should_be_invalid():
    layout_with_balcony_inside = _generate_dummy_layout(area_type=AreaType.BALCONY)
    violations = PlanClassificationBalconyHasRailingValidator(
        plan_id=1, plan_layout=layout_with_balcony_inside
    ).validate()
    assert not layout_with_balcony_inside.railings
    assert len(violations) == 1
    assert violations[0].violation_type == ViolationType.BALCONY_WITHOUT_RAILING


@pytest.mark.parametrize(
    "railing_rect,violation_expected",
    [
        ((0.0, 0.0, 0.1, 1.0), False),
        # just far enough to not have it intersect with area after buffering it
        ((-0.025, 0.0, -0.02, 1.0), True),
        ((-2, -2, -1, -1), True),
        ((0.5, 0.5, 1, 1), False),
    ],
)
def test_balcony_area_must_have_a_buffered_railing_separator_intersect_it(
    railing_rect, violation_expected
):
    space = SimSpace(footprint=box(0, 0, 1, 1))
    area = SimArea(footprint=space.footprint, area_type=AreaType.BALCONY)
    space.add_area(area)
    railing = SimSeparator(
        separator_type=SeparatorType.RAILING, footprint=box(*railing_rect)
    )
    plan_layout = SimLayout(spaces={space}, separators={railing})

    violations = PlanClassificationBalconyHasRailingValidator(
        plan_id=1, plan_layout=plan_layout
    ).validate()
    assert (len(violations) == 1) == violation_expected


class TestSpacesConnectedValidator:
    @pytest.mark.parametrize(
        "area_type, classification_scheme",
        [
            (AreaType.LIGHTWELL, CLASSIFICATIONS.UNIFIED.value),
            (
                AreaType.OPERATIONS_FACILITIES,
                CLASSIFICATIONS.UNIFIED.value,
            ),
        ],
    )
    def test_unit_with_only_areas_no_connection_needed_should_not_create_violation(
        self, mocker, area_type, classification_scheme
    ):
        mocker.patch.object(
            UnitHandler,
            "layout_handler_by_id",
            return_value=PlanLayoutHandler(plan_id=-999),
        )
        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=None)
        mocker.patch.object(
            SpacesConnectedValidator,
            "new_areas",
            mocker.PropertyMock(return_value=[{"area_type": area_type.name}]),
        )
        violations = SpacesConnectedValidator(
            plan_id=None, new_area_ids=[], apartment_no=None, unit_handler=UnitHandler()
        ).validate()
        assert not violations

    def test_unit_area_not_matching_space_creates_violation(self, mocker):
        mocker.patch.object(
            UnitHandler,
            "layout_handler_by_id",
            return_value=PlanLayoutHandler(plan_id=-999),
        )
        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=SimLayout())
        mocker.patch.object(
            SpacesConnectedValidator,
            "new_areas",
            mocker.PropertyMock(
                return_value=[
                    {
                        "area_type": AreaType.ROOM.value,
                        "x_coord": 0,
                        "y_coord": 0,
                        "id": "1",
                    }
                ]
            ),
        )
        violations = SpacesConnectedValidator(
            plan_id=None, new_area_ids=[], apartment_no=None, unit_handler=UnitHandler()
        ).validate()

        assert len(violations) == 1
        assert violations[0].violation_type == ViolationType.AREA_MISSING_SPACE


@pytest.mark.parametrize(
    "unit_usage, unit_area_type, expect_violation",
    [
        (UNIT_USAGE.RESIDENTIAL.name, AreaType.COMMUNITY_ROOM.name, True),
        (UNIT_USAGE.RESIDENTIAL.name, AreaType.ROOM.name, False),
        (UNIT_USAGE.COMMERCIAL.name, AreaType.CORRIDOR.name, True),
        (UNIT_USAGE.COMMERCIAL.name, AreaType.OFFICE.name, False),
    ]
    + [(UNIT_USAGE.PLACEHOLDER.name, area_type.name, False) for area_type in AreaType],
)
def test_unit_linking_validator(mocker, unit_usage, unit_area_type, expect_violation):
    mocker.patch.object(ReactPlannerHandler, "plan_scale", return_value=0)

    areas_by_unit_id = {
        1: [
            {
                "area_type": unit_area_type,
                "coord_x": 100,
                "coord_y": 200,
            }
        ]
    }
    mocker.patch.object(
        UnitLinkingValidator, "areas_by_unit_id", return_value=areas_by_unit_id
    )
    unit_list = [{"id": 1, "unit_usage": unit_usage, "client_id": None}]
    violations = [
        violation
        for violations in UnitLinkingValidator.violations_by_unit_client_id(
            unit_list=unit_list, plan_id=-99
        ).values()
        for violation in violations
    ]
    if expect_violation:
        assert len(violations) == 1
        assert (
            violations[0].violation_type
            == ViolationType.AREA_TYPE_NOT_ALLOWED_FOR_UNIT_USAGE_TYPE
        )
    else:
        assert not violations


def test_unit_linking_validator_not_raising_exceptions_if_no_units():
    violations = UnitLinkingValidator.violations_by_unit_client_id(
        unit_list=[], plan_id=-99
    )
    assert not violations
    assert isinstance(violations, defaultdict)


class TestDoorValidator:
    @pytest.mark.parametrize(
        "opening_type, should_violate",
        [(OpeningType.DOOR, True), (OpeningType.ENTRANCE_DOOR, False)],
    )
    def test_only_entrance_doors_connecting_shared_spaces(
        self, mocker, opening_type, should_violate
    ):
        """
        ____________________________________________
        │        │  │  a3        │  │              │
        │        │  │____________│  │              │
        │ a1     │__│            │__│   a4         │
        │        │d1│  a2        │d2│              │
        │________│__│____________│__│______________│

        Test of Validation of a Unit containing areas a2 & a4. a2 is part of a shared space, a4 is a privat spaces.
        If door d2 is not an entrance door a violation should be raised.
        Remark:
        area a1 and door d1 are additionally added to the test to ensure following scenario:
        d1 beeing a regular door connecting to another shared / public space. We have to make sure
        that this is not creating a violation as d1 is assigned to the unit.

        """
        a1 = SimArea(footprint=box(-5, 0, -0.2, 5), area_type=AreaType.CORRIDOR)
        s1 = SimSpace(footprint=a1.footprint)
        s1.areas = {a1}
        w1 = SimSeparator(
            footprint=box(-0.2, 0, 0, 5), separator_type=SeparatorType.WALL
        )
        d1 = SimOpening(
            footprint=box(-0.2, 0, 0, 1),
            height=None,
            opening_type=OpeningType.DOOR,
            separator=w1,
            separator_reference_line=get_center_line_from_rectangle(w1.footprint)[0],
        )
        w1.openings = {d1}
        a2 = SimArea(
            footprint=box(0, 0, 5, 2.5), area_type=AreaType.LOGGIA, db_area_id=2
        )
        a3 = SimArea(
            footprint=box(0, 2.5, 5, 5), area_type=AreaType.ARCADE, db_area_id=3
        )
        shared_space = SimSpace(footprint=box(0, 0, 5, 5))
        shared_space.areas = {a2, a3}
        w2 = SimSeparator(
            footprint=box(5, 0, 5.2, 5), separator_type=SeparatorType.WALL
        )
        d2 = SimOpening(
            footprint=box(5, 0, 5.2, 1),
            height=None,
            opening_type=opening_type,
            separator=w2,
            separator_reference_line=get_center_line_from_rectangle(w2.footprint)[0],
        )
        w2.openings = {d2}

        a4 = SimArea(
            footprint=box(5.2, 0, 10, 5), area_type=AreaType.ROOM, db_area_id=4
        )
        inside_space = SimSpace(footprint=box(5.2, 0, 10, 5))
        inside_space.areas = {a4}

        plan_layout = SimLayout()
        plan_layout.add_spaces({s1, shared_space, inside_space})
        plan_layout.add_separators({w1, w2})

        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=plan_layout)
        mocker.patch.object(
            UnitHandler,
            "layout_handler_by_id",
            return_value=PlanLayoutHandler(plan_id=-999),
        )

        violations = DoorValidator(
            plan_id=None,
            new_area_ids=[2, 4],
            apartment_no=None,
            unit_handler=UnitHandler(),
        ).validate()

        if should_violate:
            assert len(violations) == 1
            assert (
                violations[0].violation_type
                == ViolationType.SHARED_SPACE_NOT_CONNECTED_WITH_ENTRANCE_DOOR
            )
        else:
            assert not violations

    @pytest.mark.parametrize(
        "opening_type, should_violate",
        [(OpeningType.DOOR, False), (OpeningType.ENTRANCE_DOOR, True)],
    )
    def test_private_spaces_not_connected_by_entrance_doors(
        self, mocker, opening_type, should_violate
    ):
        """
        __________________________
        │        │  │            │
        │        │  │            │
        │ Balcony│__│  ROOM      │
        │        │d1│            │
        │________│__│____________│
        """
        balcony = SimArea(
            footprint=box(-5, 0, -0.2, 5), area_type=AreaType.BALCONY, db_area_id=1
        )
        s1 = SimSpace(footprint=balcony.footprint)
        s1.areas = {balcony}
        w1 = SimSeparator(
            footprint=box(-0.2, 0, 0, 5), separator_type=SeparatorType.WALL
        )
        d1 = SimOpening(
            footprint=box(-0.2, 0, 0, 1),
            height=None,
            opening_type=opening_type,
            separator=w1,
            separator_reference_line=get_center_line_from_rectangle(w1.footprint)[0],
        )
        w1.openings = {d1}
        room = SimArea(footprint=box(0, 0, 5, 5), area_type=AreaType.ROOM, db_area_id=2)
        s2 = SimSpace(footprint=room.footprint)
        s2.areas = {room}

        plan_layout = SimLayout()
        plan_layout.add_spaces({s1, s2})
        plan_layout.add_separators({w1})

        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=plan_layout)
        mocker.patch.object(
            UnitHandler,
            "layout_handler_by_id",
            return_value=PlanLayoutHandler(plan_id=-999),
        )

        violations = DoorValidator(
            plan_id=None,
            new_area_ids=[1, 2],
            apartment_no=None,
            unit_handler=UnitHandler(),
        ).validate()

        if should_violate:
            assert len(violations) == 1
            assert violations[0].violation_type == ViolationType.INSIDE_ENTRANCE_DOOR
        else:
            assert not violations
