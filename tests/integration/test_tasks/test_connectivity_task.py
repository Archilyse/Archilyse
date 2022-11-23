import json
from collections import defaultdict
from typing import Callable, Tuple

import pytest
from deepdiff import DeepDiff
from shapely.geometry import MultiPolygon, Point
from shapely.ops import unary_union

from brooks.classifications import BaseClassificationScheme
from common_utils.constants import DEFAULT_GRID_RESOLUTION, TASK_TYPE
from common_utils.exceptions import ConnectivityEigenFailedConvergenceException
from dufresne.polygon.utils import as_multipolygon
from handlers import SlamSimulationHandler, UnitHandler
from handlers.db import UnitAreaDBHandler, UnitSimulationDBHandler
from simulations.connectivity import ConnectivitySimulator
from simulations.hexagonizer import HexagonizerGraph
from tasks.connectivity_tasks import connectivity_simulation_task
from tasks.simulations_tasks import register_simulation
from tasks.utils.utils import create_run_id
from tasks.workflow_tasks import WorkflowGenerator


@pytest.fixture
def expected_eigen_centrality(fixtures_path):
    with fixtures_path.joinpath(
        "connectivity/expected_eigen_centrality.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture
def expected_connectivity_simulation(fixtures_path):
    with fixtures_path.joinpath(
        "connectivity/expected_connectivity_simulation_task_regression.json"
    ).open() as f:
        return json.load(f)


@pytest.mark.skip
def test_connectivity_simulation_task_regression(
    celery_eager,
    run_ids,
    site_with_1_unit,
    expected_connectivity_simulation,
):
    WorkflowGenerator(
        site_id=site_with_1_unit["site"]["id"]
    ).get_connectivity_simulation_task_chain().delay()
    result = SlamSimulationHandler.get_simulation_results_formatted(
        unit_id=site_with_1_unit["units"][0]["id"],
        simulation_type=TASK_TYPE.CONNECTIVITY,
    )
    assert result == expected_connectivity_simulation


def test_connectivity_eigen_centrality_should_compute_for_each_unit_area(
    mocker,
    celery_eager,
    site_with_1_unit,
    expected_eigen_centrality,
    fixtures_path,
    update_fixtures=False,
):
    from tasks import connectivity_tasks as connectivity_module

    class EigenCentralitySimulator(ConnectivitySimulator):
        def all_simulations(self, layout) -> Tuple[str, Callable]:
            yield "eigen_centrality", self.eigen_centrality

    mocker.patch.object(
        connectivity_module,
        "ConnectivitySimulator",
        EigenCentralitySimulator,
    )

    site = site_with_1_unit["site"]
    units = site_with_1_unit["units"]
    plan_id = units[0]["plan_id"]

    unit_areas = UnitAreaDBHandler.find_in(unit_id=[u["id"] for u in units])
    unit_areas_indexed = defaultdict(list)
    for unit_area in unit_areas:
        unit_areas_indexed[unit_area["unit_id"]].append(unit_area["area_id"])

    # create the units for closeness/centrality analysis
    run_id = create_run_id()
    register_simulation.delay(
        site_id=site["id"], run_id=run_id, task_type=TASK_TYPE.CONNECTIVITY.name
    )
    connectivity_simulation_task.delay(site_id=site["id"], run_id=run_id)

    unit_handler = UnitHandler()

    site_simulation_results = UnitSimulationDBHandler.find(run_id=run_id)
    for simulation_results in site_simulation_results:
        unit_id = simulation_results["unit_id"]

        unit_layout = unit_handler.build_unit_from_area_ids(
            plan_id=plan_id,
            area_ids=unit_areas_indexed[unit_id],
            georeference_plan_layout=True,
        )
        layout_areas_by_area_id = {
            area.db_area_id: area.footprint for area in unit_layout.areas
        }
        full_unit_polygon = unit_layout.get_footprint_no_features()
        area_footprints = unary_union(
            [footprint for footprint in layout_areas_by_area_id.values()]
        )
        excluded_footprint: MultiPolygon = as_multipolygon(
            full_unit_polygon.difference(area_footprints)
        )

        unit_results = simulation_results["results"]
        resolution = unit_results.pop("resolution")
        assert resolution <= 1.0

        expected_eigen_centrality = {
            f"{float(k):.5f}": v for k, v in expected_eigen_centrality.items()
        }
        eigen_values_by_area = {}
        for area_id, results in unit_results.items():
            area_id = int(area_id)
            area_size = layout_areas_by_area_id[area_id].area
            assert area_id in unit_areas_indexed[unit_id]

            # all of the observation points of under the area id must be within that brooks area footprint
            assert all(
                layout_areas_by_area_id[area_id].contains(Point(x, y))
                for (y, x, _) in results["observation_points"]
            )

            # there cannot be any observation points outside of the areas
            assert all(
                not subfootprint.contains(Point(x, y))
                for subfootprint in excluded_footprint.geoms
                for (y, x, z) in results["observation_points"]
            )

            # analysis output value control
            eigen_values_by_area[f"{area_size:.5f}"] = results[
                "connectivity_eigen_centrality"
            ]

        if update_fixtures:
            with fixtures_path.joinpath(
                "connectivity/expected_eigen_centrality.json"
            ).open("wt") as f:
                json.dump(eigen_values_by_area, f)

        assert not DeepDiff(
            eigen_values_by_area, expected_eigen_centrality, significant_digits=2
        )


def test_connectivity_eigen_fails(site_with_1_unit, mocker):
    from simulations.connectivity import ConnectivitySimulator

    mocker.patch.object(ConnectivitySimulator, "EIGEN_MAX_ITER", side_effect=10)

    unit_layout = UnitHandler().get_unit_layout(
        unit_id=site_with_1_unit["units"][0]["id"],
        georeferenced=True,
        postprocessed=False,
    )
    unit_polygon = unit_layout.get_footprint_no_features()

    hex_graph = HexagonizerGraph(
        polygon=unit_polygon,
        resolution=DEFAULT_GRID_RESOLUTION,
    )

    with pytest.raises(ConnectivityEigenFailedConvergenceException):
        ConnectivitySimulator(
            graph=hex_graph.connected_graph,
            area_type_filter=BaseClassificationScheme.CONNECTIVITY_UNWANTED_AREA_TYPES,
            resolution=0.5,
        ).eigen_centrality()
