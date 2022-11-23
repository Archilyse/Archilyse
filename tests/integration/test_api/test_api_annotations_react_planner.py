import uuid
from dataclasses import asdict
from http import HTTPStatus
from operator import itemgetter
from unittest.mock import MagicMock, call

import pytest
from deepdiff import DeepDiff

from brooks.models import SimLayout
from common_utils.constants import USER_ROLE
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    CURRENT_REACT_ANNOTATION_VERSION,
    ReactPlannerData,
    ReactPlannerGeomProperty,
    ReactPlannerItem,
    ReactPlannerItemProperties,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerName,
    ReactPlannerType,
    ReactPlannerVersions,
    ReactPlannerVertex,
)
from slam_api.apis.annotation_react_planner import (
    PlanAnnotationV2View,
    annotations_v2_app,
)
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for


@pytest.fixture
def planner_data_corrupted():
    planner_data = ReactPlannerData()
    # These vertices don't have any reference to the line
    vertex_a = ReactPlannerVertex(x=0, y=0)
    vertex_b = ReactPlannerVertex(x=10, y=10)
    planner_data.layers["layer-1"].vertices = {
        vertex_a.id: vertex_a,
        vertex_b.id: vertex_b,
    }
    line = ReactPlannerLine(
        properties=ReactPlannerLineProperties(
            width=ReactPlannerGeomProperty(value=10),
            height=ReactPlannerGeomProperty(value=100),
        ),
        vertices=[vertex_a.id, vertex_b.id],
        auxVertices=[vertex_a.id, vertex_b.id],
        coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]],
    )
    planner_data.layers["layer-1"].lines = {line.id: line}
    return planner_data


@pytest.fixture
def react_planner_data_errors():
    return [
        {
            "human_id": None,
            "is_blocking": 1,
            "object_id": "56e5bd3905944634bf4c0ced78099e00",
            "position": {"coordinates": [1109.58, 1446.72], "type": "Point"},
            "text": "Door is not connecting 2 areas",
            "type": "DOOR_NOT_CONNECTING_AREAS",
        },
        {
            "human_id": None,
            "is_blocking": 1,
            "object_id": "46a6936c207f4e279350ea63eb3e1d6e",
            "position": {"coordinates": [1461.53, 563.05], "type": "Point"},
            "text": "Space not accessible. It should have a type of door, stairs or an "
            "elevator",
            "type": "SPACE_NOT_ACCESSIBLE",
        },
    ]


@pytest.fixture
def react_planner_square_space_dict_scale_factor(
    react_data_valid_square_space_with_entrance_door,
):
    return react_data_valid_square_space_with_entrance_door["scale"]


@pytest.fixture
def plan_georeferenced(plan):
    return PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values={"georef_x": 124.56, "georef_y": 78.9},
    )


@pytest.fixture
def create_areas_for_plan_mock(mocker):
    import handlers.plan_utils

    return mocker.patch.object(handlers.plan_utils, "create_areas_for_plan")


@pytest.fixture
def update_plan_rotation_point_task_mock(mocker):
    from handlers import PlanHandler

    return mocker.patch.object(PlanHandler, "update_rotation_point")


@pytest.fixture
def react_planner_square_space_w_shaft_feature(
    react_data_valid_square_space_with_entrance_door,
):
    shaft_properties = ReactPlannerItemProperties(
        width=ReactPlannerGeomProperty(value=50),
        length=ReactPlannerGeomProperty(value=60),
        height=ReactPlannerGeomProperty(value=20),
        altitude=ReactPlannerGeomProperty(value=0),
    )
    shaft_id = str(uuid.uuid4())
    shaft_item = ReactPlannerItem(
        id=shaft_id,
        x=400,
        y=500,
        type=ReactPlannerType.SHAFT.value,
        name=ReactPlannerName.SHAFT.value,
        prototype="items",
        rotation=0,
        properties=shaft_properties,
    )
    react_data_valid_square_space_with_entrance_door["layers"]["layer-1"][
        "items"
    ].update({shaft_id: asdict(shaft_item)})
    react_data_valid_square_space_with_entrance_door["layers"]["layer-1"]["holes"] = {}
    return react_data_valid_square_space_with_entrance_door


