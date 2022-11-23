import json
from zipfile import ZipFile

import pytest
from deepdiff import DeepDiff
from pytest import fixture

from handlers import AutoUnitLinkingHandler
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    GroupDBHandler,
    PlanDBHandler,
    QADBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)

SITE_1440_BUILDING_ID = 2659
SITE_1440 = 1440
SITE_1440_CLIENT_ID = 6


@fixture
def site_1440(fixtures_path, qa_data):
    for handler in (
        ClientDBHandler,
        GroupDBHandler,
        SiteDBHandler,
        BuildingDBHandler,
        PlanDBHandler,
        ReactPlannerProjectsDBHandler,
        FloorDBHandler,
        AreaDBHandler,
        UnitDBHandler,
        UnitAreaDBHandler,
    ):
        with ZipFile(fixtures_path.joinpath("site_1440.zip")) as zip_file:
            with zip_file.open(f"{handler.model.__table__}.json") as json_file:
                data = json.load(json_file)

        if str(handler.model.__table__) == "plans":
            for entity in data:
                handler.add(**entity)
        elif str(handler.model.__table__) == "react_planner_projects":
            handler.bulk_insert([{k: v for k, v in a.items()} for a in data])
        elif str(handler.model.__table__) == "buildings":
            handler.bulk_insert(
                [
                    {**b, "client_building_id": f"fake-id-{i}"}
                    for i, b in enumerate(data, start=1)
                ]
            )
        else:
            handler.bulk_insert(data)

    QADBHandler.add(site_id=SITE_1440, client_id=SITE_1440_CLIENT_ID, data=qa_data)


@pytest.mark.parametrize(
    "floor_number,expected_result",
    [
        (
            0,
            [],
        ),
        (
            1,
            [
                # these are apartments
                {"unit_id": 61735, "unit_client_id": "61734"},
                {"unit_id": 61736, "unit_client_id": "61735"},
                {"unit_id": 61734, "unit_client_id": "61736"},
            ],
        ),
    ],
)
def test_unit_linking_plan_not_georeferenced(site_1440, floor_number, expected_result):
    # given
    # remove georeferencing
    floor = FloorDBHandler.get_by(
        floor_number=floor_number, building_id=SITE_1440_BUILDING_ID
    )
    PlanDBHandler.update(
        item_pks={"id": floor["plan_id"]}, new_values={"georef_x": None}
    )
    # when
    units_linked = list(
        AutoUnitLinkingHandler(building_id=SITE_1440_BUILDING_ID).unit_linking(
            floor_id=floor["id"]
        )
    )
    # then
    assert not DeepDiff(expected_result, units_linked, ignore_order=True)


def test_unit_linking_floor_by_floor(site_1440):
    # given
    expected_result_by_floor = {
        0: [],
        1: [
            {"unit_client_id": "61734", "unit_id": 61735},
            {"unit_client_id": "61735", "unit_id": 61736},
            {"unit_client_id": "61736", "unit_id": 61734},
        ],
        2: [],
        3: [],
        4: [],
        5: [],
    }
    handler = AutoUnitLinkingHandler(building_id=SITE_1440_BUILDING_ID)
    results_by_floor_number = {}
    for floor in FloorDBHandler.find():
        floor = FloorDBHandler.get_by(floor_number=floor["floor_number"])
        units_linked = handler.unit_linking(floor_id=floor["id"])
        results_by_floor_number[floor["floor_number"]] = list(units_linked)

    assert not DeepDiff(
        expected_result_by_floor, results_by_floor_number, ignore_order=True
    )
