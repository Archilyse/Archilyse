from collections import defaultdict

from celery import group

from common_utils.constants import (
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
)
from common_utils.logger import logger
from handlers.db import PotentialSimulationDBHandler
from tasks.potential_view_tasks import get_potential_quavis_simulation_chain
from tasks.surroundings_tasks import generate_surroundings_for_potential_task


def get_sims_failed():
    sims_failed = PotentialSimulationDBHandler.find(
        status=POTENTIAL_SIMULATION_STATUS.FAILURE,
        identifier=None,
        output_columns=["id", "building_footprint"],
    )
    sims_by_footprint_to_rerun = defaultdict(list)
    for sim in sims_failed:
        sims_by_footprint_to_rerun[sim["building_footprint"]].append(sim["id"])
    return sims_by_footprint_to_rerun


def get_sims_pending():
    sims_failed = PotentialSimulationDBHandler.find(
        status=POTENTIAL_SIMULATION_STATUS.PROCESSING,
        identifier=None,
        output_columns=["id", "building_footprint"],
    )
    sims_by_footprint_to_rerun = defaultdict(list)
    for sim in sims_failed:
        sims_by_footprint_to_rerun[sim["building_footprint"]].append(sim["id"])
    return sims_by_footprint_to_rerun


def main():
    sims_pending = get_sims_pending()
    sims_failed = get_sims_failed()
    counts = [
        sum([len(x) for x in sims.values()]) for sims in (sims_failed, sims_pending)
    ]
    logger.info(
        f"Simulations failed: {counts[0]}, "
        f"Simulations pending: {counts[1]}. "
        f"TOTAL: {sum(counts)} with {len(sims_failed) + len(sims_pending)} surroundings generation"
    )

    for building_footprint, sims_ids in (sims_pending | sims_failed).items():
        PotentialSimulationDBHandler.bulk_update(
            status={s: "PENDING" for s in sims_ids}
        )
        (
            generate_surroundings_for_potential_task.si(
                region=REGION.CH.name,
                source_surr=SURROUNDING_SOURCES.SWISSTOPO.value,
                simulation_version=SIMULATION_VERSION.PH_2022_H1.value,
                building_footprint_lat_lon=building_footprint,
            )
            | group(
                *[
                    get_potential_quavis_simulation_chain(simulation_id=sim_id)
                    for sim_id in sims_ids
                ]
            )
        ).delay()


if __name__ == "__main__":
    main()
