import json

import pytest
from deepdiff import DeepDiff
from shapely.geometry import Point

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    NOISE_SURROUNDING_TYPE,
    NOISE_TIME_TYPE,
    TASK_TYPE,
)
from handlers import SlamSimulationHandler
from handlers.db import PlanDBHandler, SiteDBHandler, SlamSimulationDBHandler


@pytest.fixture
def noise_window_expected(fixtures_path):
    with fixtures_path.joinpath("noise/noise_window_expected.json").open() as f:
        return json.load(f)


def test_noise_window_task(
    site_with_1_unit,
    celery_eager,
    mocked_gcp_download,
    mocker,
    noise_window_expected,
    fixtures_path,
    update_fixtures=False,
):
    from simulations.noise import noise_window_simulation_handler as nwsh
    from tasks.workflow_tasks import WorkflowGenerator

    mocker.patch.object(
        nwsh,
        "get_surrounding_footprints",
        return_value=[],
    )
    mocker.patch.object(
        nwsh,
        "get_noise_sources",
        return_value=[
            (
                Point(2679538.7 - 200, 1249432.5 - 200),
                {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 50},
            )
        ],
    )
    zh_hardbruecke = Point(8.492116888772355, 47.390917203653025)

    # given
    # a site at Zurich Hardbruecke
    site_id = site_with_1_unit["site"]["id"]

    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(
            lon=zh_hardbruecke.x,
            lat=zh_hardbruecke.y,
        ),
    )
    PlanDBHandler.update(
        item_pks=dict(id=site_with_1_unit["plan"]["id"]),
        new_values=dict(
            georef_x=zh_hardbruecke.x,
            georef_y=zh_hardbruecke.y,
            georef_rot_y=0,
            georef_rot_x=0,
            georef_scale=0.0001,
        ),
    )

    # and no simulation results in the database
    assert not SlamSimulationDBHandler.exists(site_id=site_id)

    # when
    WorkflowGenerator(site_id=site_id).get_noise_windows_simulation_task_chain().delay()

    # then
    all_simulations = SlamSimulationDBHandler.find(site_id=site_id)
    assert len(all_simulations) == 1
    assert all_simulations[0]["type"] == TASK_TYPE.NOISE_WINDOWS.name
    assert all_simulations[0]["state"] == ADMIN_SIM_STATUS.SUCCESS.name
    assert not all_simulations[0]["errors"]

    simulation_results = SlamSimulationHandler.get_all_results(
        site_id=site_id, task_type=TASK_TYPE.NOISE_WINDOWS
    )
    assert len(simulation_results) == 1

    unit_results = simulation_results[0]["results"]

    # all area results have the noise keys
    assert all(
        noise_type.value in area_vals
        for area_vals in unit_results.values()
        for noise_type in NOISE_SURROUNDING_TYPE
    )

    #  All area results have the same size (obs points consistency)
    for area_result in unit_results.values():
        assert len({len(sim_values) for sim_values in area_result.values()}) == 1

    if update_fixtures:
        to_save = {}
        for area, results in unit_results.items():
            to_save[area] = {
                "observation_points": results["observation_points"],
                "noise": results["noise_TRAFFIC_DAY"],
            }
        with fixtures_path.joinpath("noise/noise_window_expected.json").open("w") as f:
            json.dump(to_save, f)

    # assert all areas values
    for area_id, values in unit_results.items():
        assert len(noise_window_expected[area_id]["observation_points"]) == len(
            values["observation_points"]
        )
        assert not DeepDiff(
            noise_window_expected[area_id]["observation_points"],
            values["observation_points"],
            ignore_order=True,
            significant_digits=2,
        )
        assert len(noise_window_expected[area_id]["noise"]) == len(
            values["noise_TRAFFIC_DAY"]
        )
        assert not DeepDiff(
            noise_window_expected[area_id]["noise"],
            values["noise_TRAFFIC_DAY"],
            ignore_order=True,
            significant_digits=2,
        )
