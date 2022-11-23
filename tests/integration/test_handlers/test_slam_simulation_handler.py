from collections import defaultdict

import pytest
from deepdiff import DeepDiff

from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from common_utils.exceptions import DBNotFoundException, SimulationNotSuccessException
from handlers.db import (
    SlamSimulationDBHandler,
    UnitAreaDBHandler,
    UnitAreaStatsDBHandler,
    UnitSimulationDBHandler,
    UnitStatsDBHandler,
)
from handlers.simulations.slam_simulation_handler import SlamSimulationHandler


def test_register_simulation(site):
    run_id = "My-Run-ID"

    # when
    simulation = SlamSimulationHandler.register_simulation(
        site_id=site["id"], run_id=run_id, task_type=TASK_TYPE.VIEW_SUN
    )

    # then
    assert simulation["run_id"] == run_id
    assert simulation["site_id"] == site["id"]
    assert simulation["type"] == TASK_TYPE.VIEW_SUN.name
    assert simulation["state"] == ADMIN_SIM_STATUS.PENDING.name
    assert SlamSimulationDBHandler.get_by(run_id=run_id) == simulation


def test_update_state(pending_simulation):
    # when
    simulation = SlamSimulationHandler.update_state(
        run_id=pending_simulation["run_id"],
        state=ADMIN_SIM_STATUS.PROCESSING,
        errors={"hallo": "welt"},
    )

    # then
    assert simulation["state"] == ADMIN_SIM_STATUS.PROCESSING.value
    assert simulation["errors"] == {"hallo": "welt"}


def test_slam_simulation_handler_store_results(
    pending_simulation, first_pipeline_complete_db_models
):
    # given
    fake_results = defaultdict(dict)
    for unit_area in UnitAreaDBHandler.find_in(
        unit_id=[u["id"] for u in first_pipeline_complete_db_models["units"]],
    ):
        fake_results[unit_area["unit_id"]][str(unit_area["area_id"])] = {
            "some": [1, 2, 3]
        }

    # when
    SlamSimulationHandler.store_results(
        run_id=pending_simulation["run_id"], results=fake_results
    )

    # then
    results_db = UnitSimulationDBHandler.find(run_id=pending_simulation["run_id"])
    assert {r["unit_id"]: r["results"] for r in results_db} == fake_results

    expected_stats = {
        "p20": 1.4,
        "p80": 2.6,
        "median": 2.0,
        "min": 1.0,
        "max": 3.0,
        "mean": 2.0,
        "stddev": 0.816496580927726,
        "count": 3,
    }
    results_db = UnitAreaStatsDBHandler.find(run_id=pending_simulation["run_id"])
    assert not DeepDiff(
        [
            {
                "run_id": pending_simulation["run_id"],
                "unit_id": int(unit_id),
                "area_id": int(area_id),
                "dimension": dimension,
                **expected_stats,
            }
            for unit_id, unit_area_results in fake_results.items()
            for area_id, area_results in unit_area_results.items()
            for dimension in area_results.keys()
        ],
        results_db,
        ignore_order=True,
    )

    results_db = UnitStatsDBHandler.find(run_id=pending_simulation["run_id"])
    expected_result = [
        {
            "run_id": pending_simulation["run_id"],
            "unit_id": int(unit_id),
            "dimension": dimension,
            "only_interior": only_interior,
            **expected_stats,
        }
        for unit_id, unit_area_results in fake_results.items()
        for dimension in set(
            dimension
            for area_results in unit_area_results.values()
            for dimension in area_results.keys()
        )
        for only_interior in [True, False]
    ]
    assert not DeepDiff(expected_result, results_db, ignore_order=True)


def test_get_simulation_raises_not_found_exception(site):
    with pytest.raises(DBNotFoundException):
        SlamSimulationHandler.get_simulation(
            site_id=site["id"], task_type=TASK_TYPE.BASIC_FEATURES
        )


def test_get_simulation(basic_features_finished):
    simulation = SlamSimulationHandler.get_simulation(
        site_id=basic_features_finished["site_id"], task_type=TASK_TYPE.BASIC_FEATURES
    )
    assert basic_features_finished == simulation


def test_get_results_raises_not_found_exception(unit):
    with pytest.raises(DBNotFoundException):
        SlamSimulationHandler.get_results(
            unit_id=unit["id"],
            task_type=TASK_TYPE.BASIC_FEATURES,
            site_id=unit["site_id"],
        )


def test_get_results_raises_not_success_exception(unit, basic_features_started):
    with pytest.raises(SimulationNotSuccessException):
        SlamSimulationHandler.get_results(
            unit_id=unit["id"],
            task_type=TASK_TYPE.BASIC_FEATURES,
            site_id=unit["site_id"],
        )
