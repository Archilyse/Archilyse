from collections import Counter
from http import HTTPStatus

import pytest
from shapely import wkt
from shapely.geometry import shape

from brooks.classifications import CLASSIFICATIONS
from brooks.models.violation import ViolationType
from brooks.types import AreaType, SIACategory
from common_utils.constants import DMS_PERMISSION, USER_ROLE
from handlers import AreaHandler, PlanHandler, PlanLayoutHandler
from handlers.db import DmsPermissionDBHandler, SiteDBHandler
from handlers.db.area_handler import AreaDBHandler
from handlers.editor_v2 import ReactPlannerHandler
from slam_api.apis.areas import (
    AreasView,
    areas_app,
    get_areas_autoclassified,
    get_areas_by_unit_id,
    validate_classifications,
)
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for


def test_get_plan_areas(client, plan, areas_db, login):
    url = get_address_for(
        blueprint=areas_app,
        view_function=AreasView,
        plan_id=plan["id"],
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    for area in areas_db:
        area["coord_x"] = float(area["coord_x"])
        area["coord_y"] = float(area["coord_y"])
    assert sorted(response.json, key=lambda x: x["id"]) == sorted(
        areas_db, key=lambda x: x["id"]
    )


class TestAutoClassification:
    @staticmethod
    def test_get_plan_areas_autoclassified_react_planner(
        client,
        login,
        plan_annotated,
    ):
        url = get_address_for(
            blueprint=areas_app,
            view_function=get_areas_autoclassified,
            plan_id=plan_annotated["id"],
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert Counter([area["area_type"] for area in response.json]) == {
            AreaType.ROOM.value: 2,
            AreaType.BATHROOM.value: 1,
            AreaType.CORRIDOR.value: 1,
            AreaType.KITCHEN.value: 1,
            AreaType.BALCONY.value: 2,
        }

    @staticmethod
    @pytest.mark.parametrize(
        "fixture_plan_id, expected_count",
        [
            (
                2494,
                {
                    AreaType.STAIRCASE.value: 1,
                    AreaType.BATHROOM.value: 9,
                    AreaType.ROOM.value: 9,
                    AreaType.CORRIDOR.value: 11,
                    AreaType.STOREROOM.value: 1,
                    AreaType.SHAFT.value: 9,
                    AreaType.KITCHEN.value: 9,
                },
            ),
            (
                5797,
                {
                    AreaType.ROOM.value: 7,
                    AreaType.STOREROOM.value: 7,
                    AreaType.SHAFT.value: 4,
                    AreaType.CORRIDOR.value: 4,
                    AreaType.BALCONY.value: 1,
                    AreaType.ELEVATOR.value: 1,
                },
            ),
            (
                5825,
                {
                    AreaType.ROOM.value: 12,
                    AreaType.BATHROOM.value: 6,
                    AreaType.SHAFT.value: 6,
                    AreaType.KITCHEN.value: 3,
                    AreaType.STAIRCASE.value: 3,
                    AreaType.CORRIDOR.value: 3,
                    AreaType.STOREROOM.value: 1,
                    AreaType.BALCONY.value: 1,
                    AreaType.ELEVATOR.value: 1,
                },
            ),
            (
                6951,
                {
                    AreaType.SHAFT.value: 9,
                    AreaType.BALCONY.value: 7,
                    AreaType.BATHROOM.value: 6,
                    AreaType.ROOM.value: 9,
                    AreaType.CORRIDOR.value: 6,
                    AreaType.KITCHEN.value: 4,
                    AreaType.STOREROOM.value: 2,
                    AreaType.ELEVATOR.value: 2,
                },
            ),
        ],
    )
    def test_get_plan_areas_autoclassified_mocked_areas_regression(
        mocker,
        client,
        login,
        make_classified_plans,
        building,
        plan,
        fixture_plan_id,
        expected_count,
    ):
        def sort_areas(areas):
            return sorted([area for area in areas], key=lambda z: z["id"])

        make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
        db_areas = [area for area in AreaDBHandler.find(plan_id=plan["id"])]

        url = get_address_for(
            blueprint=areas_app,
            view_function=get_areas_autoclassified,
            plan_id=plan["id"],
            use_external_address=False,
        )

        db_areas_defined = [
            area for area in db_areas if area["area_type"] != AreaType.NOT_DEFINED.name
        ]
        db_areas_made_undefined = [area.copy() for area in db_areas_defined]
        for db_area in db_areas_made_undefined:
            db_area["area_type"] = AreaType.NOT_DEFINED.name

        mocker.patch.object(AreaDBHandler, "find", return_value=db_areas_defined)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert sort_areas(response.json) == sort_areas(db_areas_defined)

        mocker.patch.object(AreaDBHandler, "find", return_value=db_areas_made_undefined)
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, response.json

        # NOTE: There are some errors in the expected results, this is more like a full-chain regression
        #       test.
        assert Counter([area["area_type"] for area in response.json]) == expected_count
        layout = PlanLayoutHandler(plan_id=plan["id"]).get_layout(scaled=False)
        AreaHandler.map_existing_areas(
            brooks_areas=layout.areas,
            db_areas=response.json,
            raise_on_inconsistency=True,
        )


@login_as([USER_ROLE.DMS_LIMITED.name])
def test_get_unit_areas(client, login, site_with_3_units):
    DmsPermissionDBHandler.add(
        site_id=site_with_3_units["site"]["id"],
        user_id=login["user"]["id"],
        rights=DMS_PERMISSION.READ.name,
    )

    num_areas = []
    for unit in site_with_3_units["units"]:
        url = get_address_for(
            blueprint=areas_app,
            view_function=get_areas_by_unit_id,
            unit_id=unit["id"],
            use_external_address=False,
        )
        response = client.get(url)

        assert response.status_code == HTTPStatus.OK
        num_areas.append(len(response.json))

    assert sorted(num_areas) == [9, 10, 12]


def get_area_type_sorted(area_type: AreaType, biggest: bool = True) -> dict:
    return sorted(
        AreaDBHandler.find(area_type=area_type.name),
        key=lambda x: wkt.loads(x["scaled_polygon"]).area,
    )[-1 if biggest else 0]


class TestPutAreas:
    @staticmethod
    def test_put_plan_areas_happy_path(client, plan, login, areas_accessible_areas):
        not_defined_area = get_area_type_sorted(area_type=AreaType.NOT_DEFINED)
        staircase_area = get_area_type_sorted(area_type=AreaType.STAIRCASE)
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )

        all_areas = {
            x["id"]: x["area_type"] for x in AreaDBHandler.find(plan_id=plan["id"])
        }
        assert all(
            a not in {AreaType.BALCONY.name, AreaType.KITCHEN_DINING.name}
            for a in all_areas.values()
        )
        all_areas[not_defined_area["id"]] = AreaType.BALCONY.name
        all_areas[staircase_area["id"]] = AreaType.KITCHEN_DINING.name
        response = client.put(url, json={"areas": all_areas})
        assert response.status_code == HTTPStatus.ACCEPTED, response.json
        assert len(response.json["errors"]) == 1
        assert [error["is_blocking"] for error in response.json["errors"]] == [0]

        areas = AreaDBHandler.find(plan_id=plan["id"])
        assert {area["id"]: area["area_type"] for area in areas} == all_areas

    @staticmethod
    def test_put_plan_areas_validations_wrong_area(client, plan, areas_db, login):
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.put(url, json={"areas": {areas_db[0]["id"]: "RANDOM_AREA"}})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @staticmethod
    def test_put_plan_areas_validations_empty(client, plan, areas_db, login):
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.put(url, json={"areas": {}})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @staticmethod
    def test_put_plan_areas_validations_wrong_plan(
        client,
        plan_annotated,
        make_annotations,
        areas_db,
        login,
        plan_b,
        area_polygon_wkt,
    ):
        make_annotations(plan_b)
        area_plan_b = AreaDBHandler.add(
            plan_id=plan_b["id"],
            coord_x=100.0,
            coord_y=200.0,
            area_type=AreaType.NOT_DEFINED.name,
            scaled_polygon=area_polygon_wkt,
        )
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan_annotated["id"],
            use_external_address=False,
        )
        response = client.put(
            url, json={"areas": {area_plan_b["id"]: AreaType.ROOM.name}}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Areas not belonging to the plan" in response.json["msg"]

    @staticmethod
    def test_put_plan_areas_validation_exception_partial_areas(
        client, plan, login, areas_accessible_areas
    ):
        area_with_shaft = AreaDBHandler.get_by(area_type=AreaType.SHAFT.name)

        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.put(
            url, json={"areas": {area_with_shaft["id"]: AreaType.ROOM.name}}
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Areas not belonging to the plan" in response.json["msg"]

    @staticmethod
    def test_put_plan_areas_validation_is_blocking_error(
        client, plan, login, areas_accessible_areas
    ):
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )

        all_areas = AreaDBHandler.find(plan_id=plan["id"])
        shaft_area = AreaDBHandler.get_by(area_type=AreaType.SHAFT.name)
        new_data = {
            "areas": {
                area["id"]: area["area_type"]
                for area in all_areas
                if area["area_type"] != AreaType.SHAFT.name
            }
        }
        new_data["areas"][shaft_area["id"]] = AreaType.ROOM.name

        response = client.put(url, json=new_data)
        assert response.status_code == HTTPStatus.ACCEPTED
        assert len(response.json["errors"]) == 2
        assert {error["is_blocking"] for error in response.json["errors"]} == {1, 0}

    @staticmethod
    @pytest.mark.parametrize(
        "area_type, valid",
        [
            (AreaType.VOID.name, True),
            (AreaType.OUTDOOR_VOID.name, True),
            *(
                (x.name, True)
                for x in sorted(
                    CLASSIFICATIONS.UNIFIED.value().get_children(SIACategory.FF),
                    key=str,
                )
            ),
        ],
    )
    def test_put_plan_areas_shafts_void_ff_where_shaft(
        client, plan, login, areas_accessible_areas, site, area_type, valid
    ):
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        all_areas = AreaDBHandler.find(plan_id=plan["id"])
        shaft_area = AreaDBHandler.get_by(area_type=AreaType.SHAFT.name)
        new_data = {
            "areas": {
                area["id"]: area["area_type"]
                for area in all_areas
                if area["area_type"] != AreaType.SHAFT.name
            }
        }
        new_data["areas"][shaft_area["id"]] = area_type
        response = client.put(url, json=new_data)

        assert response.status_code == HTTPStatus.ACCEPTED
        if not valid:
            assert response.json["errors"]
        assert bool(AreaDBHandler.find(area_type=area_type)) == valid

    @staticmethod
    def test_put_plan_areas_validation_exception_shaft_areas_without_feature(
        client, plan, login, areas_accessible_areas
    ):
        url = get_address_for(
            blueprint=areas_app,
            view_function=AreasView,
            plan_id=plan["id"],
            use_external_address=False,
        )

        all_areas = AreaDBHandler.find(plan_id=plan["id"])
        area_not_defined = get_area_type_sorted(area_type=AreaType.NOT_DEFINED)
        new_data = {
            "areas": {
                area["id"]: area["area_type"]
                for area in all_areas
                if area["id"] != area_not_defined["id"]
            }
        }
        new_data["areas"][area_not_defined["id"]] = AreaType.SHAFT.name

        response = client.put(url, json=new_data)
        assert response.status_code == HTTPStatus.ACCEPTED, response.json
        assert {error["type"] for error in response.json["errors"]} == {
            ViolationType.SHAFT_WITHOUT_SHAFT_FEATURE.name,
            ViolationType.SHAFT_HAS_OPENINGS.name,
        }
        assert {error["is_blocking"] for error in response.json["errors"]} == {1}
        assert response.status_code == HTTPStatus.ACCEPTED


def test_validate_plan_areas(client, site, plan, login, areas_accessible_areas, mocker):
    from handlers.validators import (
        PlanClassificationBalconyHasRailingValidator,
        PlanClassificationDoorNumberValidator,
        PlanClassificationFeatureConsistencyValidator,
        PlanClassificationRoomWindowValidator,
        PlanClassificationShaftValidator,
    )

    validators = (
        PlanClassificationShaftValidator,
        PlanClassificationDoorNumberValidator,
        PlanClassificationFeatureConsistencyValidator,
        PlanClassificationRoomWindowValidator,
        PlanClassificationBalconyHasRailingValidator,
    )
    validator_spies = [mocker.spy(validator, "validate") for validator in validators]

    url = get_address_for(
        blueprint=areas_app,
        view_function=validate_classifications,
        plan_id=plan["id"],
        use_external_address=False,
    )

    all_areas = AreaDBHandler.find(plan_id=plan["id"])
    area_not_defined = get_area_type_sorted(area_type=AreaType.NOT_DEFINED)
    new_data = {
        "areas": {
            area["id"]: area["area_type"]
            for area in all_areas
            if area["id"] != area_not_defined["id"]
        }
    }
    new_data["areas"][area_not_defined["id"]] = AreaType.SHAFT.name

    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"full_slam_results": "SUCCESS", "pipeline_and_qa_complete": True},
    )
    response = client.post(url, json=new_data)
    assert response.status_code == HTTPStatus.ACCEPTED
    assert len(response.json["errors"]) == 2
    assert {error["type"] for error in response.json["errors"]} == {
        ViolationType.SHAFT_WITHOUT_SHAFT_FEATURE.name,
        ViolationType.SHAFT_HAS_OPENINGS.name,
    }

    for spy in validator_spies:
        assert spy.call_count == 1

    site = SiteDBHandler.get_by(
        id=site["id"], output_columns=["full_slam_results", "pipeline_and_qa_complete"]
    )
    assert (
        site["full_slam_results"] == "SUCCESS"
        and site["pipeline_and_qa_complete"] is True
    )


