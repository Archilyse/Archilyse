from collections import Counter

from shapely import wkt

from handlers.db import AreaDBHandler
from handlers.plan_utils import create_areas_for_plan
from tasks.pipeline_tasks import auto_classify_areas_for_plan


def test_auto_classify_areas_for_plan_with_no_previous_classification(plan_annotated):
    create_areas_for_plan(plan_id=plan_annotated["id"])
    auto_classify_areas_for_plan(plan_id=plan_annotated["id"])
    areas = AreaDBHandler.find()
    assert Counter([a["area_type"] for a in areas]) == {
        "ROOM": 2,
        "CORRIDOR": 1,
        "BALCONY": 2,
        "BATHROOM": 1,
        "KITCHEN": 1,
    }


def test_auto_classify_areas_for_plan_respects_manually_classified_areas(
    plan_annotated,
):
    create_areas_for_plan(plan_id=plan_annotated["id"])

    areas_sorted = sorted(
        AreaDBHandler.find(),
        key=lambda x: wkt.loads(x["scaled_polygon"]).area,
        reverse=True,
    )
    # we manually classify the bigger areas as room
    for area in areas_sorted[:-1]:
        AreaDBHandler.update(
            item_pks={"id": area["id"]}, new_values={"area_type": "ROOM"}
        )
    auto_classify_areas_for_plan(plan_id=plan_annotated["id"])
    updated_areas = AreaDBHandler.find()
    assert Counter([a["area_type"] for a in updated_areas]) == {
        "ROOM": 6,
        "BALCONY": 1,
    }
