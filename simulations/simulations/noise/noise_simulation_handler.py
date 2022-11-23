from math import log
from typing import Dict, List, Set

from brooks.models import SimArea, SimLayout, SimSpace
from common_utils.constants import (
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION,
    NOISE_SURROUNDING_TYPE,
)
from common_utils.typing import (
    AreaID,
    LocationTuple,
    NoiseAreaResultsType,
    NoiseTypeName,
    UnitID,
)
from handlers import SiteHandler


class NoiseSimulationHandler:
    DEFAULT_ISOLATION_FACTOR = 1.0
    DEFAULT_MAX_ATTENUATION = 40.0

    def __init__(
        self,
        site_id: int,
        noise_window_per_area: Dict[UnitID, Dict[AreaID, NoiseAreaResultsType]],
    ):
        self.site_id = site_id
        self.noise_window_per_area = noise_window_per_area

    def get_noise_for_site(
        self,
    ) -> Dict[UnitID, Dict[AreaID, NoiseAreaResultsType]]:
        area_obs_points_by_unit = SiteHandler.get_obs_points_by_unit_and_area(
            site_id=self.site_id,
            grid_resolution=DEFAULT_GRID_RESOLUTION,
            grid_buffer=DEFAULT_GRID_BUFFER,
            obs_height=0,
        )

        # get the areas windows noises, dedup and calc noise for space, then each area inside get same val
        site_results: Dict[UnitID, Dict[AreaID, NoiseAreaResultsType]] = {
            unit_id: {
                area_id: {"observation_points": points.tolist()}
                for area_id, points in unit_results.items()
            }
            for unit_id, unit_results in area_obs_points_by_unit.items()
        }

        for unit_info, unit_layout in SiteHandler.get_unit_layouts(
            site_id=self.site_id, scaled=True, georeferenced=True
        ):
            for space in unit_layout.spaces:
                space_noises = self.calculate_space_noises(
                    layout=unit_layout, space=space, unit_id=unit_info["id"]
                )
                for area in space.areas:
                    if area.db_area_id not in site_results[unit_info["id"]]:
                        # There are no obs points for this area
                        continue
                    len_obs_points = len(
                        site_results[unit_info["id"]][area.db_area_id][
                            "observation_points"
                        ]
                    )
                    for noise_name, noise_val in space_noises.items():
                        site_results[unit_info["id"]][area.db_area_id][noise_name] = [
                            noise_val
                        ] * len_obs_points

        return site_results

    @staticmethod
    def _avg_decibels(values: List[float]) -> float:
        """Decibels are logarithmic quantities.
        Therefore, they must be averaged logarithmically rather than algebraically"""
        return (
            10.0 * log(sum([10 ** (x / 10) for x in values]) / len(values), 10)
            if len(values)
            else 0.0
        )

    @staticmethod
    def _get_space_surface(space) -> float:
        return space.footprint.length * space.height[1]

    @staticmethod
    def _get_openings_surface(layout: SimLayout, areas: Set[SimArea]) -> float:
        openings = {
            opening
            for area in areas
            for opening in layout.get_windows_and_outdoor_doors(area=area)
        }
        return sum(
            (opening.height[1] - opening.height[0]) * opening.length
            for opening in openings
        )

    @classmethod
    def noise_attenuation(cls, space_surface: float, openings_surface: float) -> float:
        """Returns a positive value of attenuation in dba"""
        percentage_open = openings_surface / space_surface
        return (
            -10.0 * log(percentage_open, 10)
            if percentage_open
            else cls.DEFAULT_MAX_ATTENUATION
        )

    def calculate_space_noises(
        self, unit_id: int, layout: SimLayout, space: SimSpace
    ) -> Dict[NoiseTypeName, float]:
        """
        Average all the noises of the different openings and subtracts
        an attenuation factor based on the size of windows and the space
        """
        db_area_ids = {area.db_area_id for area in space.areas}
        space_area_noises = [
            values
            for area_id, values in self.noise_window_per_area[unit_id].items()
            if area_id in db_area_ids
        ]
        if not space_area_noises:
            return {nt.value: 0.0 for nt in NOISE_SURROUNDING_TYPE}

        space_noise_attenuation = self.noise_attenuation(
            space_surface=self._get_space_surface(space=space),
            openings_surface=self._get_openings_surface(
                layout=layout, areas=space.areas
            ),
        )

        # we have to dedup noises bases on the different locations (areas can share openings)
        unique_location_noises: Dict[LocationTuple, Dict[str, float]] = {}
        for area_info in space_area_noises:
            for i, location in enumerate(area_info["observation_points"]):
                if location not in unique_location_noises:
                    unique_location_noises[location] = {
                        noise_type.value: area_info[noise_type.value][i]  # type: ignore
                        for noise_type in NOISE_SURROUNDING_TYPE
                    }
        final_noise = {}
        for noise_type in NOISE_SURROUNDING_TYPE:
            noises = [val[noise_type.value] for val in unique_location_noises.values()]
            avg_noise = self._avg_decibels(noises)
            final_noise[noise_type.value] = max(
                avg_noise - self.DEFAULT_ISOLATION_FACTOR * space_noise_attenuation, 0.0
            )
        return final_noise
