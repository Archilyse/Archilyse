import mimetypes

import pytest
from werkzeug.datastructures import FileStorage

from brooks.types import AreaType
from common_utils.exceptions import DBValidationException, ValidationException
from handlers import FloorHandler
from handlers.db import AreaDBHandler, FloorDBHandler, UnitAreaDBHandler, UnitDBHandler


@pytest.mark.parametrize("floors_to_create", [{0, 1, 2}, {0}])
def test_floor_handler_add(
    mocked_plan_image_upload_to_gc,
    floors_to_create,
    building,
    fixtures_path,
):
    pdf_path = fixtures_path.joinpath("images/pdf_sample.pdf")
    with pdf_path.open("rb") as fp:
        file = FileStorage(fp, content_type=mimetypes.types_map[".pdf"])
        new_floors = FloorHandler.create_floors_from_plan_file(
            floorplan=file,
            building_id=building["id"],
            new_floor_numbers=floors_to_create,
        )
        assert len(new_floors) == len(floors_to_create)
        assert {floor["floor_number"] for floor in new_floors} == floors_to_create


class TestFloorHandlerUpsertFloorRange:
    @staticmethod
    def test_upsert_floor_numbers_creates(building, plan):
        floor_numbers = {0, 1, 2}
        FloorHandler.upsert_floor_numbers(
            building_id=building["id"], plan_id=plan["id"], floor_numbers=floor_numbers
        )
        assert {
            floor["floor_number"]
            for floor in FloorDBHandler.find(
                plan_id=plan["id"], output_columns=["floor_number"]
            )
        } == floor_numbers

    @staticmethod
    @pytest.mark.parametrize(
        "expected_floor_numbers",
        [{0, 1}, {-1, 0, 1}, {-3, -2, -1}, {2}],
    )
    def test_upsert_floor_numbers_deletes_correctly(
        building, plan, make_floor, expected_floor_numbers
    ):
        make_floor(building=building, plan=plan, floornumber=-1)
        make_floor(building=building, plan=plan, floornumber=0)
        make_floor(building=building, plan=plan, floornumber=1)
        final_floors = FloorHandler.upsert_floor_numbers(
            building_id=building["id"],
            plan_id=plan["id"],
            floor_numbers=expected_floor_numbers,
        )
        assert {
            floor["floor_number"] for floor in final_floors
        } == expected_floor_numbers

    @staticmethod
    @pytest.mark.parametrize(
        "floors_to_create",
        [{0, 1}, {0}, {-2, -1, 0}, {2, 3}],
    )
    def test_upsert_floor_numbers_creates_copies_units(
        building, plan, floors_to_create
    ):
        floor_zero = FloorDBHandler.add(
            plan_id=plan["id"], building_id=building["id"], floor_number=0
        )
        unit_a = UnitDBHandler.add(
            site_id=building["site_id"],
            plan_id=plan["id"],
            floor_id=floor_zero["id"],
            apartment_no=99,
        )
        unit_b = UnitDBHandler.add(
            site_id=building["site_id"],
            plan_id=plan["id"],
            floor_id=floor_zero["id"],
            apartment_no=101,
        )
        area_a = AreaDBHandler.add(
            plan_id=plan["id"],
            coord_x=1,
            coord_y=1,
            area_type=AreaType.ROOM.value,
            scaled_polygon="area_a",
        )
        area_b = AreaDBHandler.add(
            plan_id=plan["id"],
            coord_x=10,
            coord_y=10,
            area_type=AreaType.BATHROOM.value,
            scaled_polygon="area_b",
        )
        UnitAreaDBHandler.add(unit_id=unit_a["id"], area_id=area_a["id"])
        UnitAreaDBHandler.add(unit_id=unit_b["id"], area_id=area_b["id"])
        final_floors = FloorHandler.upsert_floor_numbers(
            building_id=building["id"],
            plan_id=plan["id"],
            floor_numbers=floors_to_create,
        )
        assert {floor["floor_number"] for floor in final_floors} == floors_to_create

        final_units = UnitDBHandler.find()
        assert len(final_units) == len(floors_to_create) * 2
        assert len({unit["apartment_no"] for unit in final_units}) == 2
        assert len(
            {unit_area["unit_id"] for unit_area in UnitAreaDBHandler.find()}
        ) == len(final_units)
        assert (
            len({unit_area["area_id"] for unit_area in UnitAreaDBHandler.find()}) == 2
        )

    @staticmethod
    def test_upsert_floor_numbers_raises_exception_floor_number_exists_in_building(
        building, make_plans
    ):
        plan_a, plan_b = make_plans(building, building)
        FloorDBHandler.add(
            plan_id=plan_a["id"], building_id=building["id"], floor_number=0
        )
        FloorDBHandler.add(
            plan_id=plan_b["id"], building_id=building["id"], floor_number=1
        )
        with pytest.raises(DBValidationException):
            FloorHandler.upsert_floor_numbers(
                building_id=building["id"], plan_id=plan_a["id"], floor_numbers={0, 1}
            )

    @staticmethod
    @pytest.mark.parametrize(
        "lower_range, upper_range, expected_floor_numbers",
        [(0, 1, {0, 1}), (0, None, {0}), (-2, 0, {-2, -1, 0}), (2, 3, {2, 3})],
    )
    def test_get_floor_numbers_from_floor_ranges(
        lower_range, upper_range, expected_floor_numbers
    ):
        assert (
            FloorHandler.get_floor_numbers_from_floor_range(
                floor_lower_range=lower_range,
                floor_upper_range=upper_range,
            )
            == expected_floor_numbers
        )

    @staticmethod
    def test_exception_wrong_range(building, plan):
        with pytest.raises(ValidationException):
            FloorHandler.get_floor_numbers_from_floor_range(
                floor_lower_range=0,
                floor_upper_range=-2,
            )
