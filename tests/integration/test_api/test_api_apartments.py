import json
from collections import Counter, defaultdict
from http import HTTPStatus

import pytest

from brooks.models.violation import ViolationType
from brooks.types import AreaType
from db_models import AreaDBModel
from handlers import PlanLayoutHandler
from handlers.area_handler import AreaHandler
from handlers.db import (
    AreaDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
    UnitDBHandler,
)
from handlers.db.area_handler import UnitAreaDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.validators.unit_areas.unit_area_validation import UnitAccessibleValidator
from slam_api.apis.apartment import (
    ApartmentLinkingViewCollection,
    ApartmentSplitViewCollection,
    ApartmentView,
    ApartmentViewCollection,
    apartments_app,
)
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for


class TestApartmentAPIPut:
    @staticmethod
    def test_put_apartment_area_types_not_defined(
        client,
        building,
        site,
        plan,
        plan_b,
        login,
        make_floor,
        annotations_box_data,
    ):
        ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations_box_data)
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={
                "georef_scale": 10**-5,
                "georef_rot_x": 0.0,
                "georef_rot_y": 0.0,
            },
        )
        apartment_no = 0
        make_floor(building=building, plan=plan, floornumber=0)
        make_floor(building=building, plan=plan, floornumber=1)

        AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])
        db_areas = AreaDBHandler.find()

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=apartment_no,
            use_external_address=False,
        )
        area_ids = [x["id"] for x in db_areas]
        request_body = {"area_ids": area_ids}
        response = client.put(url, json=request_body)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.data
        assert len(response.json["errors"]) == 1
        assert response.json["errors"][0]["type"] == ViolationType.AREA_NOT_DEFINED.name
        assert len(UnitDBHandler.find()) == 0

    @staticmethod
    def test_put_apartment_nonexistent_plan_id(client, plan, login):
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=99999999999999,
            apartment_no=0,
            use_external_address=False,
        )
        request_body = {"area_ids": [1, 2, 3]}
        response = client.put(url, json=request_body)
        assert response.status_code == HTTPStatus.NOT_FOUND, response.data

    @staticmethod
    def test_put_apartment_missing_arguments(client, plan, login):
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=0,
            use_external_address=False,
        )
        request_body = {"missing": [1, 2, 3]}
        response = client.put(url, json=request_body)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data

    @staticmethod
    def test_put_apartment_empty_area_ids(client, plan, login):
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=0,
            use_external_address=False,
        )
        request_body = {"area_ids": []}
        response = client.put(url, json=request_body)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data

    @staticmethod
    def test_put_apartment_nonexistent_area_id(client, plan_classified_scaled):
        """Scenario possible when the user holds multiple windows open and the FE didn't refresh the area ids in
        splitting"""
        apartment_no = 0

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan_classified_scaled["id"],
            apartment_no=apartment_no,
            use_external_address=False,
        )
        response = client.put(url, json={"area_ids": [9999999]})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data

    @staticmethod
    def test_put_apartment_area_spaces_must_be_connected(
        mocker,
        client,
        plan,
        make_classified_plans,
        login,
    ):
        # we want to test only the space connectivity
        mocker.patch.object(UnitAccessibleValidator, "validate"),
        make_classified_plans(plan, annotations_plan_id=5825)
        bathroom_area = AreaDBHandler.get_by(id=472811)
        room_area = AreaDBHandler.get_by(id=472822)
        disconnected_areas = [bathroom_area["id"], room_area["id"]]
        apartment_no = 0
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=apartment_no,
            use_external_address=False,
        )
        response = client.put(url, json={"area_ids": disconnected_areas})
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert Counter([error["type"] for error in response.json["errors"]]) == {
            ViolationType.CONNECTED_SPACES_MISSING.name: 8,
            ViolationType.UNIT_SPACES_NOT_CONNECTED.name: 3,
        }, response.json["errors"]

    @staticmethod
    def test_put_apartment_area_ids_must_define_all_connected_spaces(
        mocker, client, plan, make_classified_plans
    ):
        # we want to test only the space connectivity
        mocker.patch.object(UnitAccessibleValidator, "validate"),
        plan_id = 863
        make_classified_plans(plan, annotations_plan_id=plan_id)
        all_plan_areas = AreaDBHandler.find(plan_id=plan["id"])
        one_connected_space_missing = [a["id"] for a in all_plan_areas[1:]]
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=0,
            use_external_address=False,
        )
        response = client.put(url, json={"area_ids": one_connected_space_missing})
        assert response.status_code == HTTPStatus.BAD_REQUEST

    @staticmethod
    def test_put_apartment_wrong_plan(
        client,
        fixtures_path,
        make_sites,
        make_buildings,
        make_plans,
        make_annotations,
        client_db,
        site,
        plan,
        plan_b,
    ):

        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={"georef_scale": 1.0, "georef_rot_x": 0.0, "georef_rot_y": 0.0},
        )
        PlanDBHandler.update(
            item_pks={"id": plan_b["id"]},
            new_values={"georef_scale": 1.0, "georef_rot_x": 0.0, "georef_rot_y": 0.0},
        )

        make_annotations(plan, plan_b)

        # prepare raw brooks model for both plans
        plan_model = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
            validate=False, classified=False, scaled=False
        )
        plan_b_model = PlanLayoutHandler(plan_id=plan_b["id"]).get_layout(
            validate=False, classified=False, scaled=False
        )
        AreaHandler.recover_and_upsert_areas(plan_id=plan["id"], plan_layout=plan_model)
        AreaHandler.recover_and_upsert_areas(
            plan_id=plan_b["id"], plan_layout=plan_b_model
        )

        area_ids_2 = [area["id"] for area in AreaDBHandler.find(plan_id=plan_b["id"])]

        # attempt to create units of plan 1 from area ids from plan 2
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=0,
            use_external_address=False,
        )
        response = client.put(url, json={"area_ids": area_ids_2})
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.data

    @staticmethod
    def test_put_apartment_db_area_coordinates_mismatch_against_brooks_geometries(
        mocker, client, plan, make_classified_plans
    ):
        # emulates a situation where there is a plan, whose area representative points are not within brooks spaces
        mocker.patch.object(UnitAccessibleValidator, "validate"),

        make_classified_plans(plan, annotations_plan_id=3332)
        area = AreaDBHandler.add(
            plan_id=plan["id"],
            coord_x=0.0,
            coord_y=0.0,
            area_type=AreaType.ROOM.value,
            scaled_polygon="POLYGON ((0 0 0 0))",
        )
        # add first unit
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=0,
            use_external_address=False,
        )
        response = client.put(url, json={"area_ids": [area["id"]]})
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.data

    @staticmethod
    def test_put_apartment_multiple_errors(
        client, building, plan, floor, login, annotations_plan_868
    ):
        ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations_plan_868)
        apartment_no = 0
        AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=apartment_no,
            use_external_address=False,
        )
        area_ids = [x["id"] for x in AreaDBHandler.find()]
        request_body = {"area_ids": area_ids}
        response = client.put(url, json=request_body)
        assert response.status_code == HTTPStatus.BAD_REQUEST, response.data
        assert Counter([error["type"] for error in response.json["errors"]]) == {
            ViolationType.UNIT_SPACES_NOT_CONNECTED.name: 16,
            ViolationType.AREA_NOT_DEFINED.name: 23,
            ViolationType.INSIDE_ENTRANCE_DOOR.name: 3,
        }

    @staticmethod
    def test_put_apartments_call_counts(
        mocker, client, building, plan, make_classified_split_plans, make_floor
    ):
        make_classified_split_plans(plan, building=building)
        units = UnitDBHandler.find()
        raw_layout_mock = mocker.spy(ReactPlannerToBrooksMapper, "get_layout")
        assert len(units)
        for unit in units:
            url = get_address_for(
                blueprint=apartments_app,
                view_function=ApartmentView,
                plan_id=unit["plan_id"],
                apartment_no=unit["apartment_no"],
                use_external_address=False,
            )
            area_ids = [
                x["area_id"]
                for x in UnitAreaDBHandler.find(
                    output_columns=["area_id"], unit_id=unit["id"]
                )
            ]
            request_body = {"area_ids": area_ids}
            client.put(url, json=request_body)

        assert raw_layout_mock.call_count == len(units)


