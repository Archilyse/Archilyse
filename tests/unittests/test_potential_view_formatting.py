from itertools import chain

from deepdiff import DeepDiff

from common_utils.constants import IMMO_RESPONSE_PRECISION, REGION, VIEW_SUN_DIMENSIONS
from handlers import PotentialSimulationHandler
from tests.utils import check_immo_response_precision


def test_potential_view_formatting(potential_view_results_test_api_simulations):
    """
    Given simulation results
    When formatted
    """
    formatted_potential_view_results = (
        PotentialSimulationHandler.format_view_sun_raw_results(
            potential_view_results_test_api_simulations,
            dimensions=list(chain(*VIEW_SUN_DIMENSIONS.values())),
            simulation_region=REGION.CH,
        )
    )

    """
    Then the result is a dictionary
    and observation_points in the keys
    and all records have the same amount of values as observation points
    and all values precision is IMMO_RESPONSE_PRECISION maximum
    """
    assert isinstance(formatted_potential_view_results, dict)
    assert "observation_points" in formatted_potential_view_results.keys()

    check_immo_response_precision(
        formatted_potential_view_results, IMMO_RESPONSE_PRECISION
    )


def test_potential_view_formatting_from_cz():
    view_sun_raw_results = {
        "unit_id": {
            "area_id": {
                "observation_points": [[-1045351.3590536425, -740478.8567660097, 0.0]],
                "galaxies": [1.0],
            }
        }
    }
    formatted_potential_view_results = (
        PotentialSimulationHandler.format_view_sun_raw_results(
            view_sun_raw_results=view_sun_raw_results,
            dimensions=["galaxies"],
            simulation_region=REGION.CZ,
        )
    )
    assert not DeepDiff(
        dict(formatted_potential_view_results),
        {
            "galaxies": [1.0],
            "observation_points": [
                {"height": 0.0, "lat": 50.0694869907022, "lon": 14.457962467174319}
            ],
        },
        ignore_order=True,
        significant_digits=IMMO_RESPONSE_PRECISION,
    )
