import math
from typing import Dict, List, Tuple, Union

from contexttimer import timer
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from common_utils.constants import NOISE_TIME_TYPE
from common_utils.logger import logger
from common_utils.typing import Distance
from simulations.noise.utils import aggregate_noises


class NoiseRayTracerSimulator:
    OBSERVATION_DISTANCE = 4

    def __init__(self, noise_sources: List[Tuple[Point, Dict[NOISE_TIME_TYPE, float]]]):
        self._noise_sources = noise_sources

    @classmethod
    def _attenuate_noise(cls, distance: float, noise_at_source: float) -> float:
        """
        Attenuates a point noise source assuming noise_at_source is 4 meter distant from
        the actual noise emitting source.
        """
        return max(
            noise_at_source - 20 * math.log(distance / cls.OBSERVATION_DISTANCE, 10),
            0.0,
        )

    @staticmethod
    def _get_real_distance(source: float, end_point: float) -> float:
        return math.sqrt(source**2 + end_point**2)

    @timer(logger=logger)
    def get_noises_2d_distances_at(
        self, location: Point, blocking_elements: Union[Polygon, MultiPolygon]
    ) -> List[Tuple[Dict[NOISE_TIME_TYPE, float], Distance]]:
        """Returns noise at origin, distance"""
        noises = []
        for remote_noise_source, noises_at_source in self._noise_sources:
            noise_ray = LineString([location, remote_noise_source])
            if not noise_ray.intersects(blocking_elements):  # There is direct view
                noises.append((noises_at_source, noise_ray.length))
        return noises

    @classmethod
    def calculate_noise_3d(
        cls,
        noises: List[Tuple[Dict[NOISE_TIME_TYPE, float], Distance]],
        height: float,
        noise_time: NOISE_TIME_TYPE,
    ) -> float:
        noises_attenuated = []
        for noises_level, distance_2d in noises:
            noise_level = noises_level[noise_time]
            noises_attenuated.append(
                cls._attenuate_noise(
                    distance=cls._get_real_distance(
                        source=distance_2d,
                        # To account that the source is at OBSERVATION_DISTANCE height
                        end_point=height - cls.OBSERVATION_DISTANCE,
                    ),
                    noise_at_source=noise_level,
                )
            )
        return aggregate_noises(noises=noises_attenuated)
