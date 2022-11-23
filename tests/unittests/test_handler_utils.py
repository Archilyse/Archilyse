from common_utils.constants import (
    SIMULATION_VALUE_TYPE,
    SUN_DIMENSION,
    UNIT_BASICS_DIMENSION,
    VIEW_DIMENSION,
)
from handlers.utils import get_simulation_name


def test_get_simulation_name(unit_vector_with_balcony):
    for sim_name in (
        get_simulation_name(dimension=sim_dimension, value_type=value_type)
        for sim_type in [SUN_DIMENSION, VIEW_DIMENSION, UNIT_BASICS_DIMENSION]
        for sim_dimension in sim_type
        for value_type in SIMULATION_VALUE_TYPE
    ):
        assert sim_name in unit_vector_with_balcony[0]