class TestAnnotationPut:
    @staticmethod
    @pytest.mark.parametrize(
        "input_data",
        [
            pytest.lazy_fixture("react_data_valid_square_space_with_entrance_door"),
            pytest.lazy_fixture("react_planner_square_space_w_shaft_feature"),
        ],
    )
    def test_put_validates_react_schema_input_should_have_no_errors(
        client,
        login,
        plan,
        input_data,
        create_areas_for_plan_mock,
        update_plan_rotation_point_task_mock,
    ):
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=input_data,
        )
        assert response.status_code == HTTPStatus.OK
        assert not DeepDiff(response.json["errors"], [])
        assert response.json["annotation_finished"] is True
        create_areas_for_plan_mock.assert_called_once_with(plan_id=plan["id"])
        update_plan_rotation_point_task_mock.assert_called_once_with()

    @staticmethod
    @pytest.mark.parametrize(
        "scale_factor, should_be_cleared",
        [
            (
                pytest.lazy_fixture("react_planner_square_space_dict_scale_factor"),
                False,
            ),
            (1.22, True),
            (543.21, True),
        ],
    )
    def test_put_new_scale_factor_should_clear_georef_x_y(
        client,
        login,
        plan_georeferenced,
        react_data_valid_square_space_with_entrance_door,
        scale_factor,
        should_be_cleared,
    ):
        ReactPlannerProjectsDBHandler.add(
            plan_id=plan_georeferenced["id"],
            data=react_data_valid_square_space_with_entrance_door,
        )

        assert all(
            plan_georeferenced[param] is not None for param in ["georef_x", "georef_y"]
        )

        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan_georeferenced["id"],
                validated=False,
            ),
            json={
                **react_data_valid_square_space_with_entrance_door,
                "scale": scale_factor,
            },
        )
        assert response.status_code == HTTPStatus.OK
        plan_after_put = PlanDBHandler.get_by(id=plan_georeferenced["id"])

        if should_be_cleared:
            assert all(
                plan_after_put[param] is None for param in ["georef_x", "georef_y"]
            )
        else:
            assert all(
                plan_after_put[param] == plan_georeferenced[param]
                for param in ["georef_x", "georef_y"]
            )

    @staticmethod
    @login_as([USER_ROLE.ADMIN.name])
    @pytest.mark.parametrize(
        "input_data, expected_http_code, should_call_create_areas_task, annotation_initially_finished, expected_georef_scale",
        [
            (
                pytest.lazy_fixture("react_planner_floorplan_annotation_w_errors"),
                HTTPStatus.OK,
                False,
                True,
                0.00010004,
            ),
            (
                pytest.lazy_fixture("react_data_valid_square_space_with_entrance_door"),
                HTTPStatus.OK,
                True,
                False,
                0.00010004,
            ),
            (
                {"version": CURRENT_REACT_ANNOTATION_VERSION},
                HTTPStatus.UNPROCESSABLE_ENTITY,
                False,
                False,
                None,
            ),
        ],
    )
    def test_put_validates_react_schema_input_and_brooks_errors(
        client,
        login,
        plan,
        annotation_initially_finished,
        input_data,
        expected_http_code,
        should_call_create_areas_task,
        expected_georef_scale,
        create_areas_for_plan_mock,
        update_plan_rotation_point_task_mock,
    ):
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={"annotation_finished": annotation_initially_finished},
        )

        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=input_data,
        )
        assert response.status_code == expected_http_code
        assert create_areas_for_plan_mock.mock_calls == (
            [call(plan_id=plan["id"])] if should_call_create_areas_task else []
        )
        assert update_plan_rotation_point_task_mock.call_count == (
            1 if should_call_create_areas_task else 0
        )
        plan = PlanDBHandler.get_by(id=plan["id"])
        assert plan["annotation_finished"] == should_call_create_areas_task
        if response.status_code == HTTPStatus.OK:
            assert response.json["annotation_finished"] is should_call_create_areas_task

    @staticmethod
    def test_store_empty_plan_data_only_stores_and_reset_values(
        client,
        plan,
        create_areas_for_plan_mock,
        update_plan_rotation_point_task_mock,
    ):
        # Given the plan is already set as finished
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={"annotation_finished": True},
        )
        empty_data = asdict(ReactPlannerData())
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=empty_data,
        )
        assert response.status_code == HTTPStatus.OK
        create_areas_for_plan_mock.assert_not_called()
        update_plan_rotation_point_task_mock.assert_not_called()
        plan = PlanDBHandler.get_by(id=plan["id"])
        assert plan["annotation_finished"] is False
        assert response.json["annotation_finished"] is False

    @staticmethod
    def test_store_annotation_old_version_runs_all_migrations(client, plan):
        react_planner_data = ReactPlannerData()
        react_planner_data.version = ReactPlannerVersions.V15.name
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=asdict(react_planner_data),
        )

        assert response.status_code == HTTPStatus.OK, response.json
        assert (
            ReactPlannerProjectsDBHandler.get_by(plan_id=plan["id"])["data"]["version"]
            == CURRENT_REACT_ANNOTATION_VERSION
        )

    @staticmethod
    def test_annotation_migration_fails_raises_exception(client, plan, mocker):
        from handlers.editor_v2.schema import migration_by_version

        react_planner_data = ReactPlannerData()
        react_planner_data.version = ReactPlannerVersions.V11.name
        mocker.patch.dict(
            migration_by_version,
            {ReactPlannerVersions.V11.name: MagicMock(side_effect=Exception())},
        )
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=asdict(react_planner_data),
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert (
            response.json["msg"]
            == f"Could not migrate annotation from old version {ReactPlannerVersions.V11.name} to current version. Error: "
        )

    @staticmethod
    def test_annotation_migration_fails_if_project_version_below_baseline(client, plan):
        react_planner_data = ReactPlannerData()
        react_planner_data.version = ReactPlannerVersions.V4.name
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=asdict(react_planner_data),
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert (
            response.json["msg"]
            == f"Could not migrate annotation from old version {ReactPlannerVersions.V4.name}"
            f" to current version. Error: Project is not migrated up-to-date."
        )

    @staticmethod
    def test_validation_annotations_violation_put(client, plan, planner_data_corrupted):
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=asdict(planner_data_corrupted),
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json["errors"]) == 6
        assert (
            len(
                [
                    x
                    for x in response.json["errors"]
                    if "doesn't reference back the line" in x["text"]
                ]
            )
            == 4
        )

        # We also make sure the annotation is saved despite the errors
        project = ReactPlannerProjectsDBHandler.get_by(plan_id=plan["id"])
        assert len(project["data"]["layers"]["layer-1"]["lines"]) == 1
        assert len(project["data"]["layers"]["layer-1"]["vertices"]) == 2

    @staticmethod
    def test_put_violation_of_schema_raises_exception(client, plan):
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json={"random": True},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json["msg"]["random"] == ["Unknown field."]

    @staticmethod
    def test_put_incorrect_field_type_string_converted_to_float(client, plan):
        react_planner_data = ReactPlannerData()
        item = ReactPlannerItem(
            name=ReactPlannerName.KITCHEN.value,
            x=100,
            y=100,
            type=ReactPlannerType.KITCHEN.value,
            properties=ReactPlannerItemProperties(
                width=ReactPlannerGeomProperty(value="10"),
                length=ReactPlannerGeomProperty(value="10"),
            ),
            rotation=120,
        )
        react_planner_data.layers["layer-1"].items = {item.id: item}
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=asdict(react_planner_data),
        )
        assert response.status_code == HTTPStatus.OK

    @staticmethod
    def test_put_incorrect_field_type_incorrect_type_returns_validation_error(
        client, plan
    ):
        react_planner_data = ReactPlannerData()
        item = ReactPlannerItem(
            name=ReactPlannerName.KITCHEN.value,
            x=100,
            y=100,
            type=ReactPlannerType.KITCHEN.value,
            properties=ReactPlannerItemProperties(
                width=ReactPlannerGeomProperty(value="a"),
                length=ReactPlannerGeomProperty(value="b"),
            ),
            rotation=120,
        )
        react_planner_data.layers["layer-1"].items = {item.id: item}
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json=asdict(react_planner_data),
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json == {
            "msg": {
                "layers": {
                    "layer-1": {
                        "value": {
                            "items": {
                                item.id: {
                                    "value": {
                                        "properties": {
                                            "length": {
                                                "value": ["Not a valid number."]
                                            },
                                            "width": {"value": ["Not a valid number."]},
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    @staticmethod
    def test_annotation_migration_fails_and_schema_validation_raises_final_exception_and_not_migration_exception(
        client, plan, mocker
    ):
        from handlers.editor_v2.schema import migration_by_version

        mocker.patch.dict(
            migration_by_version,
            {ReactPlannerVersions.V11.name: MagicMock(side_effect=Exception())},
        )
        response = client.put(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
            json={"random": True},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json["msg"]["random"] == ["Unknown field."]


class TestGetAnnotations:
    @staticmethod
    def test_validation_annotations_violation_get(client, plan, planner_data_corrupted):
        ReactPlannerProjectsDBHandler.add(
            plan_id=plan["id"], data=asdict(planner_data_corrupted)
        )
        response = client.get(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
                validated=True,
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json["errors"]) == 6
        assert (
            len(
                [
                    x
                    for x in response.json["errors"]
                    if "doesn't reference back the line" in x["text"]
                ]
            )
            == 4
        )

    @staticmethod
    @login_as([USER_ROLE.TEAMMEMBER.name])
    def test_get_returns_persisted_react_planner_data(
        client, login, plan, insert_react_planner_data
    ):
        response = client.get(
            get_address_for(
                blueprint=annotations_v2_app,
                use_external_address=False,
                view_function=PlanAnnotationV2View,
                plan_id=plan["id"],
            ),
        )
        assert response.status_code == HTTPStatus.OK
        assert not DeepDiff(response.json["data"], insert_react_planner_data["data"])
        assert response.json["created"]
        assert response.json["id"]

    @staticmethod
    def test_get_returns_persisted_validated_react_planner_data_should_have_no_errors(
        mocker,
        client,
        login,
        plan,
        insert_react_planner_data,
    ):
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={
                "georef_scale": 1.0,
            },
        )
        mocker.patch.object(
            ReactPlannerToBrooksMapper,
            "get_layout",
            return_value=SimLayout(),
        )
        request_url = get_address_for(
            blueprint=annotations_v2_app,
            use_external_address=False,
            view_function=PlanAnnotationV2View,
            plan_id=plan["id"],
        )
        response = client.get(f"{request_url}?validated=true")
        assert response.status_code == HTTPStatus.OK
        assert not DeepDiff(response.json["data"], insert_react_planner_data["data"])
        assert not DeepDiff(response.json["errors"], [])

    @staticmethod
    def test_get_returns_persisted_validated_react_planner_data(
        client,
        login,
        plan,
        react_planner_data_errors,
        react_planner_floorplan_annotation_w_errors,
    ):
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={
                "georef_scale": 1.0,
            },
        )
        ReactPlannerProjectsDBHandler.add(
            plan_id=plan["id"],
            data=react_planner_floorplan_annotation_w_errors,
        )
        request_url = get_address_for(
            blueprint=annotations_v2_app,
            use_external_address=False,
            view_function=PlanAnnotationV2View,
            plan_id=plan["id"],
        )
        response = client.get(f"{request_url}?validated=true")
        assert response.status_code == HTTPStatus.OK
        assert not DeepDiff(
            response.json["data"], react_planner_floorplan_annotation_w_errors
        )
        assert not DeepDiff(
            sorted(response.json["errors"], key=itemgetter("type")),
            react_planner_data_errors,
            significant_digits=2,
            exclude_regex_paths="'object_id'",
            ignore_order=True,
        )
