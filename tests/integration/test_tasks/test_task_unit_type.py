from handlers import SlamSimulationHandler
from handlers.db import UnitDBHandler
from tasks.basic_features import run_unit_types_task


def test_run_unit_types_task(
    celery_eager, site, building, plan, unit, basic_features_finished
):
    SlamSimulationHandler.store_results(
        run_id=basic_features_finished["run_id"],
        results={unit["id"]: [{"UnitBasics.number-of-rooms": 3}]},
    )
    run_unit_types_task(site_id=site["id"])
    assert UnitDBHandler.get_by(id=unit["id"])["unit_type"] == "3"
