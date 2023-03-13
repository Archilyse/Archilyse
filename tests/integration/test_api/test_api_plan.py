import copy
import json
import re
from collections import Counter
from dataclasses import asdict
from http import HTTPStatus

import pytest
from shapely.geometry import shape

from brooks.models.violation import ViolationType
from brooks.types import AreaType
from brooks.util.projections import project_geometry
from common_utils.constants import DMS_PERMISSION, REGION, UNIT_USAGE, USER_ROLE
from handlers import GCloudStorageHandler, SiteHandler
from handlers.db import (
    AreaDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
)
from handlers.editor_v2.schema import ReactPlannerData
from handlers.utils import get_client_bucket_name
from handlers.validators.linking.unit_linking_validator import UnitLinkingValidator
from slam_api.apis.plan import (
    PlanFloorsView,
    PlanUnitsView,
    PlanView,
    get_footprint_api,
    get_georeferenced_plans_under_same_site,
    get_plan_layout_unscaled_for_pipeline,
    get_plan_pipeline,
    get_plan_raw_image,
    get_simple_brooks_model_api,
    patch_plan_heights,
    plan_app,
    save_georeferencing_data,
    set_as_masterplan,
    validate_georeferencing,
)
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for


@pytest.fixture
def empty_annotations(plan):
    return ReactPlannerProjectsDBHandler.add(
        plan_id=plan["id"], data=asdict(ReactPlannerData())
    )


@pytest.fixture
def plan_2494_scaled(plan, georef_plan_values):
    return PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values=georef_plan_values[2494],
    )


class TestBrooksModel:
    @staticmethod
    def test_get_plan_layout_unscaled_for_pipeline(
        mocker, client, plan, annotations_finished, login
    ):
        """ "
        Given a valid test user
        And an existing plan id
        And valid annotations in the DB
        when the brooks model classified is requested
        then endpoint should return a valid brooks model
        """
        deepcopy_spy = mocker.spy(copy, "deepcopy")
        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_plan_layout_unscaled_for_pipeline,
                plan_id=plan["id"],
            )
        )
        assert plan_response.status_code == HTTPStatus.OK
        assert "id" in plan_response.json
        # marshmallow seem to be making calls to deepcopy when the API has arguments defined
        assert deepcopy_spy.call_count == 1

    @staticmethod
    def test_get_brooks_model_with_errors(
        client, plan, login, react_planner_background_image_full_plan
    ):
        ReactPlannerProjectsDBHandler.add(
            plan_id=plan["id"],
            data=react_planner_background_image_full_plan,
        )
        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_plan_layout_unscaled_for_pipeline,
                plan_id=plan["id"],
                validate=True,
            )
        )
        assert plan_response.status_code == HTTPStatus.OK
        errors = Counter([error["type"] for error in plan_response.json["errors"]])
        assert errors == {
            ViolationType.OPENING_OVERLAPS_ANOTHER_OPENING.name: 4,
        }

    @staticmethod
    def test_get_brooks_footprint(client, plan, plan_classified_scaled, login):
        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_footprint_api,
                plan_id=plan["id"],
            )
        )
        assert plan_response.status_code == HTTPStatus.OK
        assert isinstance(plan_response.json["coordinates"], list)
        assert isinstance(plan_response.json["coordinates"][0], list)
        assert isinstance(plan_response.json["coordinates"][0][0], list)
        assert isinstance(plan_response.json["coordinates"][0][0][0], float)
        assert plan_response.json["type"] == "Polygon"
        assert project_geometry(
            geometry=shape(plan_response.json),
            crs_from=REGION.LAT_LON,
            crs_to=REGION.CH,
        ).area == pytest.approx(186.602, abs=10**-3)

    def test_get_brooks_footprint_react_is_scaled(
        self,
        client,
        plan_annotated,
        login,
    ):
        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_footprint_api,
                plan_id=plan_annotated["id"],
            )
        )
        assert plan_response.status_code == HTTPStatus.OK

        site = SiteDBHandler.get_by(id=plan_annotated["site_id"])

        georeferenced_footprint = shape(plan_response.json)

        assert georeferenced_footprint.centroid.x == pytest.approx(
            expected=site["lon"], abs=1e-7
        )
        assert georeferenced_footprint.centroid.y == pytest.approx(
            expected=site["lat"], abs=1e-7
        )

        assert project_geometry(
            geometry=georeferenced_footprint,
            crs_from=REGION.LAT_LON,
            crs_to=REGION.CH,
        ).area == pytest.approx(expected=57.78, abs=0.01)


