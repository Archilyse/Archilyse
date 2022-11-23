from collections import Counter

import pytest
from deepdiff import DeepDiff

from common_utils.exceptions import DBNotFoundException
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler
from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import (
    CURRENT_REACT_ANNOTATION_VERSION,
    ReactPlannerBackground,
    ReactPlannerData,
    ReactPlannerGeomProperty,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerSchema,
    ReactPlannerVertex,
)


@pytest.mark.parametrize(
    "empty_annotation, errors, annotation_finished, expected_annotation_finished",
    [
        (True, ["error 1"], True, False),
        (True, [], True, False),
        (True, [], False, False),
        (True, ["error 2"], False, False),
        (False, ["error 1"], True, False),
        (False, [], True, True),
        (False, [], False, False),
        (False, ["error 2"], False, False),
    ],
)
def test_get_plan_data(
    mocker,
    empty_annotation,
    errors,
    annotation_finished,
    expected_annotation_finished,
):
    if empty_annotation:
        annotation = ReactPlannerData()
    else:
        annotation = ReactPlannerData()
        line = ReactPlannerLine(
            id="line_id",
            vertices=["va", "vb"],
            auxVertices=["va"],
            properties=ReactPlannerLineProperties(
                width=ReactPlannerGeomProperty(value=10),
                height=ReactPlannerGeomProperty(value=100),
            ),
            coordinates=[],
        )
        vertex_a = ReactPlannerVertex(id="va", x=0, y=0, lines=["line_id"])
        vertex_b = ReactPlannerVertex(id="vb", x=10, y=10, lines=["line_id"])
        annotation.layers["layer-1"].vertices = {
            vertex_a.id: vertex_a,
            vertex_b.id: vertex_b,
        }
        annotation.layers["layer-1"].lines = {line.id: line}

    mocker.patch.object(
        ReactPlannerProjectsDBHandler,
        "get_by",
        return_value={"data": ReactPlannerSchema().dump(annotation)},
    )
    mocker.patch.object(ReactPlannerHandler, "_validate_plan_data", return_value=errors)

    plan_data = ReactPlannerHandler().get_plan_data_w_validation_errors(
        plan_info={"id": 1, "annotation_finished": annotation_finished}, validated=True
    )
    assert bool(plan_data["annotation_finished"]) is expected_annotation_finished
    assert plan_data["errors"] == errors


def test_get_scale_factor_planner_handler(mocker):
    mocker.patch.object(
        ReactPlannerProjectsDBHandler,
        "get_by",
        return_value={"data": ReactPlannerSchema().dump(ReactPlannerData(scale=3.0))},
    )
    assert ReactPlannerHandler().plan_scale(plan_id=1) == 3.0


def test_validate_plan_react_data(mocker, react_planner_background_image_full_plan):
    from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper

    mocker.patch.object(
        ReactPlannerHandler,
        "project",
        return_value={"data": react_planner_background_image_full_plan},
    )

    get_layout_spy = mocker.spy(ReactPlannerToBrooksMapper, "get_layout")
    errors = ReactPlannerHandler()._validate_plan_data(
        plan_id=1,
        schema_loaded=ReactPlannerSchema().load(
            react_planner_background_image_full_plan
        ),
    )

    assert Counter([error.type for error in errors]) == {
        "OPENING_OVERLAPS_ANOTHER_OPENING": 4,
        "CORRUPTED_ANNOTATION": 1,
    }
    assert not DeepDiff(
        {coord for e in errors for coord in (e.position.x, e.position.y)},
        {
            1259.5670610313005,
            1068.80803867936,
            1068.4827250286942,
            2193.6825398691913,
            2194.6121246759267,
            2193.2834227877715,
            1364.5265844164928,
            1403.1879136718958,
            1212.5045023275177,
            1086.8021602083118,
        },
        significant_digits=3,
        ignore_order=True,
    )
    assert get_layout_spy.call_args_list[0].kwargs["scaled"] is True
    assert get_layout_spy.call_args_list[0].kwargs["post_processed"] is False


