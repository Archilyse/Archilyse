import pytest
from shapely.geometry import LineString, MultiPolygon, box

from brooks.models import SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.models.violation import ViolationType
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from handlers import UnitHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from handlers.validators import (
    SpacesDoorsSinglePolygonValidator,
    SpacesUnionSinglePolygonValidator,
    UnitAccessibleValidator,
)


@pytest.mark.parametrize(
    "door_size, expected_exception",
    [
        ({"minx": 3.4, "miny": 0, "maxx": 3.45, "maxy": 3}, True),
        ({"minx": 3.5, "miny": 0, "maxx": 3.51, "maxy": 3}, True),
        ({"minx": 2.0, "miny": 0, "maxx": 5.0, "maxy": 3}, False),
    ],
)
def test_unit_validator_space_not_connected_unique_polygon(
    mocker, door_size, expected_exception
):
    """
      space 2
    ┌─────┐                ┌────┐
    │     │                │    │space 1
    │     │       ┌┐       │    │
    │     │       └┘       │    │
    └─────┘      door      └────┘
    """
    space_2 = box(minx=0, miny=0, maxx=1, maxy=3)
    space_1 = box(minx=6, miny=0, maxx=7, maxy=3)
    door_box = box(**door_size)

    separator = SimSeparator(
        separator_type=SeparatorType.WALL,
        footprint=box(minx=3.1, miny=0, maxx=4.9, maxy=3),
    )
    separator.openings = {
        SimOpening(
            footprint=door_box,
            separator=separator,
            height=(0, 200),
            opening_type=OpeningType.DOOR,
            separator_reference_line=LineString(),
        )
    }
    mocker.patch.object(
        UnitHandler,
        "build_unit_from_area_ids",
        return_value=SimLayout(
            spaces={SimSpace(footprint=space_1), SimSpace(footprint=space_2)},
            separators={separator},
        ),
    )
    validation_errors = SpacesDoorsSinglePolygonValidator(
        plan_id=-999,
        new_area_ids=[],
        apartment_no=1,
        unit_handler=UnitHandler(),
    ).validate()
    if expected_exception:
        assert len(validation_errors) == 1
        assert (
            validation_errors[0].violation_type
            == ViolationType.UNIT_SPACES_NOT_CONNECTED
        )
    else:
        assert validation_errors == []


def test_unit_validator_space_not_connected_small_shaft(mocker):
    """
      space 1
    ┌─────┐
    │     │
    │     │       ┌┐
    │     │       └┘
    └─────┘      shaft
    """
    space_1 = box(minx=0, miny=0, maxx=7, maxy=7)
    shaft_space = box(minx=8, miny=0, maxx=8.5, maxy=0.5)

    mocker.patch.object(
        UnitHandler,
        "build_unit_from_area_ids",
        return_value=SimLayout(
            spaces={SimSpace(footprint=space_1), SimSpace(footprint=shaft_space)}
        ),
    )
    validation_errors = SpacesUnionSinglePolygonValidator(
        plan_id=-999,
        new_area_ids=[],
        apartment_no=1,
        unit_handler=UnitHandler(),
    ).validate()

    assert len(validation_errors) == 1
    assert (
        validation_errors[0].violation_type == ViolationType.UNIT_SPACES_NOT_CONNECTED
    )


def test_spaces_union_single_polygon_validator_should_attempt_to_convert_unit_layout_to_polygon(
    mocker,
):
    import handlers.validators.unit_areas.unit_area_validation as validation_module

    unit_footprint = MultiPolygon([box(0, 0, 1, 1)])
    mocker.patch.object(
        SimLayout, "footprint", mocker.PropertyMock(return_value=unit_footprint)
    )
    mocker.patch.object(
        UnitHandler,
        "build_unit_from_area_ids",
        return_value=SimLayout(spaces={SimSpace(footprint=box(0, 0, 1, 1))}),
    )

    buffer_unbuffer_spy = mocker.spy(validation_module, "buffer_unbuffer_geometry")
    validation_errors = SpacesUnionSinglePolygonValidator(
        plan_id=-999,
        new_area_ids=[],
        apartment_no=1,
        unit_handler=UnitHandler(),
    ).validate()
    assert not validation_errors
    buffer_unbuffer_spy.assert_called_once()


@pytest.mark.parametrize(
    "replace_feature, expected_violation",
    [
        (OpeningType.ENTRANCE_DOOR, None),
        (FeatureType.STAIRS, None),
        (FeatureType.ELEVATOR, None),
        (FeatureType.SHAFT, ViolationType.APARTMENT_NOT_ACCESSIBLE),
    ],
)
def test_apartment_is_accessible(
    mocker, annotations_accessible_areas, replace_feature, expected_violation
):
    plan_layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_accessible_areas)
    )
    for area in plan_layout.areas:
        area._type = AreaType.ROOM

    for opening in plan_layout.openings:
        opening._type = replace_feature

    for feature in plan_layout.features:
        feature._type = replace_feature

    mocker.patch.object(
        UnitHandler, "build_unit_from_area_ids", return_value=plan_layout
    )
    violations = UnitAccessibleValidator(
        plan_id=123,
        new_area_ids=[],
        apartment_no=0,
        unit_handler=UnitHandler(),
    ).validate()
    if expected_violation:
        assert len(violations) == 1
        assert violations[0].violation_type == expected_violation
    else:
        assert not violations
