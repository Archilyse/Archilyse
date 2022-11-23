import numpy as np
import pytest
from deepdiff import DeepDiff

from common_utils.constants import TASK_TYPE, VIEW_DIMENSION
from handlers import StatsHandler
from handlers.db import (
    SlamSimulationDBHandler,
    UnitAreaStatsDBHandler,
    UnitSimulationDBHandler,
)


class TestStatsHandler:
    @pytest.mark.parametrize(
        "exclude_area_ids, expected_results",
        [(None, [(1, "some_dimension", [1, 2, 3])]), ({1}, [])],
    )
    def test_get_area_dimension_values(self, exclude_area_ids, expected_results):
        unit_area_results = {
            1: {
                "some_dimension": [1, 2, 3],
                "observation_points": "will be ignored",
            },
            "resolution": "will be ignored",
        }
        assert (
            list(
                StatsHandler._get_area_dimension_values(
                    unit_area_results=unit_area_results,
                    area_ids_to_exclude=exclude_area_ids,
                )
            )
            == expected_results
        )

    @pytest.mark.parametrize(
        "stats,dimensions,existing_dims,optional_filled_dims",
        [
            (
                [
                    {
                        "unit_id": 1,
                        "area_id": 1,
                        "dimension": "closeness_centrality",
                        "mean": 10,
                    }
                ],
                {"closeness_centrality", "eigen_centrality"},
                {"closeness_centrality"},
                {"eigen_centrality"},
            ),
            (
                [
                    {
                        "unit_id": 1,
                        "area_id": 1,
                        "dimension": "not_included_dimnesion",
                        "mean": 10,
                    }
                ],
                {"eigen_centrality"},
                {},
                {"eigen_centrality"},
            ),
        ],
    )
    def test_get_area_stats_fills_missing(
        self, mocker, stats, dimensions, existing_dims, optional_filled_dims
    ):
        mocker.patch.object(
            SlamSimulationDBHandler,
            SlamSimulationDBHandler.get_latest_run_id.__name__,
            return_value=None,
        )
        mocker.patch.object(
            UnitAreaStatsDBHandler,
            UnitAreaStatsDBHandler.find.__name__,
            return_value=stats,
        )

        result = StatsHandler.get_area_stats(
            site_id=1,
            task_type=TASK_TYPE.CONNECTIVITY,
            desired_dimensions=dimensions,
            fill_missing_dimensions=True,
        )

        assert result[1][1].keys() == dimensions
        for dim in existing_dims:
            assert not np.isnan(result[1][1][dim]["mean"])
        for dim in optional_filled_dims:
            assert np.isnan(result[1][1][dim]["mean"])

    def test_get_area_stats_calls_map_to_legacy_dimensions(self, mocker):
        mocker.patch.object(
            SlamSimulationDBHandler,
            SlamSimulationDBHandler.get_latest_run_id.__name__,
            return_value=None,
        )
        mocker.patch.object(
            UnitAreaStatsDBHandler,
            UnitAreaStatsDBHandler.find.__name__,
            return_value=[],
        )
        map_legacy_mocked = mocker.patch.object(
            StatsHandler,
            StatsHandler._map_to_legacy_dimensions.__name__,
            return_value=[],
        )

        StatsHandler.get_area_stats(
            site_id=1,
            task_type=TASK_TYPE.VIEW_SUN,
            desired_dimensions={VIEW_DIMENSION.VIEW_STREETS.value},
            legacy_dimensions_compatible=True,
        )
        map_legacy_mocked.assert_called_once()

    @pytest.mark.parametrize(
        "values, expected_result",
        [
            (
                [1, 2, 3],
                {
                    "p20": 1.4,
                    "p80": 2.6,
                    "median": 2.0,
                    "min": 1.0,
                    "max": 3.0,
                    "mean": 2.0,
                    "stddev": 0.816496580927726,
                    "count": 3,
                },
            ),
            (
                [0, 0, 0],
                {
                    "p20": 0.0,
                    "p80": 0.0,
                    "median": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "stddev": 0.0,
                    "count": 3,
                },
            ),
            (
                [0],
                {
                    "p20": 0.0,
                    "p80": 0.0,
                    "median": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "mean": 0.0,
                    "stddev": 0.0,
                    "count": 1,
                },
            ),
        ],
    )
    def test_compute_stats(self, values, expected_result):
        assert StatsHandler._compute_stats(values=values) == expected_result

    @pytest.mark.parametrize(
        "simulation_results, expected_stats",
        [
            (
                {1: {1: {"some": [1, 2, 3]}}},
                [
                    {
                        "unit_id": 1,
                        "area_id": 1,
                        "dimension": "some",
                        "p20": 1.4,
                        "p80": 2.6,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 3,
                    }
                ],
            )
        ],
    )
    def test_compute_area_stats(self, simulation_results, expected_stats):
        assert (
            list(
                StatsHandler(
                    run_id="run_id", results=simulation_results
                )._compute_unit_area_stats()
            )
            == expected_stats
        )

    @pytest.mark.parametrize(
        "exclude_area_ids, expected_stats",
        [
            (
                set(),
                [
                    {
                        "unit_id": 1,
                        "dimension": "some",
                        "p20": 1,
                        "p80": 3,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 6,
                    }
                ],
            ),
            (
                {1},
                [
                    {
                        "unit_id": 1,
                        "dimension": "some",
                        "p20": 1.4,
                        "p80": 2.6,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 3,
                    }
                ],
            ),
            (
                {1, 2},
                [],
            ),
        ],
    )
    def test_compute_unit_stats(self, exclude_area_ids, expected_stats):
        simulation_results = {
            1: {
                1: {"some": [1, 2, 3]},
                2: {"some": [1, 2, 3]},
            }
        }
        assert (
            list(
                StatsHandler(
                    run_id="loquetal", results=simulation_results
                )._compute_unit_stats(area_ids_to_exclude=exclude_area_ids)
            )
            == expected_stats
        )

    @pytest.mark.parametrize(
        "exclude_area_ids, expected_stats",
        [
            (
                set(),
                [
                    {
                        "client_id": "maisonette",
                        "dimension": "some",
                        "p20": 1.0,
                        "p80": 3.0,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 12,
                    },
                    {
                        "client_id": "studio",
                        "dimension": "some",
                        "p20": 1.0,
                        "p80": 3.0,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 6,
                    },
                ],
            ),
            (
                {1, 3},
                [
                    {
                        "client_id": "maisonette",
                        "dimension": "some",
                        "p20": 1.0,
                        "p80": 3.0,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 6,
                    },
                    {
                        "client_id": "studio",
                        "dimension": "some",
                        "p20": 1.0,
                        "p80": 3.0,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 6,
                    },
                ],
            ),
            (
                {1, 2, 3, 4},
                [
                    {
                        "client_id": "studio",
                        "dimension": "some",
                        "p20": 1.0,
                        "p80": 3.0,
                        "median": 2.0,
                        "min": 1.0,
                        "max": 3.0,
                        "mean": 2.0,
                        "stddev": 0.816496580927726,
                        "count": 6,
                    },
                ],
            ),
        ],
    )
    def test_compute_apartment_stats(self, mocker, exclude_area_ids, expected_stats):
        mocker.patch.object(
            StatsHandler,
            "unit_id_to_client_id",
            {1: "maisonette", 2: "maisonette", 3: "studio"},
        )
        simulation_results = {
            1: {
                1: {"some": [1, 2, 3]},
                2: {"some": [1, 2, 3]},
            },
            2: {
                3: {"some": [1, 2, 3]},
                4: {"some": [1, 2, 3]},
            },
            3: {
                5: {"some": [1, 2, 3]},
                6: {"some": [1, 2, 3]},
            },
        }
        assert not DeepDiff(
            list(
                StatsHandler(
                    run_id="loquetal", results=simulation_results
                )._compute_apartment_stats(area_ids_to_exclude=exclude_area_ids)
            ),
            expected_stats,
        )

    def test_map_to_legacy_dimensions(self, mocker):
        area_id = 28
        unit_id = 314
        street_dimensions = StatsHandler.LEGACY_DIMENSIONS_MAPPER[
            VIEW_DIMENSION.VIEW_STREETS.value
        ]
        mocker.patch.object(
            UnitSimulationDBHandler,
            UnitSimulationDBHandler.get_by.__name__,
            return_value={
                "results": {str(area_id): {d: [0.1, 0.2, 2] for d in street_dimensions}}
            },
        )
        unit_area_stats = {unit_id: {area_id: {}}}

        new_stats = StatsHandler._map_to_legacy_dimensions(
            unit_area_stats=unit_area_stats, run_id="loquetal"
        )
        assert new_stats[unit_id][area_id] == {
            "streets": {
                "p20": 0.7,
                "p80": 6.4,
                "median": 1.0,
                "min": 0.5,
                "max": 10.0,
                "mean": 3.8333333333333335,
                "stddev": 4.365266951236265,
                "count": 3,
            }
        }