class TestApartmentApiGetDelete:
    @staticmethod
    @pytest.mark.parametrize(
        "num_units,expected_status", [(0, HTTPStatus.NOT_FOUND), (2, HTTPStatus.OK)]
    )
    def test_get_all_apartments_for_plan(
        mocker,
        client,
        make_units,
        building,
        make_floor,
        plan,
        num_units,
        expected_status,
    ):
        if num_units > 0:
            floor0 = make_floor(building=building, plan=plan, floornumber=0)
            floor1 = make_floor(building=building, plan=plan, floornumber=1)
            units = make_units(*[floor0, floor1])

            db_areas_id = [
                AreaDBHandler.add(**area)["id"]
                for area in [
                    {
                        AreaDBModel.coord_x.key: 0,
                        AreaDBModel.coord_y.key: i,
                        AreaDBModel.plan_id.key: plan["id"],
                        AreaDBModel.area_type.key: AreaType.NOT_DEFINED.name,
                        AreaDBModel.scaled_polygon.key: "",
                    }
                    for i in range(0, 5)
                ]
            ]
            for unit in units:
                for area_id in db_areas_id:
                    UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area_id)

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentViewCollection,
            plan_id=plan["id"],
            use_external_address=False,
        )
        unit_find_spy = mocker.spy(UnitDBHandler, "find")
        unit_area_spy = mocker.spy(UnitAreaDBHandler, "find_in")
        response = client.get(url)
        assert response.status_code == expected_status, response.data
        unit_find_spy.assert_called_once()
        if num_units:
            unit_area_spy.assert_called_once()

        if expected_status == HTTPStatus.OK:
            assert len(response.json) == num_units
            assert {x["apartment_no"] for x in response.json} == {
                x["apartment_no"] for x in units
            }
            for unit in response.json:
                assert sorted(unit["area_ids"]) == sorted(db_areas_id)

    @staticmethod
    def test_get_all_apartments_for_plan_and_apartment_no(
        client, site, building, make_floor, plan
    ):
        apartment_no = 0
        floor0 = make_floor(building=building, plan=plan, floornumber=0)
        floor1 = make_floor(building=building, plan=plan, floornumber=1)
        units = []
        for floor in (floor0, floor1):
            units.append(
                UnitDBHandler.add(
                    plan_id=floor["plan_id"],
                    site_id=site["id"],
                    floor_id=floor["id"],
                    apartment_no=apartment_no,
                )
            )

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=plan["id"],
            apartment_no=apartment_no,
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK, response.data
        assert len(response.json) == 2
        assert [x["apartment_no"] for x in response.json] == [
            x["apartment_no"] for x in units
        ]

    @staticmethod
    def test_delete_apartments(client, site, plan, building, make_floor, login):
        floors = [
            make_floor(building=building, plan=plan, floornumber=0),
            make_floor(building=building, plan=plan, floornumber=1),
        ]
        for floor in floors:
            for apartment_no in range(3):
                UnitDBHandler.add(
                    plan_id=floor["plan_id"],
                    site_id=site["id"],
                    floor_id=floor["id"],
                    apartment_no=apartment_no,
                )

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentView,
            plan_id=floors[0]["plan_id"],
            apartment_no=0,
            use_external_address=False,
        )
        assert len(UnitDBHandler.find()) == 6
        response = client.delete(url)
        assert response.status_code == HTTPStatus.ACCEPTED
        assert len(UnitDBHandler.find()) == 4


