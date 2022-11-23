import json

from handlers import PlanLayoutHandler, ReactPlannerHandler
from handlers.db import AreaDBHandler, UnitAreaDBHandler, UnitDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from handlers.unit_handler import UnitHandler


def test_build_unit(mocker, annotations_plan_5825, fixtures_path):
    raw_brooks_model = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_5825), scaled=True
    )

    unit_info = {"plan_id": 5825}
    with fixtures_path.joinpath("areas/areas_plan_5825.json").open() as f:
        areas = json.load(f)
        plan_areas_db = [{"id": i, **area} for i, area in enumerate(areas)]
    unit_areas_db = [
        {"unit_id": 34850, "area_id": db_area["id"]} for db_area in plan_areas_db
    ]
    mocker.patch.object(
        PlanLayoutHandler,
        "_get_raw_layout_from_react_data",
        return_value=raw_brooks_model,
    )
    mocker.patch.object(AreaDBHandler, "find", return_value=plan_areas_db)
    mocker.patch.object(UnitHandler, "_get_unit_info", return_value=unit_info)
    mocker.patch.object(UnitAreaDBHandler, "find", return_value=unit_areas_db)
    mocker.patch.object(
        ReactPlannerHandler,
        "project",
        return_value={"data": {"scale": annotations_plan_5825["scale"]}},
    )

    unit_layout = UnitHandler().build_unit_from_area_ids(
        plan_id=-9999,
        area_ids=[db_entry["area_id"] for db_entry in unit_areas_db],
    )
    assert len(unit_layout.areas) == len(unit_areas_db)
    assert len(unit_layout.separators) == 82
    assert len(unit_layout.openings) == 64
    assert len(unit_layout.features) == 30


class TestUnitHandlerDuplicateUnitsNewFloor:
    @staticmethod
    def test_duplicate_units_new_floor_no_existing_units(mocker):
        mocker.patch.object(UnitDBHandler, "find", return_value=[])
        mocker.patch.object(UnitDBHandler, "find_in", return_value=[])
        mocker.patch.object(UnitAreaDBHandler, "find_in", return_value=[])
        mocker.patch.object(UnitAreaDBHandler, "bulk_insert", return_value=0)
        mocked_insert = mocker.patch.object(
            UnitDBHandler, "bulk_insert", return_value=[]
        )
        new_floor_ids = [1, 2]

        UnitHandler.duplicate_apartments_new_floor(
            plan_id=1, new_floor_ids=new_floor_ids
        )
        mocked_insert.assert_called_with(items=[])

    @staticmethod
    def test_duplicate_unit_areas(mocker):
        mocker.patch.object(
            UnitDBHandler,
            "find_in",
            return_value=[{"id": 1, "apartment_no": 2}, {"id": 10, "apartment_no": 3}],
        )
        mocker_insert = mocker.patch.object(
            UnitAreaDBHandler, "bulk_insert", return_value=0
        )

        UnitHandler.duplicate_unit_areas(
            new_floor_ids=[1, 2], area_ids_by_apartment_no={2: [4, 5], 3: [6, 7]}
        )
        mocker_insert.assert_called_with(
            items=[
                {"unit_id": 1, "area_id": 4},
                {"unit_id": 1, "area_id": 5},
                {"unit_id": 10, "area_id": 6},
                {"unit_id": 10, "area_id": 7},
            ]
        )
