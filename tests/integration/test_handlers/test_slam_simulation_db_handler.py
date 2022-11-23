import pytest

from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from common_utils.exceptions import DBNotFoundException
from handlers.db import SlamSimulationDBHandler
from handlers.simulations.slam_simulation_handler import SlamSimulationHandler


def test_get_latest_run_id_raises_not_found_exception(unit):
    with pytest.raises(DBNotFoundException):
        SlamSimulationDBHandler.get_latest_run_id(
            site_id=unit["id"], task_type=TASK_TYPE.BASIC_FEATURES
        )


def test_get_latest_run_id(basic_features_started):
    run_id = SlamSimulationDBHandler.get_latest_run_id(
        site_id=basic_features_started["site_id"], task_type=TASK_TYPE.BASIC_FEATURES
    )
    assert basic_features_started["run_id"] == run_id


def test_get_latest_run_id_state(basic_features_started):
    with pytest.raises(DBNotFoundException):
        SlamSimulationDBHandler.get_latest_run_id(
            site_id=basic_features_started["site_id"],
            task_type=TASK_TYPE.BASIC_FEATURES,
            state=ADMIN_SIM_STATUS.SUCCESS,
        )

    run_id = SlamSimulationDBHandler.get_latest_run_id(
        site_id=basic_features_started["site_id"],
        task_type=TASK_TYPE.BASIC_FEATURES,
        state=ADMIN_SIM_STATUS.PROCESSING,
    )

    assert basic_features_started["run_id"] == run_id


def test_check_state_returns_false(site):
    assert not SlamSimulationDBHandler.check_state(
        site_id=site["id"],
        task_type=TASK_TYPE.BASIC_FEATURES,
        states=[ADMIN_SIM_STATUS.SUCCESS],
    )


def test_check_state_returns_true(site, basic_features_finished):
    assert SlamSimulationDBHandler.check_state(
        site_id=site["id"],
        task_type=TASK_TYPE.BASIC_FEATURES,
        states=[ADMIN_SIM_STATUS.SUCCESS],
    )


def test_check_state_returns_latest_state(site, basic_features_finished):
    run_id = "my-other-run"
    SlamSimulationHandler.register_simulation(
        run_id=run_id,
        site_id=site["id"],
        task_type=TASK_TYPE.BASIC_FEATURES,
        state=ADMIN_SIM_STATUS.PROCESSING,
    )
    assert SlamSimulationDBHandler.check_state(
        site_id=site["id"],
        task_type=TASK_TYPE.BASIC_FEATURES,
        states=[ADMIN_SIM_STATUS.PROCESSING],
    )