@pytest.mark.parametrize("georeferenced", [True, False])
def test_ensure_rotation_point_not_updated_if_already_georeferenced(
    celery_eager,
    plan,
    react_planner_background_image_one_unit,
    georeferenced,
    mocker,
):
    mocker.patch.object(
        ReactPlannerHandler,
        "migrate_data_if_old_version",
        return_value=react_planner_background_image_one_unit,
    )
    mocker.patch.object(
        ReactPlannerHandler,
        "get_by_migrated",
        return_value={"data": react_planner_background_image_one_unit},
    )
    mocker.patch.object(
        ReactPlannerHandler,
        "_saves_data_georef_invalidated",
        return_value={"data": {"scale": 1}},
    )
    mocker.patch.object(ReactPlannerHandler, "_validate_plan_data", return_value=[])
    mocker.patch.object(PlanHandler, "is_georeferenced", return_value=georeferenced)
    mocked_update_rotation = mocker.patch.object(PlanHandler, "update_rotation_point")

    import handlers.plan_utils

    mocker.patch.object(handlers.plan_utils, "create_areas_for_plan")

    ReactPlannerHandler().store_plan_data(
        plan_id=plan["id"],
        plan_data=react_planner_background_image_one_unit,
        validated=True,
    )

    assert mocked_update_rotation.call_count == 0 if georeferenced else 1


