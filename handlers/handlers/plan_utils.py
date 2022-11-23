def create_areas_for_plan(plan_id: int, preclassify: bool = False):
    from handlers.area_handler import AreaHandler
    from handlers.db import ReactPlannerProjectsDBHandler

    if not ReactPlannerProjectsDBHandler.exists(plan_id=plan_id):
        return None

    AreaHandler.recover_and_upsert_areas(
        plan_id=plan_id,
        set_area_types_from_react_areas=preclassify,
    )
