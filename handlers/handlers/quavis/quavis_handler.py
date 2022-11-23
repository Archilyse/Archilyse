from collections import defaultdict
from datetime import datetime
from typing import Any, DefaultDict, Iterable, Iterator, Union

import numpy as np
from shapely.geometry import Point

from common_utils.chunker import chunker
from common_utils.constants import (
    DEFAULT_WRAPPER_RESOLUTION,
    SIMULATION_VERSION,
    SurroundingTypeToView2Dimension,
    SurroundingTypeToViewDimension,
)
from common_utils.exceptions import QuavisSimulationException
from dufresne.solar_from_wgs84 import get_solar_parameters_from_wgs84
from simulations.view.view_wrapper import ViewWrapper
from surroundings.utils import SurrTrianglesType


class QuavisHandler:
    # METHODS IMPLEMENTED FOR SLAM AND POTENTIAL VIEW IN SUBCLASSES
    @classmethod
    def get_lat_lon_site_location(cls, entity_info: dict) -> Point:
        raise NotImplementedError

    @classmethod
    def get_obs_points_by_area(
        cls,
        entity_info: dict,
        grid_resolution: float,
        grid_buffer: float,
        obs_height: float,
        simulation_version: SIMULATION_VERSION,
    ) -> dict[Any, dict[Any, np.ndarray]]:
        raise NotImplementedError

    @classmethod
    def get_site_triangles(
        cls, entity_info: dict, simulation_version: SIMULATION_VERSION
    ) -> Iterable:
        raise NotImplementedError

    @staticmethod
    def get_surrounding_triangles(
        entity_info: dict, simulation_version: SIMULATION_VERSION
    ) -> Iterator[SurrTrianglesType]:
        raise NotImplementedError

    @classmethod
    def use_sun_v2(cls) -> bool:
        raise NotImplementedError

    # QUAVIS INPUT / OUTPUT GENERATION

    @classmethod
    def get_quavis_input(
        cls,
        entity_info: dict,
        grid_resolution: float,
        grid_buffer: float,
        obs_height: float,
        datetimes: list[datetime],
        simulation_version: SIMULATION_VERSION = SIMULATION_VERSION.PH_01_2021,
    ) -> dict:
        wrapper = ViewWrapper(resolution=DEFAULT_WRAPPER_RESOLUTION)

        # compute solar positions for obs points
        location_lat_lon = cls.get_lat_lon_site_location(entity_info=entity_info)
        azimuths, altitudes, solar_zenith_luminances = zip(
            *[
                get_solar_parameters_from_wgs84(
                    longitude=location_lat_lon.x,
                    latitude=location_lat_lon.y,
                    date=date,
                )
                for date in datetimes
            ]
        )

        # observation points
        obs_points_by_unit = cls.get_obs_points_by_area(
            entity_info=entity_info,
            grid_resolution=grid_resolution,
            grid_buffer=grid_buffer,
            obs_height=obs_height,
            simulation_version=simulation_version,
        )
        for _, obs_points_by_area in sorted(obs_points_by_unit.items()):
            for _, obs_points in sorted(obs_points_by_area.items()):
                for obs_point in obs_points:
                    wrapper.add_observation_point(
                        obs_point,
                        solar_pos=list(zip(azimuths, altitudes)),
                        solar_zenith_luminance=solar_zenith_luminances,
                    )

        # layout triangles
        for _, triangles in cls.get_site_triangles(
            entity_info=entity_info, simulation_version=simulation_version
        ):
            wrapper.add_triangles(triangles, group="site")

        # surroundings
        for triangle_chunk in chunker(
            cls.get_surrounding_triangles(
                entity_info=entity_info, simulation_version=simulation_version
            ),
            size_of_chunk=100 * 1000,
        ):
            triangles_by_group = defaultdict(list)
            for surroundings_type, triangle in triangle_chunk:
                triangles_by_group[surroundings_type.name].append(triangle)

            for group, triangles in triangles_by_group.items():
                # NOTE: in LV95 +x=east, +y=north - in the wrapper its the other
                #       way around, so we are swapping the coordinates here.
                triangle_array = np.array(triangles)
                triangle_array[:, :, [0, 1]] = triangle_array[:, :, [1, 0]]
                wrapper.add_triangles(triangle_array, group=group)

        return wrapper.generate_input(
            run_volume=True, run_area=True, run_sun=True, use_sun_v2=cls.use_sun_v2()
        )

    @classmethod
    def get_quavis_results(
        cls,
        entity_info: dict,
        quavis_input: dict,
        quavis_output: dict,
        grid_resolution: float,
        grid_buffer: float,
        obs_height: float,
        datetimes: list[datetime],
        simulation_version: SIMULATION_VERSION,
    ) -> dict:
        """Returns
        {
            "<unit_id>": {
                "<area_id>": {
                        "type": AreaType.whatever,
                        "observation_points": [...],
                        "grounds": [...],
                        "mountains": [...]
                    }
                }
        }
        """
        dimensions_mapping = (
            SurroundingTypeToView2Dimension
            if simulation_version
            in {SIMULATION_VERSION.EXPERIMENTAL, SIMULATION_VERSION.PH_2022_H1}
            else SurroundingTypeToViewDimension
        )

        wrapper = ViewWrapper.load_wrapper_from_input_no_geometries(
            input_data=quavis_input
        )
        quavis_results = wrapper.parse_quavis_output(output_data=quavis_output)

        obs_point_index = 0
        obs_points_by_unit = cls.get_obs_points_by_area(
            entity_info=entity_info,
            grid_resolution=grid_resolution,
            grid_buffer=grid_buffer,
            obs_height=obs_height,
            simulation_version=simulation_version,
        )

        site_results: DefaultDict[
            Union[int, str], dict[Union[int, str], DefaultDict[str, list]]
        ] = defaultdict(dict)
        for unit_id, obs_points_by_area in sorted(obs_points_by_unit.items()):
            for area_db_id, obs_points in sorted(obs_points_by_area.items()):
                site_results[unit_id][area_db_id] = defaultdict(list)
                for i, obs_point in enumerate(obs_points):
                    obs_point_quavis = quavis_results[obs_point_index + i]
                    if (
                        np.linalg.norm(obs_point_quavis["position"] - obs_point)
                        > grid_resolution * 1e-3
                    ):
                        raise QuavisSimulationException(
                            "Observation point calculated before the quavis execution "
                            "doesn't match with the observation point afterwards:"
                            f"Quavis: {obs_point_quavis['position']}. Now: {obs_point}. "
                            f"Area id: {area_db_id} of unit {unit_id}"
                        )

                    site_results[unit_id][area_db_id]["observation_points"].append(
                        obs_point_quavis["position"]
                    )

                    obs_point_result = cls._get_results_of_obs_point(
                        obs_point_quavis,
                        datetimes=datetimes,
                        dimensions_mapping=dimensions_mapping,
                    )
                    for dimension, value in obs_point_result.items():
                        site_results[unit_id][area_db_id][dimension].append(value)

                obs_point_index += len(obs_points)

        return site_results

    @classmethod
    def _get_results_of_obs_point(
        cls,
        obs_point_result: dict,
        datetimes: list,
        dimensions_mapping: dict[str, str],
    ) -> dict:
        values = defaultdict(int)

        # SUN
        for idx, v in enumerate(obs_point_result["simulations"]["sun"]):
            key = "sun-" + str(datetimes[idx])
            values[key] = v

        # VIEW
        view_sim_values: dict = obs_point_result["simulations"]["area_by_group"]
        renamed_fields = set(dimensions_mapping.keys())
        computed_fields = set(view_sim_values.keys())
        for key in computed_fields.union(renamed_fields):
            normalized_name = dimensions_mapping.get(key, key)
            values[normalized_name] += view_sim_values.get(key, 0)

        values["isovist"] = obs_point_result["simulations"]["volume"]
        values["sky"] = 4 * np.pi - obs_point_result["simulations"]["area"]

        return values
