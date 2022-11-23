import contextlib

from celery import group

from common_utils.constants import (
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    SIMULATION_VERSION,
)
from common_utils.exceptions import TaskAlreadyRunningException
from handlers.db import PotentialSimulationDBHandler
from tasks.utils.constants import SURROUNDINGS_LOCATIONS_PERIODIC_QA
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def run_potential_surrounding_quality(self):
    import pendulum
    from shapely.wkb import loads

    from tasks.potential_view_tasks import (
        SIMULATION_TYPES_TO_RUN,
        get_potential_quavis_simulation_chain,
    )
    from tasks.surroundings_tasks import generate_surroundings_for_potential_task

    day = pendulum.today().to_date_string()

    for place_name, (
        building_footprint_wkb,
        floors_numbers,
        region,
        source,
    ) in SURROUNDINGS_LOCATIONS_PERIODIC_QA.items():
        building_footprint = loads(building_footprint_wkb, hex=True)
        for simulation_version in (
            SIMULATION_VERSION.PH_2022_H1,
            SIMULATION_VERSION.PH_01_2021,
        ):
            sims = []
            for floor_number in floors_numbers:
                kwargs = dict(
                    building_footprint=building_footprint,
                    floor_number=floor_number,
                    identifier=f"pot_surr_qa_{source.value}_{place_name}-{floor_number}-{day}",
                    layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
                    status=POTENTIAL_SIMULATION_STATUS.PENDING,
                    simulation_version=simulation_version,
                    source_surr=source,
                    region=region.name,
                )
                sims.extend(
                    [
                        PotentialSimulationDBHandler.add(type=sim_type, **kwargs)
                        for sim_type in SIMULATION_TYPES_TO_RUN
                    ]
                )
            tasks_chain = generate_surroundings_for_potential_task.si(
                region=region.name,
                source_surr=source.name,
                simulation_version=simulation_version.name,
                building_footprint_lat_lon=building_footprint.wkt,
            ) | group(
                *[
                    get_potential_quavis_simulation_chain(simulation_id=sim["id"])
                    for sim in sims
                ]
            )
            tasks_chain.delay()


QA_SITE_IDS = (1431, 1432, 1433)


@celery_retry_task
def run_slam_quality(self):
    from tasks.workflow_tasks import run_digitize_analyze_client_tasks

    for site_id in QA_SITE_IDS:
        with contextlib.suppress(TaskAlreadyRunningException):
            run_digitize_analyze_client_tasks.delay(site_id=site_id)