class TestPlanGeoreferenceValues:
    @staticmethod
    def test_plan_georeference_endpoint(
        client,
        make_plans,
        site,
        building,
        login,
        annotations_path,
        make_classified_plans,
    ):
        plan1, plan2, plan3 = make_plans(building, building, building)
        make_classified_plans(plan1, plan2)

        new_values = {"lon": 7.603514874587979, "lat": 47.5655062991789}
        SiteDBHandler.update(item_pks=dict(id=site["id"]), new_values=new_values)

        PlanDBHandler.update(
            item_pks=dict(id=plan1["id"]),
            new_values=dict(
                georef_rot_x=2323.50396161757,
                georef_rot_y=-1567.21560230765,
                georef_x=7.572675060989316,  # site location projected +- the georef_rot point
                georef_y=47.5796408706309,
                georef_scale=1.07,
                georef_rot_angle=-132.5,
            ),
        )

        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_georeferenced_plans_under_same_site,
                plan_id=plan2["id"],
            )
        )

        assert plan_response.status_code == HTTPStatus.OK

        plans_georeferenced = plan_response.json["data"]
        assert plans_georeferenced[0]["id"] == plan1["id"]
        assert len(plans_georeferenced) == 1

        # As georef info is generated from site coordinates, they should be close
        plan_centroid = shape(plans_georeferenced[0]["footprint"]).centroid
        site_location = SiteHandler.get_lat_lon_location(site_info=site)
        assert 250 > plan_centroid.distance(site_location) > 0

    def test_other_plans_georeferenced_footprints_are_scaled(
        self, client, plan_annotated, mocker
    ):
        PlanDBHandler.update(
            item_pks={"id": plan_annotated["id"]},
            new_values={
                "georef_rot_x": 0,
                "georef_rot_y": 0,
                "georef_rot_angle": 0,
                "georef_x": 0,
                "georef_y": 0,
            },
        )
        mocker.patch.object(
            PlanDBHandler,
            "get_other_georeferenced_plans_by_site",
            return_value=[PlanDBHandler.get_by(id=plan_annotated["id"])],
        )

        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_georeferenced_plans_under_same_site,
                plan_id=plan_annotated["id"],
            )
        )
        assert plan_response.status_code == HTTPStatus.OK
        footprint_lat_lon = shape(plan_response.json["data"][0]["footprint"])
        footprint_lv95 = project_geometry(
            geometry=footprint_lat_lon,
            crs_from=REGION.LAT_LON,
            crs_to=REGION.CH,
        )
        assert footprint_lv95.area == pytest.approx(expected=57.78, abs=0.01)

    @staticmethod
    @pytest.mark.parametrize(
        "building1, building2, floor_number1, floor_number2, expect_violations",
        [
            (0, 0, 0, 1, []),  # Same building, same floor
            (0, 1, 0, 1, []),  # Different building, different floor
            (
                0,
                1,
                0,
                0,
                [
                    "plan 1 intersects with plan 2 (building 3, floor 0) by more than 5.0%"
                ],
            ),  # Same floor, different building
            (
                1,
                0,
                1,
                1,
                [
                    "plan 1 intersects with plan 2 (building 2, floor 1) by more than 5.0%"
                ],
            ),  # Same floor, different building
        ],
    )
    def test_georeferencing_overlap_warnings(
        mocker,
        client,
        make_buildings,
        make_plans,
        make_floor,
        site,
        building,
        login,
        annotations_path,
        make_annotations,
        building1,
        building2,
        floor_number1,
        floor_number2,
        expect_violations,
    ):
        # Setup entities according to test config
        buildings = make_buildings(site, site)
        plans = make_plans(buildings[building1], buildings[building2])

        make_floor(buildings[building1], plans[0], floor_number1)
        make_floor(buildings[building2], plans[1], floor_number2)

        # Setup georef parameters
        make_annotations(*plans)
        new_values = {"lon": 7.603514874587979, "lat": 47.5655062991789}
        SiteDBHandler.update(item_pks=dict(id=site["id"]), new_values=new_values)
        for plan in plans:
            PlanDBHandler.update(
                item_pks=dict(id=plan["id"]),
                new_values=dict(
                    georef_rot_x=2323.50396161757,
                    georef_rot_y=-1567.21560230765,
                    georef_x=7.572675060989316,  # site location projected +- the georef_rot point
                    georef_y=47.5796408706309,
                    georef_rot_angle=-132.5,
                ),
            )

        # To avoid many DB calls
        planner_get_by_spy = mocker.spy(ReactPlannerProjectsDBHandler, "get_by")
        planner_find_in_spy = mocker.spy(ReactPlannerProjectsDBHandler, "find_in")
        site_get_by_spy = mocker.spy(SiteDBHandler, "get_by")
        plan_get_by_spy = mocker.spy(PlanDBHandler, "get_by")
        # Validate
        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=validate_georeferencing,
                plan_id=plans[0]["id"],
            )
        )

        assert set(plan_response.json["data"]) == set(expect_violations)
        assert (
            planner_find_in_spy.call_count == 1
        )  # To get all the other georeferenced plans
        assert planner_get_by_spy.call_count <= 1  # To get the target id data
        assert (
            site_get_by_spy.call_count <= 1
        )  # To get the target site id info for georef projection
        assert plan_get_by_spy.call_count == 1


