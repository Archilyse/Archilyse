from math import sqrt

from brooks.classifications import CLASSIFICATIONS
from brooks.models import SimLayout
from brooks.types import AreaType
from common_utils.constants import DEFAULT_GRID_RESOLUTION
from common_utils.exceptions import ConnectivityEigenFailedConvergenceException
from common_utils.logger import logger
from handlers import SiteHandler, SlamSimulationHandler
from simulations.connectivity import ConnectivitySimulator
from simulations.hexagonizer import HexagonizerGraph
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def connectivity_simulation_task(self, site_id: int, run_id: str):
    from handlers.db import SiteDBHandler

    classification_scheme = CLASSIFICATIONS[
        SiteDBHandler.get_by(id=site_id)["classification_scheme"]
    ].value()

    site_results = {}

    for unit_info, unit_layout in SiteHandler.get_unit_layouts(
        site_id=site_id, scaled=True, georeferenced=True
    ):
        obs_points, unit_results, resolution = generate_unit_simulations_results(
            area_types_filter=classification_scheme.CONNECTIVITY_UNWANTED_AREA_TYPES,
            unit_id=unit_info["id"],
            unit_layout=unit_layout,
        )

        site_results[unit_info["id"]] = SlamSimulationHandler.format_results_by_area(  # type: ignore
            obs_points=obs_points,
            simulation_results=unit_results,
            unit_layout=unit_layout,
        )
        site_results[unit_info["id"]]["resolution"] = resolution

    SlamSimulationHandler.store_results(run_id=run_id, results=site_results)


def generate_unit_simulations_results(
    area_types_filter: set[AreaType],
    unit_id: int,
    unit_layout: SimLayout,
) -> tuple[list, dict, float]:
    hex_graph, resolution = get_hex_graph_and_resolution(unit_layout=unit_layout)

    logger.info(
        f"unit {unit_id}| num_obs_points= {len(hex_graph.obs_points)} | resolution {resolution}"
    )

    connectivity_simulator = ConnectivitySimulator(
        graph=hex_graph.connected_graph,
        area_type_filter=area_types_filter,
        resolution=DEFAULT_GRID_RESOLUTION,
    )

    simulation_results = {}
    for sim_name, sim in connectivity_simulator.all_simulations(layout=unit_layout):
        try:
            simulation_results[f"connectivity_{sim_name}"] = sim()
        except ConnectivityEigenFailedConvergenceException:
            logger.error(
                f"connectivity_{sim_name} failed to converge for unit id {unit_id}"
            )
    return hex_graph.obs_points, simulation_results, resolution


def get_hex_graph_and_resolution(
    unit_layout: SimLayout,
) -> tuple[HexagonizerGraph, float]:
    unit_polygon = unit_layout.get_footprint_no_features()

    if unit_polygon.area < 450:
        resolution = 0.25
    else:
        resolution = round(sqrt(unit_polygon.area / 15000 * sqrt(3)), 2)

    hex_graph = HexagonizerGraph(
        polygon=unit_polygon,
        resolution=resolution,
    )

    return hex_graph, resolution
