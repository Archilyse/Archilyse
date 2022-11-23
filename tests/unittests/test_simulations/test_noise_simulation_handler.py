import pytest

from simulations.noise import NoiseSimulationHandler


class TestNoiseSimulationHandler:
    @pytest.mark.parametrize(
        "plan_id, expected",
        [
            (
                4976,
                {
                    2.91,
                    3.99,
                    17.48,
                    19.79,
                    20.47,
                    21.79,
                    22.2,
                    25.32,
                    25.58,
                    27.59,
                    31.57,
                    34.62,
                    34.82,
                    36.43,
                    37.64,
                    37.86,
                    39.87,
                    40.89,
                    54.59,
                    62.05,
                    64.03,
                    76.33,
                    82.16,
                },
            )
        ],
    )
    def test_noise_simulator_get_space_surface(
        self,
        plan_id,
        expected,
        layout_scaled_classified_wo_db_conn,
    ):
        layout = layout_scaled_classified_wo_db_conn(plan_id)
        results = sorted(
            NoiseSimulationHandler._get_space_surface(space=space)
            for space in layout.spaces
        )
        assert results == pytest.approx(sorted(expected), abs=0.01)

    @pytest.mark.parametrize(
        "plan_id,expected",
        [(4976, 62.7768), (2494, 111.2495)],
    )
    def test_noise_simulator_get_openings_surface(
        self,
        plan_id,
        expected,
        layout_scaled_classified_wo_db_conn,
    ):
        layout = layout_scaled_classified_wo_db_conn(plan_id)
        assert NoiseSimulationHandler._get_openings_surface(
            layout=layout, areas=layout.areas
        ) == pytest.approx(expected, abs=0.01)

    @pytest.mark.parametrize(
        "space_surface,openings_surface, expected",
        [(10, 10, 0), (10, 9, 0.4575), (10, 0, 40)],
    )
    def test_noise_simulator_noise_attenuation(
        self, space_surface, openings_surface, expected
    ):
        assert NoiseSimulationHandler.noise_attenuation(
            space_surface=space_surface, openings_surface=openings_surface
        ) == pytest.approx(expected, abs=0.0001)