def test_get_by_migrated(mocker):
    react_data = {"version": CURRENT_REACT_ANNOTATION_VERSION}
    mocked_db_handler = mocker.patch.object(
        ReactPlannerProjectsDBHandler, "get_by", return_value={"data": react_data}
    )
    mocked_migration_call = mocker.patch.object(
        ReactPlannerHandler, "migrate_data_if_old_version", return_value=react_data
    )

    ReactPlannerHandler().get_by_migrated(plan_id=-99)
    assert mocked_db_handler.call_count == 1
    assert mocked_migration_call.call_count == 1


def test_get_by_migrated_no_db_call(mocker):
    react_data = {"version": CURRENT_REACT_ANNOTATION_VERSION}
    mocked_db_handler = mocker.patch.object(
        ReactPlannerProjectsDBHandler, "get_by", return_value={"data": react_data}
    )
    mocked_migration_call = mocker.patch.object(
        ReactPlannerHandler, "migrate_data_if_old_version", return_value=react_data
    )

    ReactPlannerHandler(plan_data={"data": {}}).get_by_migrated(plan_id=-99)
    assert mocked_db_handler.call_count == 0
    assert mocked_migration_call.call_count == 1


def test_get_image_transformation(mocker):
    data = ReactPlannerSchema().dump(ReactPlannerData())
    data["background"] = {
        "rotation": 45,
        "shift": {"x": 10, "y": 20},
        "width": 1000,
        "height": 500,
    }

    mocker.patch.object(
        ReactPlannerHandler,
        "get_data",
        return_value=ReactPlannerData(**data),
    )
    mocker.patch.object(PlanDBHandler, "get_by", return_value={"image_width": 3000})
    transformation = ReactPlannerHandler().get_image_transformation(plan_id=1)
    assert transformation == {
        "rotation": 45,
        "shift_x": 10,
        "shift_y": 20,
        "scale": 1000 / 3000,
    }


def test_get_image_transformation_if_no_react_project_exists_return_default(mocker):
    mocker.patch.object(
        ReactPlannerHandler, "get_data", side_effect=DBNotFoundException()
    )
    transformation = ReactPlannerHandler().get_image_transformation(plan_id=1)
    assert transformation == {
        "shift_x": 0.0,
        "shift_y": 0.0,
        "scale": 1.0,
        "rotation": 0.0,
    }


@pytest.mark.parametrize(
    "background_data, expected",
    [
        (
            {
                "rotation": None,
                "shift": {"x": None, "y": None},
                "width": None,
                "height": None,
            },
            {
                "shift_x": 0.0,
                "shift_y": 0.0,
                "scale": 1.0,
                "rotation": 0.0,
            },
        ),
        (
            {
                "rotation": 100,
                "shift": {"x": None, "y": None},
                "width": None,
                "height": None,
            },
            {
                "shift_x": 0.0,
                "shift_y": 0.0,
                "scale": 1.0,
                "rotation": 100,
            },
        ),
        (
            {
                "rotation": None,
                "shift": {"x": 10.0, "y": 11.0},
                "width": None,
                "height": None,
            },
            {
                "shift_x": 10.0,
                "shift_y": 11.0,
                "scale": 1.0,
                "rotation": 0.0,
            },
        ),
    ],
)
def test_get_image_transformation_any_value_none_return_default(
    mocker, background_data, expected
):
    data = ReactPlannerData()
    data.background = ReactPlannerBackground(**background_data)
    mocker.patch.object(ReactPlannerHandler, "get_data", return_value=data)
    mocker.patch.object(PlanDBHandler, "get_by", return_value={"image_width": 3000})
    transformation = ReactPlannerHandler().get_image_transformation(plan_id=1)
    assert transformation == expected
