import pytest

from common_utils.constants import NOISE_SURROUNDING_TYPE
from handlers.db import UnitAreaDBHandler
from simulations.noise import NoiseSimulationHandler


def test_noise_sim_handler(site, building, plan, make_classified_split_plans):
    all_areas = make_classified_split_plans(
        plan, building=building, floor_number=0, annotations_plan_id=1478
    )
    unit_areas = UnitAreaDBHandler.find()

    noise_fake = {n.value: [60] for n in NOISE_SURROUNDING_TYPE}
    obs_points_fake = {"observation_points": [(1, 1, 1)]}
    area_windows_noises = {unit_area["unit_id"]: {} for unit_area in unit_areas}

    for unit_area in unit_areas:
        area_windows_noises[unit_area["unit_id"]][unit_area["area_id"]] = {
            **obs_points_fake,
            **noise_fake,
        }
    # we removed the elevator areas from the area_windows_noises, to check the format of the output
    noise_simulator = NoiseSimulationHandler(
        site_id=site["id"], noise_window_per_area=area_windows_noises
    )
    result = noise_simulator.get_noise_for_site()
    simplified_resuts = {
        a_id: vals["noise_TRAIN_DAY"][0]
        for unit_id in result.keys()
        for a_id, vals in result[unit_id].items()
    }
    assert len(simplified_resuts) == len(all_areas) - 4  # -3 shaft areas and 1 void
    assert sorted(set(simplified_resuts.values())) == pytest.approx(
        [
            19.999999999999993,
            47.22865933072759,
            47.276879896571714,
            47.34527562081226,
            48.43266932125443,
            48.514261448076226,
            49.323583021542525,
            49.89738889423478,
            49.90545095535711,
            49.96603712057462,
            51.33915128870261,
            51.44080178879125,
            52.50104268632043,
            52.50552728611406,
        ],
        abs=0.01,
    )
    assert len([True for x in simplified_resuts.values() if x < 0.0001]) == 0
