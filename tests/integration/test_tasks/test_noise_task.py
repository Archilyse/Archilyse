import json

import pytest
from deepdiff import DeepDiff
from shapely.geometry import Point

from brooks.types import AreaType
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    NOISE_SURROUNDING_TYPE,
    NOISE_TIME_TYPE,
    TASK_TYPE,
)
from handlers import SlamSimulationHandler
from handlers.db import (
    AreaDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    SlamSimulationDBHandler,
    UnitAreaDBHandler,
)


@pytest.fixture
def noise_expected(fixtures_path):
    with fixtures_path.joinpath("noise/noise_expected.json").open() as f:
        return json.load(f)


def test_noise_task(
    site_with_1_unit,
    celery_eager,
    mocked_gcp_download,
    mocker,
    noise_expected,
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
                {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
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
    assert not SlamSimulationDBHandler.find(site_id=site_id)

    # when
    wf = WorkflowGenerator(site_id=site_id)
    wf.get_noise_windows_simulation_task_chain().delay()
    wf.get_noise_simulation_task_chain().delay()

    # then
    simulations = SlamSimulationDBHandler.find(site_id=site_id, type=TASK_TYPE.NOISE)
    assert len(simulations) == 1
    assert simulations[0]["state"] == ADMIN_SIM_STATUS.SUCCESS.name
    assert not simulations[0]["errors"]

    simulation_results = SlamSimulationHandler.get_all_results(
        site_id=site_id, task_type=TASK_TYPE.NOISE
    )
    assert len(simulation_results) == 1

    unit_results = simulation_results[0]["results"]
    unit_areas = UnitAreaDBHandler.find(unit_id=site_with_1_unit["units"][0]["id"])
    areas = AreaDBHandler.find(plan_id=site_with_1_unit["plan"]["id"])
    areas_by_id = {a["id"]: a["area_type"] for a in areas}

    # Shafts are too small and don't have any observation point
    assert set(unit_results.keys()) == set(
        str(u["area_id"])
        for u in unit_areas
        if areas_by_id[u["area_id"]] not in {AreaType.SHAFT.value}
    )
    assert all(
        f"noise_{noise_type.name}" in area
        for area in unit_results.values()
        for noise_type in NOISE_SURROUNDING_TYPE
    )

    for area_result in unit_results.values():
        #  All area results have the same size (obs points consistency)
        assert len({len(sim_values) for sim_values in area_result.values()}) == 1
        for noise_type in NOISE_SURROUNDING_TYPE:
            #  Each area have the same noise level
            noise_values = area_result[f"noise_{noise_type.name}"]
            assert len(set(noise_values)) == 1

    flattened = SlamSimulationHandler._format_results(
        raw_results=unit_results, flattened=True
    )

    if update_fixtures:
        with fixtures_path.joinpath("noise/noise_expected.json").open("w") as f:
            json.dump(flattened, f)

    for dimension, values in flattened.items():
        assert not DeepDiff(values, noise_expected[dimension], significant_digits=2)
