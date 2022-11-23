from handlers import SlamSimulationHandler
from simulations.noise import NoiseSimulationHandler, NoiseWindowSimulationHandler
from simulations.noise.utils import get_noise_window_per_area
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def noise_simulation_task(self, site_id: int, run_id: str):
    site_results = NoiseSimulationHandler(
        site_id=site_id, noise_window_per_area=get_noise_window_per_area(site_id)
    ).get_noise_for_site()
    SlamSimulationHandler.store_results(run_id=run_id, results=site_results)


@celery_retry_task
def noise_windows_simulation_task(self, site_id: int, run_id: str):
    site_results = NoiseWindowSimulationHandler(site_id=site_id).get_noise_for_site()
    SlamSimulationHandler.store_results(run_id=run_id, results=site_results)
