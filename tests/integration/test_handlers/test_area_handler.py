from collections import Counter

import pytest

from brooks.types import AreaType
from handlers import PlanLayoutHandler
from handlers.area_handler import AreaHandler
from handlers.db import AreaDBHandler, ReactPlannerProjectsDBHandler


def test_recover_and_upsert_areas_empty_db(
    plan, populate_plan_areas_db, populate_plan_annotations
):
    """Test is checking the default area classification based on the features, because the areas of 3354 are empty"""
    populate_plan_annotations(fixture_plan_id=3354, db_plan_id=plan["id"])
    expected_areas = populate_plan_areas_db(
        fixture_plan_id=3354, populate=False, db_plan_id=plan["id"]
    )
    AreaHandler.recover_and_upsert_areas(
        plan_id=plan["id"],
        plan_layout=PlanLayoutHandler(plan_id=plan["id"]).get_layout(
            validate=False,
            classified=False,
            scaled=False,
            set_area_types_by_features=True,
        ),
    )
    areas = AreaDBHandler.find(plan_id=plan["id"])

    assert Counter([x["area_type"] for x in areas]) == {
        AreaType.NOT_DEFINED.name: 20,
        AreaType.SHAFT.name: 8,
        AreaType.BATHROOM.name: 5,
        AreaType.STAIRCASE.name: 1,
        AreaType.ELEVATOR.name: 1,
    }
    compare_coords(db_areas=areas, expected=expected_areas)

    # coordinates don't need to be consistent but shapely is apparently doing it consistently,
    # at least when the centroid is inside of the polygon like in this case, in any case we don't rely on this.


def compare_coords(db_areas, expected):
    db_areas = sorted(
        [
            {k: float(v) for k, v in x.items() if k in {"coord_x", "coord_y"}}
            for x in db_areas
        ],
        key=lambda x: (x["coord_x"], x["coord_y"]),
    )
    expected = sorted(
        [{k: v for k, v in x.items() if k in {"coord_x", "coord_y"}} for x in expected],
        key=lambda x: (x["coord_x"], x["coord_y"]),
    )

    for db_area, expected_area in zip(db_areas, expected):
        for coord in {"coord_x", "coord_y"}:
            assert db_area[coord] == pytest.approx(expected_area[coord], abs=2.0)


def test_recover_and_upsert_areas_with_pre_existing_areas(
    plan, populate_plan_areas_db, populate_plan_annotations, area_polygon_wkt
):
    populate_plan_annotations(fixture_plan_id=3354, db_plan_id=plan["id"])
    expected_plan_areas = populate_plan_areas_db(
        fixture_plan_id=3354, populate=False, db_plan_id=plan["id"]
    )
    coords_1 = {"coord_x": 1997.95, "coord_y": 1483.07}
    coords_2 = {"coord_x": 1184.90, "coord_y": 1857.29}
    modifier = 2
    expected_new_area_type_1 = AreaType.ROOM.name
    expected_new_area_type_2 = AreaType.KITCHEN_DINING.name
    AreaDBHandler.add(
        **{
            "plan_id": plan["id"],
            **coords_1,
            "area_type": expected_new_area_type_1,
            "scaled_polygon": area_polygon_wkt,
        }  # Replaces what otherwise will be a NOT DEFINED area
    )
    AreaDBHandler.add(
        **{
            "plan_id": plan["id"],
            **{
                k: v + modifier for k, v in coords_2.items()
            },  # the position is shifted to proof the recovered classified areas are working as long as they
            # are within the polygon
            "area_type": expected_new_area_type_2,
            "scaled_polygon": area_polygon_wkt,
        }  # Replaces what otherwise will be a NOT DEFINED area
    )

    # When the areas are recovered after reprocessing the brooks model
    AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])

    # Then the DB shows the preexisting db entries correctly classified plus the new ones found
    areas = AreaDBHandler.find(plan_id=plan["id"])

    assert Counter([x["area_type"] for x in areas]) == {
        AreaType.NOT_DEFINED.name: 33,
        AreaType.ROOM.name: 1,
        AreaType.KITCHEN_DINING.name: 1,
    }
    compare_coords(db_areas=areas, expected=expected_plan_areas)


def test_recover_and_upsert_areas_with_pre_existing_areas_conflict(
    plan, annotations_path, login, area_polygon_wkt, annotations_box_data
):
    coords_1 = {"coord_y": 544.38, "coord_x": 598.35}
    expected_new_area_type_1 = AreaType.ROOM.name
    AreaDBHandler.add(
        **{
            "plan_id": plan["id"],
            **coords_1,
            "area_type": expected_new_area_type_1,
            "scaled_polygon": area_polygon_wkt,
        }  # Replaces what otherwise will be a NOT DEFINED area
    )
    AreaDBHandler.add(
        **{
            "plan_id": plan["id"],
            **coords_1,
            "area_type": expected_new_area_type_1,
            "scaled_polygon": area_polygon_wkt,
        }  # Replaces what otherwise will be a NOT DEFINED area
    )

    # When the areas are recovered after reprocessing the brooks model
    ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations_box_data)
    AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])

    # Then the DB shows the preexisting db entries correctly classified plus the new ones found
    areas = AreaDBHandler.find(plan_id=plan["id"])

    assert Counter([x["area_type"] for x in areas]) == {AreaType.NOT_DEFINED.name: 1}
    compare_coords(db_areas=areas, expected=[coords_1])
