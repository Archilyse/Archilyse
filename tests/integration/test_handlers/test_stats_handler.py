from collections import defaultdict

import pytest
from deepdiff import DeepDiff

from common_utils.constants import (
    CONNECTIVITY_DIMENSIONS,
    NOISE_SURROUNDING_TYPE,
    SIMULATION_VERSION,
    TASK_TYPE,
    VIEW_DIMENSION_2,
)
from handlers import StatsHandler
from handlers.db import (
    ApartmentStatsDBHandler,
    UnitAreaStatsDBHandler,
    UnitSimulationDBHandler,
    UnitStatsDBHandler,
)


class TestStatsHandler:
    def test_get_site_id(self, pending_simulation):
        assert (
            StatsHandler(run_id=pending_simulation["run_id"], results={}).site_id
            == pending_simulation["site_id"]
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.EXPERIMENTAL], indirect=True
    )
    @pytest.mark.parametrize(
        "dimensions,run_id,task_type",
        [
            (
                {n.value for n in NOISE_SURROUNDING_TYPE},
                "my-fake-noise-id",
                TASK_TYPE.NOISE,
            ),
            (
                {dimension.value for dimension in VIEW_DIMENSION_2},
                "my-fake-view-sun-id",
                TASK_TYPE.VIEW_SUN,
            ),
        ],
    )
    def test_get_unit_stats(
        self, unit, site_with_simulation_results, dimensions, run_id, task_type
    ):
        expected_subset = {
            "count": 48.0,
            "max": 3.0,
            "mean": 2.0,
            "median": 2.0,
            "min": 1.0,
            "only_interior": False,
            "p20": 1.0,
            "p80": 3.0,
            "run_id": run_id,
            "stddev": 0.816496580927726,
            "unit_id": unit["id"],
        }

        stats = StatsHandler.get_unit_stats(
            site_id=site_with_simulation_results["id"],
            interior_only=False,
            task_type=task_type,
            desired_dimensions=dimensions,
        )
        for unit_stats in stats[unit["id"]].values():
            assert expected_subset.items() <= unit_stats.items()

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.EXPERIMENTAL], indirect=True
    )
    @pytest.mark.parametrize(
        "dimensions,run_id,task_type",
        [
            (
                {n.value for n in NOISE_SURROUNDING_TYPE},
                "my-fake-noise-id",
                TASK_TYPE.NOISE,
            ),
            (
                {dimension.value for dimension in VIEW_DIMENSION_2},
                "my-fake-view-sun-id",
                TASK_TYPE.VIEW_SUN,
            ),
            (
                CONNECTIVITY_DIMENSIONS - {"eigen_centrality"},
                "my-fake-conn-id",
                TASK_TYPE.CONNECTIVITY,
            ),
        ],
    )
    def test_get_apartment_stats(
        self, unit, site_with_simulation_results, dimensions, run_id, task_type
    ):
        expected_subset = {
            "count": 48.0,
            "max": 3.0,
            "mean": 2.0,
            "median": 2.0,
            "min": 1.0,
            "only_interior": False,
            "p20": 1.0,
            "p80": 3.0,
            "run_id": run_id,
            "stddev": 0.816496580927726,
            "client_id": unit["client_id"],
        }

        apt_stats = StatsHandler.get_apartment_stats(
            site_id=site_with_simulation_results["id"],
            interior_only=False,
            task_type=task_type,
            desired_dimensions=dimensions,
            fill_missing_dimensions=True,
        )
        for stats in apt_stats[unit["client_id"]].values():
            assert expected_subset.items() <= stats.items()

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.EXPERIMENTAL], indirect=True
    )
    def test_get_apartment_stats_fills_missing(
        self,
        unit,
        site_with_simulation_results,
    ):
        expected_subset = {
            **StatsHandler._FILLING_VALUES,
        }

        stats = StatsHandler.get_apartment_stats(
            site_id=site_with_simulation_results["id"],
            interior_only=False,
            task_type=TASK_TYPE.CONNECTIVITY,
            desired_dimensions={"eigen_centrality"},
            fill_missing_dimensions=True,
        )
        assert stats[unit["client_id"]]["eigen_centrality"] == expected_subset

    def test_compute_and_store_area_stats(self, pending_simulation, unit_areas_db):
        # given
        fake_results = defaultdict(dict)
        for unit_area in unit_areas_db:
            fake_results[unit_area["unit_id"]][unit_area["area_id"]] = {
                "some": [1, 2, 3]
            }

        UnitSimulationDBHandler.bulk_insert(
            items=[
                dict(
                    unit_id=unit_id,
                    run_id=pending_simulation["run_id"],
                    results=unit_area_results,
                )
                for unit_id, unit_area_results in fake_results.items()
            ]
        )

        # when
        StatsHandler(
            run_id=pending_simulation["run_id"], results=fake_results
        )._compute_and_store_area_stats()

        # then
        expected_result = [
            {
                "run_id": pending_simulation["run_id"],
                "unit_id": unit_area["unit_id"],
                "area_id": unit_area["area_id"],
                "dimension": "some",
                "p20": 1.4,
                "p80": 2.6,
                "median": 2.0,
                "min": 1.0,
                "max": 3.0,
                "mean": 2.0,
                "stddev": 0.816496580927726,
                "count": 3.0,
            }
            for unit_area in unit_areas_db
        ]
        assert not DeepDiff(
            expected_result,
            UnitAreaStatsDBHandler.find(run_id=pending_simulation["run_id"]),
            ignore_order=True,
        )

    @pytest.mark.parametrize("only_interior", [True, False])
    def test_compute_and_store_unit_stats(
        self, pending_simulation, unit, areas_db, only_interior
    ):
        # given
        fake_results = {
            unit["id"]: {area["id"]: {"some": [1, 2, 3]} for area in areas_db}
        }
        UnitSimulationDBHandler.add(
            run_id=pending_simulation["run_id"],
            unit_id=unit["id"],
            results=fake_results[unit["id"]],
        )
        # when
        StatsHandler(
            run_id=pending_simulation["run_id"], results=fake_results
        )._compute_and_store_unit_stats(only_interior=only_interior)
        # then
        assert UnitStatsDBHandler.find(run_id=pending_simulation["run_id"]) == [
            {
                "run_id": pending_simulation["run_id"],
                "unit_id": unit["id"],
                "dimension": "some",
                "p20": 1,
                "p80": 3,
                "median": 2.0,
                "min": 1.0,
                "max": 3.0,
                "mean": 2.0,
                "stddev": 0.816496580927726,
                "count": 6,
                "only_interior": only_interior,
            }
        ]

    @pytest.mark.parametrize("only_interior", [True, False])
    def test_compute_and_store_apartment_stats(
        self, pending_simulation, site, unit, areas_db, only_interior
    ):
        # given
        fake_results = {
            unit["id"]: {area["id"]: {"some": [1, 2, 3]} for area in areas_db}
        }
        # when
        StatsHandler(
            run_id=pending_simulation["run_id"], results=fake_results
        )._compute_and_store_apartment_stats(only_interior=only_interior)
        # then
        assert ApartmentStatsDBHandler.find(run_id=pending_simulation["run_id"]) == [
            {
                "run_id": pending_simulation["run_id"],
                "client_id": unit["client_id"],
                "dimension": "some",
                "p20": 1,
                "p80": 3,
                "median": 2.0,
                "min": 1.0,
                "max": 3.0,
                "mean": 2.0,
                "stddev": 0.816496580927726,
                "count": 6,
                "only_interior": only_interior,
            }
        ]