def test_correct_position_of_validation_errors_in_classification_for_react(
    client,
    celery_eager,
    plan,
    react_planner_background_image_one_unit,
):
    ReactPlannerHandler().store_plan_data(
        plan_id=plan["id"],
        plan_data=react_planner_background_image_one_unit,
        validated=True,
    )

    areas = AreaDBHandler.find(
        plan_id=plan["id"], output_columns=["id", "scaled_polygon"]
    )
    smallest_area = sorted(
        areas, key=lambda area: wkt.loads(area["scaled_polygon"]).area
    )[0]

    new_data = {
        "areas": {
            area["id"]: AreaType.NOT_DEFINED.value
            if area["id"] != smallest_area["id"]
            else AreaType.BALCONY.value
            for area in areas
        }
    }

    url = get_address_for(
        blueprint=areas_app,
        view_function=validate_classifications,
        plan_id=plan["id"],
        use_external_address=False,
    )
    validation_response = client.post(url, json=new_data)
    sorted_errors = sorted(validation_response.json["errors"], key=lambda k: k["text"])
    bathtub_error = [
        error
        for error in sorted_errors
        if error["type"] == "FEATURE_DOES_NOT_MATCH_ROOM_TYPE"
    ][0]

    validation_error_position = shape(bathtub_error["position"])

    assert validation_error_position.x == pytest.approx(expected=840.25, abs=0.01)
    assert validation_error_position.y == pytest.approx(expected=779.11, abs=0.01)
