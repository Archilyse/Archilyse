from typing import Iterator, Optional, Union

import numpy as np
from shapely.geometry import Point

from common_utils.constants import SIMULATION_VERSION
from handlers import SiteHandler
from handlers.quavis.quavis_handler import QuavisHandler


class SLAMQuavisHandler(QuavisHandler):
    @classmethod
    def use_sun_v2(cls) -> bool:
        return False

    @classmethod
    def get_lat_lon_site_location(cls, entity_info: dict) -> Point:
        return SiteHandler.get_lat_lon_location(site_info=entity_info)

    @classmethod
    def get_obs_points_by_area(
        cls,
        entity_info: dict,
        grid_resolution: float,
        grid_buffer: float,
        obs_height: float,
        simulation_version: SIMULATION_VERSION,
    ) -> dict[Union[int, str], dict[int, np.ndarray]]:
        from handlers import SiteHandler

        return SiteHandler.get_obs_points_by_unit_and_area(
            site_id=entity_info["id"],
            grid_resolution=grid_resolution,
            grid_buffer=grid_buffer,
            obs_height=obs_height,
        )

    @classmethod
    def get_site_triangles(
        cls, entity_info: dict, simulation_version: SIMULATION_VERSION
    ) -> Iterator[tuple[str, np.ndarray]]:
        from handlers import SiteHandler

        return SiteHandler.get_layout_triangles(
            site_id=entity_info["id"],
            simulation_version=simulation_version,
            by_unit=False,
        )

    @staticmethod
    def get_surrounding_triangles(
        entity_info: dict, simulation_version: Optional[SIMULATION_VERSION] = None
    ) -> Iterator:
        from handlers import SiteHandler

        return SiteHandler.get_view_surroundings(site_info=entity_info)


class SLAMSunV2QuavisHandler(SLAMQuavisHandler):
    @classmethod
    def use_sun_v2(cls) -> bool:
        return True