class TestPlanUnitEndpoint:
    @staticmethod
    def test_unit_get_endpoint(client, plan, unit, login):
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, response.data
        assert response.json[0]["id"] == unit["id"], response.data

    @pytest.mark.parametrize(
        "has_permission, expected_response_status",
        [(True, HTTPStatus.OK), (False, HTTPStatus.FORBIDDEN)],
    )
    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_get_units_dms_limited(
        self,
        client,
        client_db,
        site,
        plan,
        unit,
        login,
        make_sites,
        make_buildings,
        make_floor,
        make_plans,
        make_units,
        has_permission,
        expected_response_status,
    ):
        from handlers.db import DmsPermissionDBHandler

        if has_permission:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=DMS_PERMISSION.READ.name,
            )
        (other_site,) = make_sites(*(client_db,), group_id=login["group"]["id"])

        (other_building,) = make_buildings(*(other_site,))

        (other_plan,) = make_plans(*(other_building,))

        other_floor = make_floor(
            building=other_building, plan=other_plan, floornumber=1
        )
        make_units(*(other_floor,))
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == expected_response_status, response.data
        if expected_response_status == HTTPStatus.OK:
            assert len(response.json) == 1
            assert {unit["id"] for unit in response.json} == {unit["id"]}
        elif expected_response_status == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to access this plan"

    @staticmethod
    def test_unit_get_endpoint_floor_filter_valid(client, plan, floor, unit, login):
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            floor_id=floor["id"],
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, response.data
        assert response.json[0]["id"] == unit["id"], response.data

    @staticmethod
    def test_unit_get_endpoint_floor_filter_not_valid(client, plan, unit, login):
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            floor_id=99999,
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, response.data
        assert not response.json

    @staticmethod
    def test_unit_put_endpoint(client, plan, make_annotations, unit, login):
        make_annotations(plan)
        put_url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        get_url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.get(get_url)
        unit_list = json.loads(response.data)
        mock_client_id = "123"
        unit_list = [
            {
                "id": x["id"],
                "client_id": mock_client_id,
                "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
            }
            for x in unit_list
        ]
        response = client.put(put_url, json=unit_list)

        assert response.status_code == HTTPStatus.OK, response.data
        assert response.json[0]["client_id"] != unit["client_id"], response.data

    @staticmethod
    @pytest.mark.parametrize("unit_usage", UNIT_USAGE)
    def test_unit_put_endpoint_unit_usage(
        client, plan, unit, areas_db, login, unit_usage, mocker
    ):
        mocker.patch.object(
            UnitLinkingValidator, "violations_by_unit_client_id", return_value={}
        )
        put_url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        get_url = get_address_for(
            blueprint=plan_app,
            view_function=PlanUnitsView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.get(get_url)
        unit_list = json.loads(response.data)
        mock_client_id = "123"
        unit_list = [
            {"id": x["id"], "client_id": mock_client_id, "unit_usage": unit_usage.name}
            for x in unit_list[:1]
        ]
        response = client.put(put_url, json=unit_list)

        assert response.status_code == HTTPStatus.OK, response.data
        assert response.json[0]["client_id"] != unit["client_id"], response.data
        assert response.json[0]["unit_usage"] == unit_usage.name, response.data

    @staticmethod
    def test_unit_put_endpoint_unit_usage_return_violations(
        mocker,
        client,
        login,
        make_react_annotation_fully_pipelined,
        react_planner_background_image_full_plan,
    ):
        """
        Test that if a unit is linked with usage type residential, but contains commercial areas the route returns violations
        """
        db_data = make_react_annotation_fully_pipelined(
            react_planner_background_image_full_plan
        )

        unit = sorted(
            db_data["units"],
            key=lambda unit: len(
                UnitAreaDBHandler.find(unit_id=unit["id"], output_columns=["area_id"])
            ),
        )[
            0
        ]  # Asserts that always the same unit is used for the test

        area = sorted(
            [
                area
                for area in AreaDBHandler.find_in(
                    id=[
                        area["area_id"]
                        for area in UnitAreaDBHandler.find(
                            unit_id=unit["id"], output_columns=["area_id"]
                        )
                    ],
                    output_columns=["id", "coord_x"],
                )
            ],
            key=lambda area: area["coord_x"],
        )[
            0
        ]  # Asserts that always the same area is used for the test

        AreaDBHandler.update(
            item_pks={"id": area["id"]},
            new_values={"area_type": AreaType.COMMUNITY_ROOM.name},
        )  # Creates an area with a commercial area type which should create a violation

        unit_list = [
            {
                "id": unit["id"],
                "client_id": "some_id",
                "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
            }
        ]
        # DB N+1 calls, performance checks
        area_find_spy = mocker.spy(
            AreaDBHandler,
            "find",
        )
        unit_area_find_in_spy = mocker.spy(
            UnitAreaDBHandler,
            "find_in",
        )
        planner_project_get_spy = mocker.spy(
            ReactPlannerProjectsDBHandler,
            "get_by",
        )
        response = client.put(
            get_address_for(
                blueprint=plan_app,
                view_function=PlanUnitsView,
                plan_id=db_data["plan"]["id"],
                use_external_address=False,
            ),
            json=unit_list,
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert len(response.json["errors"]) == 1
        assert (
            response.json["errors"][0]["type"]
            == ViolationType.AREA_TYPE_NOT_ALLOWED_FOR_UNIT_USAGE_TYPE.name
        )
        assert response.json["errors"][0]["is_blocking"]
        assert response.json["errors"][0]["position"]["coordinates"] == pytest.approx(
            expected=[1413.14, 429.32], abs=1e-6
        )
        assert area_find_spy.call_count == 1
        assert unit_area_find_in_spy.call_count == 1
        assert planner_project_get_spy.call_count == 1


@login_as(["TEAMMEMBER"])
def test_plan_get_endpoint_not_existing(client, plan, login):
    url = get_address_for(
        blueprint=plan_app,
        view_function=PlanUnitsView,
        plan_id=123,
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK, response.data
    assert response.json == []


def test_get_pipelines_by_plan_endpoint(client, site, plan, building, login):
    url = get_address_for(
        blueprint=plan_app,
        view_function=get_plan_pipeline,
        plan_id=plan["id"],
        use_external_address=False,
    )

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK, response.data
    json_response = response.json
    json_response[0].pop("created")
    json_response[0].pop("updated")
    assert json_response == [
        {
            "client_building_id": building["client_building_id"],
            "building_housenumber": building["housenumber"],
            "building_id": building["id"],
            "classified": False,
            "client_site_id": "Leszku-payaso",
            "floor_numbers": [],
            "georeferenced": False,
            "id": plan["id"],
            "labelled": False,
            "splitted": False,
            "units_linked": False,
            "is_masterplan": False,
        }
    ]


class TestPlanView:
    @login_as(["TEAMMEMBER"])
    def test_plan_get_endpoint(self, client, plan, login):
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanView,
            plan_id=plan["id"],
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, response.data
        assert response.json == plan, response.data

    @login_as(["TEAMMEMBER"])
    def test_patch_plan_with_georef(
        self, client, plan_classified_scaled_georeferenced, login, annotations_path
    ):
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanView,
            plan_id=plan_classified_scaled_georeferenced["id"],
        )
        georef_info = {
            "georef_x": 1,
            "georef_y": 2,
            "georef_rot_angle": 3,
        }

        response = client.patch(url, json=georef_info)
        assert response.status_code == HTTPStatus.OK, response.data
        response_json = response.get_json()
        for key, value in georef_info.items():
            assert response_json.pop(key) == value
        response_json.pop("updated")

        plan = {
            k: v
            for k, v in plan_classified_scaled_georeferenced.items()
            if k not in georef_info
        }
        plan.pop("updated")
        assert response_json == plan

    @login_as(["TEAMMEMBER"])
    def test_patch_plan_partial(
        self, client, plan_classified_scaled_georeferenced, login
    ):
        """Using plan_image_b as it has georef data already"""
        prev_georef_info = {
            k: v
            for k, v in plan_classified_scaled_georeferenced.items()
            if k.startswith("georef")
        }
        url = get_address_for(
            blueprint=plan_app,
            view_function=PlanView,
            plan_id=plan_classified_scaled_georeferenced["id"],
        )
        new_value = 99999.9
        body = {
            "georef_scale": new_value,
        }
        response = client.patch(url, json=body)

        assert response.status_code == HTTPStatus.OK, response.data
        new_georef_info = {
            k: v for k, v in response.get_json().items() if k.startswith("georef")
        }
        assert new_georef_info.pop("georef_scale") == new_value

        prev_georef_info.pop("georef_scale")
        # Using pytest.aprox are there slight float differences that are irrelevant
        assert new_georef_info == pytest.approx(prev_georef_info)

    @pytest.mark.parametrize(
        "body,expected_response_code",
        [
            ({"not_valid_key": "payaso"}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ({"georef_scale": "payaso"}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ({}, HTTPStatus.UNPROCESSABLE_ENTITY),
            ({"georef_scale": 1.12, "archi": "lyse"}, HTTPStatus.UNPROCESSABLE_ENTITY),
        ],
    )
    def test_patch_plan_wrong(self, client, plan, login, body, expected_response_code):
        url = get_address_for(
            blueprint=plan_app, view_function=PlanView, plan_id=plan["id"]
        )
        response = client.patch(url, json=body)
        assert response.status_code == expected_response_code, response.data

    def test_patch_plan_incorrect_plan_id(self, client, plan, login):
        url = get_address_for(blueprint=plan_app, view_function=PlanView, plan_id=123)
        georef_scale = {"georef_scale": 1.12}
        response = client.patch(url, json=georef_scale)
        assert response.status_code == HTTPStatus.NOT_FOUND, response.data

    @staticmethod
    def test_delete_api_plan(client, plan):
        url = get_address_for(
            blueprint=plan_app, view_function=PlanView, plan_id=plan["id"]
        )
        response = client.delete(url)
        assert response.status_code == HTTPStatus.OK, response.data
        assert len(PlanDBHandler.find()) == 0


class TestSimpleBrooks:
    @pytest.mark.parametrize("scaled", (True, False))
    @pytest.mark.parametrize("georeferenced", (True, False))
    @pytest.mark.parametrize("classified", (True, False))
    def test_api_get_simple_layout(
        self,
        mocker,
        client,
        plan_classified_scaled_georeferenced,
        scaled,
        georeferenced,
        classified,
    ):
        deepcopy_spy = mocker.spy(copy, "deepcopy")
        plan_response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_simple_brooks_model_api,
                plan_id=plan_classified_scaled_georeferenced["id"],
                scaled=scaled,
                georeferenced=georeferenced,
                classified=classified,
            )
        )
        assert plan_response.status_code == HTTPStatus.OK
        deepcopy_spy.assert_not_called()
        assert {"features", "openings", "separators"} == set(plan_response.json.keys())


class TestRawImageRequest:
    @staticmethod
    @login_as([USER_ROLE.TEAMMEMBER.name])
    def test_plan_download_image(
        client, login, plan, mocked_gcp_download_file_as_bytes, client_db
    ):
        response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_plan_raw_image,
                plan_id=plan["id"],
            ),
        )

        assert response.status_code == HTTPStatus.OK
        assert response.data == mocked_gcp_download_file_as_bytes.return_value

        mocked_gcp_download_file_as_bytes.assert_called_with(
            bucket_name=get_client_bucket_name(client_id=client_db["id"]),
            source_file_name=GCloudStorageHandler._convert_media_link_to_file_in_gcp(
                plan["image_gcs_link"]
            ),
        )

    @staticmethod
    @login_as([USER_ROLE.TEAMMEMBER.name])
    def test_plan_download_image_missing_bucket_returns_404(
        mocker, client, login, plan, client_db
    ):
        mocker.patch.object(
            GCloudStorageHandler,
            GCloudStorageHandler._lookup_bucket.__name__,
            return_value=None,
        )
        response = client.get(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=get_plan_raw_image,
                plan_id=plan["id"],
            ),
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert re.match("Bucket .* does not exist", response.json["msg"])


