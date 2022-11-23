from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler
from handlers.editor_v2.migration_functions.fix_openings_parents import (
    fix_opening_parents,
)

if __name__ == "__main__":

    def migration_callable(plan_id: int):
        data = ReactPlannerProjectsDBHandler.get_by(plan_id=plan_id)
        fix_opening_parents(data=data["data"])

    all_plan_ids = PlanDBHandler.find(output_columns=["id"])
    all_plan_ids = [x["id"] for x in all_plan_ids]
    from tqdm.contrib.concurrent import process_map

    process_map(migration_callable, all_plan_ids, max_workers=12, chunksize=1)
