from celery import Task

from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.exceptions import BasicFeaturesException
from handlers import SlamSimulationHandler
from tasks.utils.utils import celery_retry_task, format_basic_feature_errors


class BasicFeatureTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        SlamSimulationHandler.update_state(
            run_id=kwargs["run_id"],
            state=ADMIN_SIM_STATUS.SUCCESS,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        SlamSimulationHandler.update_state(
            run_id=kwargs["run_id"],
            state=ADMIN_SIM_STATUS.FAILURE,
            errors=format_basic_feature_errors(exc=exc),
        )
        super().on_failure(exc, task_id, args, kwargs, einfo)


@celery_retry_task(base=BasicFeatureTask, throws=(BasicFeaturesException,))
def run_basic_features_task(self, run_id: str):
    from handlers import SiteHandler, SlamSimulationHandler

    simulation = SlamSimulationHandler.update_state(
        run_id=run_id, state=ADMIN_SIM_STATUS.PROCESSING
    )
    basic_features_results = SiteHandler.generate_basic_features(
        site_id=simulation["site_id"]
    )
    SlamSimulationHandler.store_results(
        run_id=run_id,
        results=dict(basic_features_results),
    )


@celery_retry_task
def run_unit_types_task(self, site_id: int):
    from handlers import BuildingHandler
    from handlers.db import BuildingDBHandler

    for building in BuildingDBHandler.find(site_id=site_id):
        BuildingHandler.create_unit_types_per_building(building_id=building["id"])
