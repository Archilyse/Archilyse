import pytest


@pytest.mark.parametrize(
    "initial_units, expected_units",
    [
        [[], None],
        [
            [
                (
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
                )
            ],
            None,
        ],  # original unit 1
        [
            [
                (
                    472793,
                    472794,
                    472801,
                    472803,
                    472813,
                    472814,
                    472815,
                )
            ],
            None,
        ],  # partial unit 1
        [[[472793], [472792], [472786]], None],  # only one area per unit
    ],
)
def test_autosplitting_task_existing_areas(
    client,
    login,
    celery_eager,
    make_classified_plans,
    building,
    plan,
    make_floor,
    initial_units,
    expected_units,
):
    """Tests the auto-splitting task when there is already a partial
    splitting."""
    from handlers import AreaHandler, UnitHandler
    from handlers.db import UnitAreaDBHandler, UnitDBHandler
    from tasks.pipeline_tasks import split_plan_task

    # first we populate the annotation & areas
    make_classified_plans(plan, annotations_plan_id=5825)
    make_floor(building=building, plan=plan, floornumber=1)
    if not expected_units:
        expected_units = {
            (
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
            ),
            (472792, 472796, 472797, 472798, 472804, 472807, 472810, 472811, 472816),
            (
                472786,
                472788,
                472791,
                472799,
                472800,
                472802,
                472805,
                472809,
                472817,
                472819,
                472821,
                472823,
            ),
        }

    apartment_no = 1
    unit_handler = UnitHandler()
    for area_ids in initial_units:
        unit_handler.bulk_upsert_units(plan_id=plan["id"], apartment_no=apartment_no)
        AreaHandler.update_relationship_with_units(
            plan_id=plan["id"],
            apartment_no=apartment_no,
            area_ids=area_ids,
        )
        apartment_no += 1

    split_plan_task.delay(plan_id=plan["id"])
    units = UnitDBHandler.find(plan_id=plan["id"], output_columns=["id"])
    areas_per_unit = {
        tuple(
            sorted(
                [area["area_id"] for area in UnitAreaDBHandler.find(unit_id=unit["id"])]
            )
        )
        for unit in units
    }
    assert areas_per_unit == expected_units
