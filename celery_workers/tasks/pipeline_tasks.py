from tasks.utils.utils import celery_retry_task


@celery_retry_task
def split_plan_task(self, plan_id: int):
    from handlers import PlanHandler, UnitHandler

    apartment_area_ids = PlanHandler(plan_id=plan_id).autosplit()
    UnitHandler().create_or_extend_units_from_areas(
        plan_id=plan_id, apartment_area_ids=apartment_area_ids
    )


@celery_retry_task
def auto_classify_areas_for_plan(self, plan_id: int):
    from handlers.area_handler import AreaHandler
    from handlers.db import AreaDBHandler

    db_areas_classified = AreaHandler.get_auto_classified_plan_areas_where_not_defined(
        plan_id=plan_id
    )
    areas_classified_to_update = {
        area["id"]: area["area_type"] for area in db_areas_classified
    }
    AreaDBHandler.bulk_update(area_type=areas_classified_to_update)
