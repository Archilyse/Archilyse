import pytest
from shapely.geometry import box

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    POTENTIAL_LAYOUT_MODE,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
)
from handlers.db import PotentialSimulationDBHandler
from handlers.simulations.potential_tile_exporter import PotentialEntityProvider
from tests.constants import SUN_ENTITY, VIEW_ENTITY


class TestPotentialEntityProvider:
    @pytest.fixture
    def potential_simulations(self, potential_sun_results, potential_view_results):
        sun_simulation, view_simulation = [
            PotentialSimulationDBHandler.add(
                layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
                simulation_version=SIMULATION_VERSION.PH_2022_H1.name,
                region=REGION.CH.name,
                type=simulation_type,
                building_footprint=box(0, 0, 1, 1),
                floor_number=0,
                status=ADMIN_SIM_STATUS.SUCCESS.name,
                identifier=None,
                result=results,
            )
            for simulation_type, results in {
                SIMULATION_TYPE.SUN: potential_sun_results,
                SIMULATION_TYPE.VIEW: potential_view_results,
            }.items()
        ]
        return sun_simulation, view_simulation

    @pytest.mark.parametrize("simulation_type", list(SIMULATION_TYPE))
    def test_get_simulation_ids(self, simulation_type, potential_simulations):
        (simulation_id,) = PotentialEntityProvider.get_simulation_ids(
            simulation_type=simulation_type, query_shape=box(0, 0, 0.5, 0.5)
        )
        assert PotentialSimulationDBHandler.exists(
            id=simulation_id, type=simulation_type, identifier=None, status="SUCCESS"
        )

    @pytest.mark.parametrize(
        "simulation_type, expected_entity",
        [
            (SIMULATION_TYPE.VIEW, VIEW_ENTITY),
            (SIMULATION_TYPE.SUN, SUN_ENTITY),
        ],
    )
    def test_get_entities(
        self, simulation_type, expected_entity, potential_simulations
    ):
        entities = list(
            PotentialEntityProvider.get_entities(
                simulation_type=simulation_type, query_shape=box(0, 0, 0.5, 0.5)
            )
        )
        assert entities == [expected_entity]
