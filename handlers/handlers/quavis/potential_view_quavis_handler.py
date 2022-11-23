from typing import Iterator

import numpy as np
from shapely import wkt
from shapely.geometry import MultiPolygon, Point, Polygon

from brooks.models.layout import PotentialLayoutWithWindows, SimLayout
from brooks.util.projections import project_geometry
from brooks.utils import get_default_element_height
from common_utils.constants import POTENTIAL_LAYOUT_MODE, REGION, SIMULATION_VERSION
from common_utils.exceptions import BaseSlamException
from handlers import PotentialSimulationHandler
from handlers.quavis.quavis_handler import QuavisHandler
from simulations.view.meshes import GeoreferencingTransformation
from simulations.view.meshes.observation_points import get_observation_points_by_area
from simulations.view.meshes.triangulation3d import TRIANGULATOR_BY_SIMULATION_VERSION
from surroundings.utils import SurrTrianglesType


class PotentialViewQuavisHandler(QuavisHandler):
    @classmethod
    def use_sun_v2(cls) -> bool:
        return True

    @classmethod
    def get_lat_lon_site_location(cls, entity_info: dict) -> Point:
        return PotentialSimulationHandler.get_lat_lon_location(simulation=entity_info)

    @classmethod
    def get_site_triangles(
        cls, entity_info: dict, simulation_version: SIMULATION_VERSION
    ) -> list[tuple[int, list[np.ndarray]]]:
        elevation, layout = cls._get_layout_and_elevation(
            simulation_info=entity_info, simulation_version=simulation_version
        )
        layout_triangulator = TRIANGULATOR_BY_SIMULATION_VERSION[
            simulation_version.name
        ](
            layout=layout,
            georeferencing_parameters=cls._get_georeferencing_transformation(
                elevation=elevation
            ),
        )

        return [
            (
                entity_info["id"],
                layout_triangulator.create_layout_triangles(
                    layouts_upper_floor=[],
                    level_baseline=cls._get_level_baseline(layout=layout),
                ),
            )
        ]

    @classmethod
    def _get_layout_and_elevation(
        cls, simulation_version: SIMULATION_VERSION, simulation_info: dict
    ) -> tuple[float, SimLayout]:
        region = REGION[simulation_info["region"]]

        projected_building = project_geometry(
            geometry=wkt.loads(simulation_info["building_footprint"]),
            crs_from=REGION.LAT_LON,
            crs_to=region,
        )
        elevation = cls._get_elevation(
            region=region,
            projected_building=projected_building,
            simulation_version=simulation_version,
        )
        layout = cls._get_layout(
            building_footprint=projected_building,
            floor_number=simulation_info["floor_number"],
            layout_mode=POTENTIAL_LAYOUT_MODE[simulation_info["layout_mode"]],
        )

        return elevation, layout

    @classmethod
    def _get_level_baseline(cls, layout: SimLayout):
        return (
            get_default_element_height("GENERIC_SPACE_HEIGHT")
            + get_default_element_height("CEILING_SLAB")
        ) * layout.floor_number

    @classmethod
    def get_surrounding_triangles(
        cls, entity_info: dict, simulation_version: SIMULATION_VERSION
    ) -> Iterator[SurrTrianglesType]:
        yield from PotentialSimulationHandler.download_view_surroundings(
            simulation_info=entity_info
        )

    @classmethod
    def get_obs_points_by_area(
        cls,
        entity_info: dict,
        grid_resolution: float,
        grid_buffer: float,
        obs_height: float,
        simulation_version: SIMULATION_VERSION,
    ) -> dict[int, dict[str, np.ndarray]]:
        elevation, layout = cls._get_layout_and_elevation(
            simulation_info=entity_info, simulation_version=simulation_version
        )

        obs_points_by_area = get_observation_points_by_area(
            areas=layout.areas,
            level_baseline=cls._get_level_baseline(layout=layout),
            georeferencing_parameters=cls._get_georeferencing_transformation(elevation),
            resolution=grid_resolution,
            buffer=grid_buffer,
            obs_height=obs_height,
        )
        # Takes the SimArea and converts it to a string that is possible to sort
        obs_points_by_area_sortable: dict[str, np.ndarray] = {
            f"{area.footprint.area}_{area.footprint.centroid.xy}": obs_points
            for area, obs_points in obs_points_by_area
        }

        return {entity_info["id"]: obs_points_by_area_sortable}

    @classmethod
    def _get_layout(
        cls,
        building_footprint: Polygon,
        floor_number: int,
        layout_mode: POTENTIAL_LAYOUT_MODE,
    ) -> SimLayout:
        if layout_mode == POTENTIAL_LAYOUT_MODE.WITH_WINDOWS:
            return PotentialLayoutWithWindows(
                footprint=building_footprint, floor_number=floor_number
            )
        else:
            raise BaseSlamException("Unsupported layout mode.")

    @classmethod
    def _get_georeferencing_transformation(
        cls, elevation
    ) -> GeoreferencingTransformation:
        georeferencing_parameters = GeoreferencingTransformation()
        georeferencing_parameters.set_translation(0, 0, elevation)
        georeferencing_parameters.set_swap_dimensions(0, 1)

        return georeferencing_parameters

    @classmethod
    def _get_elevation(
        cls,
        projected_building: MultiPolygon,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
    ):
        from surroundings.base_elevation_handler import get_elevation_handler

        elevation_handler = get_elevation_handler(
            region=region,
            location=projected_building.centroid,
            simulation_version=simulation_version,
        )

        return elevation_handler.get_elevation(point=projected_building.centroid)
