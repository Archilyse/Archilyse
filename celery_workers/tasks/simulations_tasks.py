from common_utils.constants import (
    ADMIN_SIM_STATUS,
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION,
    DEFAULT_OBSERVATION_HEIGHT,
    DEFAULT_SUN_TIMES,
    DEFAULT_SUN_V2_OBSERVATION_HEIGHT,
    SIMULATION_VERSION,
    TASK_TYPE,
)
from handlers import SlamSimulationHandler
from handlers.db import SlamSimulationDBHandler
from simulations.suntimes.suntimes_handler import SuntimesHandler
from tasks.utils.utils import celery_retry_task
from workers_config.celery_app import celery_app


@celery_retry_task
def register_simulation(self, site_id: int, run_id: str, task_type: str):
    SlamSimulationHandler.register_simulation(
        site_id=site_id,
        run_id=run_id,
        task_type=TASK_TYPE[task_type],
        state=ADMIN_SIM_STATUS.PROCESSING,
    )


@celery_retry_task
def simulation_success(self, run_id: str):
    SlamSimulationHandler.update_state(run_id=run_id, state=ADMIN_SIM_STATUS.SUCCESS)


@celery_app.task
def simulation_error(request, exc, traceback, run_id: str):

    SlamSimulationHandler.update_state(
        run_id=run_id,
        state=ADMIN_SIM_STATUS.FAILURE,
        errors={"msg": str(exc), "code": type(exc).__name__},
    )


@celery_retry_task
def run_buildings_elevation_task(self, site_id: int):
    from common_utils.constants import REGION
    from handlers import BuildingHandler
    from handlers.db import BuildingDBHandler, SiteDBHandler

    site = SiteDBHandler.get_by(id=site_id)
    simulation_version = SIMULATION_VERSION(site["simulation_version"])
    for building_info in BuildingDBHandler.find(site_id=site_id):
        BuildingHandler.calculate_elevation(
            region=REGION[site["georef_region"]],
            building_id=building_info["id"],
            simulation_version=simulation_version,
        )


@celery_retry_task
def update_site_location_task(self, site_id: int):
    from handlers import SiteHandler
    from handlers.db import SiteDBHandler

    SiteHandler.update_location_based_on_geoereferenced_layouts(
        site_info=SiteDBHandler.get_by(id=site_id)
    )


@celery_retry_task
def configure_sun_v2_quavis_task(self, run_id: str):
    from handlers.quavis import QuavisGCPHandler, SLAMSunV2QuavisHandler

    site = get_site_from_run_id(run_id=run_id)
    quavis_input = SLAMSunV2QuavisHandler.get_quavis_input(
        entity_info=site,
        grid_resolution=DEFAULT_GRID_RESOLUTION,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=DEFAULT_SUN_V2_OBSERVATION_HEIGHT,
        datetimes=SuntimesHandler.get_sun_times_v2(site_id=site["id"]),
        simulation_version=SIMULATION_VERSION(site["simulation_version"]),
    )
    QuavisGCPHandler.upload_quavis_input(run_id=run_id, quavis_input=quavis_input)

    return run_id


@celery_retry_task
def configure_quavis_task(self, run_id: str):
    from handlers.quavis import QuavisGCPHandler, SLAMQuavisHandler

    site = get_site_from_run_id(run_id=run_id)
    quavis_input = SLAMQuavisHandler.get_quavis_input(
        entity_info=site,
        grid_resolution=DEFAULT_GRID_RESOLUTION,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=DEFAULT_OBSERVATION_HEIGHT,
        datetimes=DEFAULT_SUN_TIMES,
        simulation_version=SIMULATION_VERSION(site["simulation_version"]),
    )
    QuavisGCPHandler.upload_quavis_input(run_id=run_id, quavis_input=quavis_input)

    return run_id


def get_site_from_run_id(run_id: str) -> dict:
    from handlers.db import SiteDBHandler

    simulation = SlamSimulationDBHandler.get_by(run_id=run_id)
    return SiteDBHandler.get_by(id=simulation["site_id"])


@celery_retry_task
def store_quavis_results_task(self, run_id: str):
    from handlers.quavis import QuavisGCPHandler, SLAMQuavisHandler

    site = get_site_from_run_id(run_id=run_id)
    site_results = SLAMQuavisHandler.get_quavis_results(
        entity_info=site,
        quavis_input=QuavisGCPHandler.get_quavis_input(run_id=run_id),
        quavis_output=QuavisGCPHandler.get_quavis_output(run_id=run_id),
        grid_resolution=DEFAULT_GRID_RESOLUTION,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=DEFAULT_OBSERVATION_HEIGHT,
        datetimes=DEFAULT_SUN_TIMES,
        simulation_version=SIMULATION_VERSION(site["simulation_version"]),
    )

    SlamSimulationHandler.store_results(run_id=run_id, results=site_results)


@celery_retry_task
def delete_simulation_artifacts(self, run_id: str):
    from handlers.quavis import QuavisGCPHandler

    QuavisGCPHandler.delete_simulation_artifacts(run_id=run_id)


@celery_retry_task
def store_sun_v2_quavis_results_task(self, run_id: str):
    from handlers.quavis import QuavisGCPHandler, SLAMSunV2QuavisHandler

    site = get_site_from_run_id(run_id=run_id)
    suntimes = SuntimesHandler.get_sun_times_v2(site_id=site["id"])
    site_results = SLAMSunV2QuavisHandler.get_quavis_results(
        entity_info=site,
        quavis_input=QuavisGCPHandler.get_quavis_input(run_id=run_id),
        quavis_output=QuavisGCPHandler.get_quavis_output(run_id=run_id),
        grid_resolution=DEFAULT_GRID_RESOLUTION,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=DEFAULT_SUN_V2_OBSERVATION_HEIGHT,
        datetimes=suntimes,
        simulation_version=SIMULATION_VERSION(site["simulation_version"]),
    )

    SlamSimulationHandler.store_results(run_id=run_id, results=site_results)
