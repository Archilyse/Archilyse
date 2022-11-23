import pytest

from simulations.noise import NoiseRayTracerSimulator


class TestNoiseRayTracer:
    @pytest.mark.parametrize(
        "noise_level_at_source, distance, expected_noise",
        [(100, 100, 72.04), (100, 1, 112.04)],
    )
    def test_attenuate_noise(self, noise_level_at_source, distance, expected_noise):
        assert NoiseRayTracerSimulator._attenuate_noise(
            noise_at_source=noise_level_at_source, distance=distance
        ) == pytest.approx(expected_noise, abs=1e-2)
