import pytest

from brooks.types import FeatureType, OpeningType, SeparatorType
from handlers import PlanLayoutHandler


@pytest.fixture
def plan_info():
    return {
        "id": 1,
        "default_wall_height": 1.0,
        "default_door_height": 1.5,
        "default_window_lower_edge": 3.0,
        "default_window_upper_edge": 4.0,
        "default_ceiling_slab_height": 0.3,
    }


@pytest.fixture
def expected_element_heights():
    return {
        SeparatorType.WALL: (0, 1.0),
        SeparatorType.COLUMN: (0, 1.0),
        SeparatorType.AREA_SPLITTER: (0, 1.0),
        "GENERIC_SPACE_HEIGHT": (0, 1.0),
        FeatureType.STAIRS: (0, 1.0),
        FeatureType.ELEVATOR: (0, 1.0),
        OpeningType.WINDOW: (3.0, 4.0),
        OpeningType.DOOR: (0.0, 1.5),
        OpeningType.ENTRANCE_DOOR: (0.0, 1.5),
    }


@pytest.mark.parametrize(
    "floor_numbers,floor_heights,target_floor_number,expected_baseline",
    [
        ((0, 1, 2), (1.1, 2.1, 3.1), 0, 0),
        ((0, 1, 2), (1.1, 2.1, 3.1), 1, 1.1),
        ((0, 1, 2), (1.1, 2.1, 3.1), 2, (1.1 + 2.1)),
        ((-2, -1, 0), (3.1, 2.1, 1.1), 0, 0),
        ((-2, -1, 0), (3.1, 2.1, 1.1), -1, -2.1),
        ((-2, -1, 0), (3.1, 2.1, 1.1), -2, -(3.1 + 2.1)),
        ((0, 2), (1.1, 3.1), 2, (1.1 + 2.9)),  # gap -> needs to use default of 2.9
        ((-2, 0), (3.1, 1.1), -2, -(2.9 + 3.1)),  # gap -> needs to use default of 2.9,
        ((-2, 2), (3.1, 1.1), 1, 2.9),  # gap -> needs to use default of 2.9,
    ],
)
def test_floor_handler_level_baseline(
    mocker, floor_numbers, floor_heights, target_floor_number, expected_baseline
):
    from handlers import FloorHandler
    from handlers.db import FloorDBHandler

    get_floor_number_heights_mock = mocker.patch.object(
        FloorHandler,
        "get_floor_number_heights",
        return_value=dict(zip(floor_numbers, floor_heights)),
    )
    mocker.patch.object(
        FloorDBHandler,
        "get_by",
        return_value={"floor_number": target_floor_number, "building_id": 1337},
    )

    baseline = FloorHandler.get_level_baseline(floor_id=1)
    get_floor_number_heights_mock.assert_called_once_with(building_id=1337)
    assert baseline == expected_baseline


def test_plan_handler_plan_element_heights(plan_info, expected_element_heights):
    element_heights = PlanLayoutHandler(
        plan_id=1, plan_info=plan_info
    ).plan_element_heights
    for key, expected in expected_element_heights.items():
        assert element_heights[key] == expected


def test_element_heights_react_mapper(mocker, plan_info, expected_element_heights):
    from handlers.db import ReactPlannerProjectsDBHandler
    from handlers.editor_v2 import ReactPlannerHandler
    from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
    from handlers.editor_v2.schema import ReactPlannerSchema

    mocker.patch.object(ReactPlannerSchema, "load")
    mocker.patch.object(
        ReactPlannerProjectsDBHandler, "get_by", return_value={"data": None}
    )

    mocker.patch.object(ReactPlannerHandler, "migrate_data_if_old_version")
    react_mapper_mock = mocker.patch.object(ReactPlannerToBrooksMapper, "get_layout")

    PlanLayoutHandler(plan_id=1, plan_info=plan_info)._get_raw_layout_from_react_data()
    for key, expected in expected_element_heights.items():
        assert (
            react_mapper_mock.call_args.kwargs["default_element_heights"][key]
            == expected
        )
