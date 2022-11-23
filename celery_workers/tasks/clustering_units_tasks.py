from collections import defaultdict
from decimal import Decimal
from math import ceil

from common_utils.constants import UNIT_USAGE
from common_utils.exceptions import DependenciesUnMetSimulationException
from handlers import UnitHandler
from handlers.db import FloorDBHandler, SiteDBHandler, UnitDBHandler
from tasks.utils.utils import celery_retry_task

DEFAULT_PERCENT_REDUCTION = Decimal("0.7")
MAX_AREA_DEVIATION = 0.1


def get_number_of_clusters(site_id: int, total_number_of_units: int):
    n_clusters = SiteDBHandler.get_by(
        id=site_id, output_columns=["sub_sampling_number_of_clusters"]
    )["sub_sampling_number_of_clusters"]
    if n_clusters is None:
        return ceil(total_number_of_units * (1 - DEFAULT_PERCENT_REDUCTION))
    return n_clusters


def cluster_checks_fixer(
    clustering: dict[str, list[str]],
    unit_vectors: dict,
    units_floor_numbers: dict[str, list[int]],
) -> dict[str, list[str]]:
    new_clustering: dict[str, list[str]] = {}
    for representative_client_id, cluster_units in clustering.items():
        reference_area = unit_vectors[representative_client_id]["UnitBasics.net-area"]
        reference_num_rooms = unit_vectors[representative_client_id][
            "UnitBasics.number-of-rooms"
        ]
        reference_floor_numbers = units_floor_numbers[representative_client_id]

        unique_client_ids = set()
        for client_id in cluster_units:
            # Same room count
            if (
                unit_vectors[client_id]["UnitBasics.number-of-rooms"]
                != reference_num_rooms
            ):
                unique_client_ids.add(client_id)
            # Max 1 floor difference
            elif not any(
                abs(unit_floor - ref_floor) <= 1
                for unit_floor in units_floor_numbers[client_id]
                for ref_floor in reference_floor_numbers
            ):
                unique_client_ids.add(client_id)
            # net area_check
            elif (
                abs(unit_vectors[client_id]["UnitBasics.net-area"] - reference_area)
                > reference_area * MAX_AREA_DEVIATION
            ):
                unique_client_ids.add(client_id)

        new_clustering |= {client_id: [client_id] for client_id in unique_client_ids}
        new_clustering[representative_client_id] = list(
            set(clustering[representative_client_id]) - unique_client_ids
        )

    return new_clustering


@celery_retry_task
def clustering_units_task(self, site_id: int):
    from handlers.db.clustering_subsampling_handler import (
        ClusteringSubsamplingDBHandler,
    )
    from handlers.ph_vector import PHResultVectorHandler
    from simulations.clustering_units import cluster_units

    floor_info = {
        f["id"]: f["floor_number"]
        for f in FloorDBHandler.find_by_site_id(
            site_id=site_id, output_columns=["id", "floor_number"]
        )
    }
    # Residential only
    units_floor_numbers = defaultdict(list)
    for u in UnitDBHandler.find(
        site_id=site_id,
        unit_usage=UNIT_USAGE.RESIDENTIAL,
        output_columns=["client_id", "floor_id"],
    ):
        try:
            units_floor_numbers[u["client_id"]].append(floor_info[u["floor_id"]])
        except KeyError:
            raise DependenciesUnMetSimulationException(
                f"A unit is not linked for site: {site_id}"
            )

    vector_handler = PHResultVectorHandler(site_id=site_id)
    unit_vectors = {
        client_id: unit_vector
        for client_id, unit_vector in vector_handler.generate_apartment_vector(
            interior_only=True
        ).items()
        if client_id in units_floor_numbers.keys()
    }

    if not unit_vectors:
        return
    elif len(unit_vectors) == 1:
        units = list(unit_vectors.keys())
        clusters = iter([(units, units[0])])
    else:
        n_clusters = get_number_of_clusters(
            site_id=site_id,
            total_number_of_units=len(unit_vectors),
        )
        clusters = cluster_units(unit_vectors=unit_vectors, n_clusters=n_clusters)

    results = {
        representative_client_id: cluster
        for cluster, representative_client_id in clusters
    }
    results = cluster_checks_fixer(
        clustering=results,
        unit_vectors=unit_vectors,
        units_floor_numbers=units_floor_numbers,
    )

    ClusteringSubsamplingDBHandler.add(site_id=site_id, results=results)
    UnitHandler().update_units_representative(
        site_id=site_id, clustering_subsampling=results
    )
