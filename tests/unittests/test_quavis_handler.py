from datetime import datetime

import pytest

from common_utils.constants import (
    SIMULATION_VERSION,
    VIEW_DIMENSION,
    SurroundingType,
    SurroundingTypeToView2Dimension,
    SurroundingTypeToViewDimension,
)
from handlers.quavis.quavis_handler import QuavisHandler

view_1_keys = set(SurroundingTypeToViewDimension.values()) | {
    "isovist",
    "sky",
}
view_2_keys = set(SurroundingTypeToView2Dimension.values()) | {
    "isovist",
    "sky",
}


def sun_keys(datetimes):
    return {"sun-" + str(datetime) for datetime in datetimes}


@pytest.mark.parametrize(
    "obs_point_result, datetimes, sim_version, expected_keys",
    [
        (
            {"simulations": {"area_by_group": {"mountains": 1}, "sun": [0]}},
            [datetime(1987, 3, 3, 12, 0, 0)],
            SIMULATION_VERSION.PH_2020,
            view_1_keys | sun_keys([datetime(1987, 3, 3, 12, 0, 0)]),
        ),
        (
            {"simulations": {"area_by_group": {"FOREST": 1}, "sun": [0]}},
            [datetime(1987, 3, 3, 12, 0, 0)],
            SIMULATION_VERSION.EXPERIMENTAL,
            view_2_keys | sun_keys([datetime(1987, 3, 3, 12, 0, 0)]),
        ),
        (
            {"simulations": {"area_by_group": {"random_field": 1}, "sun": []}},
            [],
            SIMULATION_VERSION.PH_01_2021,
            view_1_keys | {"random_field"},
        ),
    ],
)
def test_get_results_of_obs_point(
    obs_point_result, datetimes, sim_version, expected_keys
):
    obs_point_result["simulations"]["volume"] = 5
    obs_point_result["simulations"]["area"] = 5
    dimensions_mapping = (
        SurroundingTypeToView2Dimension
        if sim_version == SIMULATION_VERSION.EXPERIMENTAL
        else SurroundingTypeToViewDimension
    )

    result = QuavisHandler._get_results_of_obs_point(
        obs_point_result=obs_point_result,
        datetimes=datetimes,
        dimensions_mapping=dimensions_mapping,
    )
    assert set(result.keys()) == expected_keys


@pytest.mark.parametrize("sim_version", [version for version in SIMULATION_VERSION])
@pytest.mark.parametrize(
    "obs_point_result, expected",
    [
        (
            {
                "simulations": {
                    "area_by_group": {
                        SurroundingType.LAKES.name: 1.0,
                        SurroundingType.RIVERS.name: 2.0,
                        SurroundingType.SEA.name: 5.0,
                        SurroundingType.BUILDINGS.name: 10.0,
                    },
                    "sun": [],
                }
            },
            {
                VIEW_DIMENSION.VIEW_WATER.value: 8.0,
                VIEW_DIMENSION.VIEW_BUILDINGS.value: 10.0,
            },
        ),
        (
            {
                "simulations": {
                    "area_by_group": {
                        SurroundingType.LAKES.name: 1.5,
                        SurroundingType.RIVERS.name: 2.5,
                        SurroundingType.SEA.name: 5.0,
                        SurroundingType.FOREST.name: 22.0,
                        SurroundingType.TREES.name: 2.0,
                    },
                    "sun": [],
                }
            },
            {
                VIEW_DIMENSION.VIEW_WATER.value: 9.0,
                VIEW_DIMENSION.VIEW_GREENERY.value: 24.0,
            },
        ),
    ],
)
def test_get_results_of_obs_point_aggregate_types(
    obs_point_result, expected, sim_version
):
    obs_point_result["simulations"]["volume"] = 5
    obs_point_result["simulations"]["area"] = 5

    dimensions_mapping = (
        SurroundingTypeToView2Dimension
        if sim_version == SIMULATION_VERSION.EXPERIMENTAL
        else SurroundingTypeToViewDimension
    )
    final_expected = {"sky": 7.56637, "isovist": 5}
    for key in dimensions_mapping.values():
        final_expected[key] = expected.get(key, 0)

    result = QuavisHandler._get_results_of_obs_point(
        obs_point_result=obs_point_result,
        datetimes=[],
        dimensions_mapping=dimensions_mapping,
    )

    assert result == pytest.approx(final_expected)