@pytest.mark.parametrize(
    "default_wall_height,default_door_height,default_window_lower_edge,default_window_upper_edge,default_ceiling_slab_height,expected_validation_errors",
    [
        (2.0, 1.5, 0.1, 1.9, 0.3, None),
        (2.0, 2.1, 0.1, 1.9, 0.3, ["door height must be smaller than wall height."]),
        (
            2.0,
            1.5,
            0.1,
            2.1,
            0.3,
            ["upper window edge must be smaller than wall height."],
        ),
        (
            2.0,
            1.5,
            1.9,
            1.8,
            0.3,
            ["lower window edge must be smaller than upper window edge."],
        ),
        (
            200,
            1.5,
            0.1,
            1.9,
            0.3,
            ["Must be greater than or equal to 0 and less than or equal to 20."],
        ),
        (
            -2,
            1.5,
            0.1,
            1.9,
            0.3,
            ["Must be greater than or equal to 0 and less than or equal to 20."],
        ),
        (
            2.0,
            1.5,
            0.1,
            1.9,
            3.0,
            ["Must be greater than or equal to 0 and less than or equal to 2."],
        ),
    ],
)
@login_as([USER_ROLE.TEAMMEMBER.name])
def test_plan_update_heights(
    client,
    login,
    plan,
    client_db,
    default_wall_height,
    default_door_height,
    default_window_lower_edge,
    default_window_upper_edge,
    default_ceiling_slab_height,
    expected_validation_errors,
):
    payload = {
        "default_wall_height": default_wall_height,
        "default_door_height": default_door_height,
        "default_window_lower_edge": default_window_lower_edge,
        "default_window_upper_edge": default_window_upper_edge,
        "default_ceiling_slab_height": default_ceiling_slab_height,
    }
    response = client.patch(
        get_address_for(
            blueprint=plan_app,
            use_external_address=False,
            view_function=patch_plan_heights,
            plan_id=plan["id"],
        ),
        json=payload,
    )

    if expected_validation_errors is None:
        assert response.status_code == HTTPStatus.OK
        updated_plan = PlanDBHandler.get_by(id=plan["id"])
        assert {k: updated_plan[k] for k in payload} == payload
    else:
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert [
            error
            for field_errors in response.json["errors"]["json"].values()
            for error in field_errors
        ] == expected_validation_errors