class TestApartmentAPIAutoSplit:
    @staticmethod
    def test_get_apartments_autosplit(
        client,
        login,
        make_classified_plans,
        building,
        plan,
        make_floor,
    ):
        # first we populate the annotation & areas
        make_classified_plans(plan, annotations_plan_id=5825, db_fixture_ids=False)
        expected_apartments_5825 = {
            (1, 4, 6, 12, 13, 19, 21, 22, 26, 27, 29, 35),
            (2, 9, 10, 16, 20, 24, 28, 30, 31, 33),
            (3, 5, 7, 8, 11, 15, 23, 25, 36),
        }
        floor1 = make_floor(building=building, plan=plan, floornumber=1)

        # run autosplit and make sure we get the expected apartments
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentSplitViewCollection,
            plan_id=plan["id"],
            use_external_address=False,
        )
        apartments = client.get(url).json
        assert {
            tuple(sorted(apartment["area_ids"])) for apartment in apartments
        } == expected_apartments_5825
        assert {apartment["apartment_no"] for apartment in apartments} == {1, 2, 3}

        # add two more floors and make sure we get the expected units per floor
        floor2 = make_floor(building=building, plan=plan, floornumber=2)
        floor3 = make_floor(building=building, plan=plan, floornumber=3)

        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentSplitViewCollection,
            plan_id=plan["id"],
            use_external_address=False,
        )
        apartments = client.get(url).json
        for floor in [floor1, floor2, floor3]:
            floor_apartments = {
                tuple(sorted(apartment["area_ids"]))
                for apartment in apartments
                if apartment["floor_id"] == floor["id"]
            }
            assert floor_apartments == expected_apartments_5825
        assert {apartment["apartment_no"] for apartment in apartments} == {1, 2, 3}

    @staticmethod
    @pytest.mark.parametrize(
        "initial_units, expected_unit_areas",
        [
            [[], None],
            [
                [
                    [
                        472793,
                        472794,
                        472801,
                        472803,
                        472813,
                        472814,
                        472815,
                        472818,
                        472820,
                        472822,
                    ]
                ],
                None,
            ],  # 1 entire unit already exists
            [
                [
                    [
                        472793,
                        472794,
                        472801,
                        472803,
                        472813,
                        472814,
                        472815,
                    ]
                ],
                None,
            ],  # partial unit 1
            [
                [
                    [472793],
                    [472796],
                    [472823],
                ],
                None,
            ],  # only one area per unit
        ],
    )
    def test_get_apartments_autosplit_existing_units(
        client,
        login,
        make_classified_plans,
        fixtures_path,
        building,
        plan,
        make_floor,
        initial_units,
        expected_unit_areas,
    ):
        from connectors.db_connector import get_db_session_scope
        from handlers import UnitHandler

        # first we populate the annotation & areas
        make_classified_plans(plan, annotations_plan_id=5825)
        make_floor(building=building, plan=plan, floornumber=1)
        if not expected_unit_areas:
            with fixtures_path.joinpath(
                "units_areas/unit_areas_plan_5825.json"
            ).open() as f:
                unit_areas = json.load(f)
                expected_unit_areas = defaultdict(list)
                for unit_area in unit_areas:
                    expected_unit_areas[unit_area["unit_id"]].append(
                        unit_area["area_id"]
                    )
                expected_unit_areas = {
                    tuple(value) for value in expected_unit_areas.values()
                }

        with get_db_session_scope():
            apartment_no = 1
            unit_handler = UnitHandler()
            for area_ids in initial_units:
                unit_handler.bulk_upsert_units(
                    plan_id=plan["id"], apartment_no=apartment_no
                )
                AreaHandler.update_relationship_with_units(
                    plan_id=plan["id"],
                    apartment_no=apartment_no,
                    area_ids=area_ids,
                )
                apartment_no += 1

        initial_db_units = UnitDBHandler.find(plan_id=plan["id"])
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentSplitViewCollection,
            plan_id=plan["id"],
            use_external_address=False,
        )
        apartments = client.get(url).json

        assert {
            tuple(sorted(apartment["area_ids"])) for apartment in apartments
        } == expected_unit_areas
        assert {apartment["apartment_no"] for apartment in apartments} == {1, 2, 3}

        # make sure that existing units are "recovered" and not replaced by a new unit
        assert {unit["id"] for unit in apartments if "id" in unit} == {
            unit["id"] for unit in initial_db_units
        }

    @staticmethod
    @login_as(
        [
            "ARCHILYSE_ONE_ADMIN",
        ]
    )
    def test_get_apartments_autosplit_only_admins(client, login):
        url = get_address_for(
            blueprint=apartments_app,
            view_function=ApartmentSplitViewCollection,
            plan_id=1,
            use_external_address=False,
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.mark.parametrize(
    "already_linked_units,expected_result",
    [
        (
            [],
            [
                {"unit_client_id": "Apartment.01.03.0002", "unit_id": 17280},
                {"unit_client_id": "Apartment.01.01.0003", "unit_id": 17282},
                {"unit_client_id": "Apartment.01.01.0001", "unit_id": 17284},
                {"unit_client_id": "Apartment.01.01.0002", "unit_id": 17286},
                {"unit_client_id": "Apartment.01.03.0001", "unit_id": 17288},
            ],
        ),
        (
            [
                {"unit_client_id": "Apartment.01.01.0002", "unit_id": 17286},
                {"unit_client_id": "Apartment.01.01.0003", "unit_id": 17282},
            ],
            [
                {"unit_client_id": "Apartment.01.03.0002", "unit_id": 17280},
                {"unit_client_id": "Apartment.01.01.0001", "unit_id": 17284},
                {"unit_client_id": "Apartment.01.03.0001", "unit_id": 17288},
            ],
        ),
    ],
)
def test_auto_linking_apartments(
    client,
    login,
    fixtures_path,
    site_834,
    floor,
    already_linked_units,
    expected_result,
):
    for linked_unit in already_linked_units:
        UnitDBHandler.update(
            item_pks={"id": linked_unit["unit_id"]},
            new_values={"client_id": linked_unit["unit_client_id"]},
        )

    url = get_address_for(
        blueprint=apartments_app,
        view_function=ApartmentLinkingViewCollection,
        floor_id=floor["id"],
        use_external_address=False,
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert sorted(response.json, key=lambda x: x["unit_id"]) == expected_result