class TestUpdateGeoreferenceData:
    @pytest.fixture
    def prepare_plans(self, site, building, plan, make_plans, make_buildings):
        def _internal(georef_data=None, building_has_masterplan=False):
            georef_data = georef_data or {}
            (other_plan_from_same_building,) = make_plans(building)
            (other_plan_from_other_building,) = make_plans(*make_buildings(site))
            new_values = (
                {"is_masterplan": True, **georef_data}
                if building_has_masterplan
                else georef_data
            )
            PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=new_values)
            return plan, other_plan_from_same_building, other_plan_from_other_building

        return _internal

    @pytest.mark.parametrize("building_has_masterplan", [True])
    def test_update_georeference_data(
        self, client, prepare_plans, building_has_masterplan
    ):
        georef_data = {"georef_rot_x": 4, "georef_rot_y": 5}
        (
            plan,
            other_plan_from_same_building,
            other_plan_from_other_building,
        ) = prepare_plans(
            georef_data=georef_data, building_has_masterplan=building_has_masterplan
        )

        payload = {"georef_rot_angle": 1, "georef_x": 2, "georef_y": 3}
        response = client.put(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=save_georeferencing_data,
                plan_id=plan["id"],
            ),
            json=payload,
        )
        assert response.status_code == HTTPStatus.OK

        expected_georef_data_updated = {**georef_data, **payload}
        expected_georef_data_not_updated = {
            k: None for k in expected_georef_data_updated.keys()
        }

        db_plans_by_id = {
            plan["id"]: plan for plan in PlanDBHandler.find(site_id=plan["site_id"])
        }

        # plan got updated with the latest georef info
        assert (
            not expected_georef_data_updated.items()
            - db_plans_by_id[plan["id"]].items()
        )

        # Same building's plans are updated only if the building has a masterplan
        expected_georef_data_other_plan_same_building = (
            expected_georef_data_updated
            if building_has_masterplan
            else expected_georef_data_not_updated
        )
        assert not (
            expected_georef_data_other_plan_same_building.items()
            - db_plans_by_id[other_plan_from_same_building["id"]].items()
        )

        # Other building's plans are never updated
        assert not (
            expected_georef_data_not_updated.items()
            - db_plans_by_id[other_plan_from_other_building["id"]].items()
        )


def test_set_masterplan(client, building, plan, make_plans):
    other_plan = make_plans(building)[0]
    georef_data = {
        "georef_rot_angle": 1,
        "georef_x": 2,
        "georef_y": 3,
        "georef_rot_x": 4,
        "georef_rot_y": 5,
    }
    PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=georef_data)
    response = client.put(
        get_address_for(
            blueprint=plan_app,
            use_external_address=False,
            view_function=set_as_masterplan,
            plan_id=plan["id"],
        ),
    )

    assert response.status_code == HTTPStatus.OK
    assert PlanDBHandler.get_by(id=plan["id"])["is_masterplan"]

    other_plan = PlanDBHandler.get_by(id=other_plan["id"])
    for key, value in georef_data.items():
        assert other_plan[key] == value


class TestApiCreateFloorRange:
    @staticmethod
    def test_plan_api_create_floor_range(client, plan):
        response = client.put(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=PlanFloorsView,
                plan_id=plan["id"],
            ),
            json={
                "floor_lower_range": 0,
                "floor_upper_range": 1,
            },
        )
        assert len(response.json) == 2
        assert response.status_code == HTTPStatus.CREATED
        assert {floor["floor_number"] for floor in response.json} == {0, 1}

    @staticmethod
    def test_plan_api_create_floor_range_schema(client, plan):
        response = client.put(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=PlanFloorsView,
                plan_id=plan["id"],
            ),
            json={
                "floor_lower_range": 2,
                "floor_upper_range": 1,
            },
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @staticmethod
    def test_plan_api_create_floor_range_missing_upper_range(client, plan):
        response = client.put(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=PlanFloorsView,
                plan_id=plan["id"],
            ),
            json={
                "floor_lower_range": 10,
            },
        )
        assert len(response.json) == 1
        assert response.status_code == HTTPStatus.CREATED
        assert response.json[0]["floor_number"] == 10

    @staticmethod
    def test_plan_floors_delete_existing_floors_if_not_in_range(
        client, building, plan, make_floor
    ):
        for i in (8, 9, 10):
            make_floor(building=building, plan=plan, floornumber=i)

        response = client.put(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=PlanFloorsView,
                plan_id=plan["id"],
            ),
            json={"floor_lower_range": 9, "floor_upper_range": 11},
        )

        assert response.status_code == HTTPStatus.CREATED
        assert {floor["floor_number"] for floor in response.json} == {9, 10, 11}

    @staticmethod
    def test_plan_api_create_floor_range_returns_error_if_floor_already_exists(
        client, plan, building, make_plans, make_floor
    ):
        other_plan = make_plans(building)[0]
        make_floor(building, other_plan, floornumber=3)
        response = client.put(
            get_address_for(
                blueprint=plan_app,
                use_external_address=False,
                view_function=PlanFloorsView,
                plan_id=plan["id"],
            ),
            json={
                "floor_lower_range": 2,
                "floor_upper_range": 4,
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert (
            response.json["msg"]
            == "Some of the floor numbers requested to be created {2, 3, 4} already exist for the building"
        )
