import hashlib
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, DefaultDict, Iterator, Union

from shapely import wkt
from shapely.geometry import MultiPolygon, Point, Polygon

from brooks.util.geometry_ops import get_polygons
from brooks.util.projections import project_geometry
from brooks.utils import get_floor_height
from common_utils.constants import (
    DEFAULT_OBSERVATION_HEIGHT,
    DEFAULT_SUN_TIMES,
    DEFAULT_SUN_V2_OBSERVATION_HEIGHT,
    GOOGLE_CLOUD_VIEW_SURROUNDINGS,
    IMMO_RESPONSE_PRECISION,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
)
from common_utils.exceptions import MissingTargetPotentialException
from common_utils.utils import get_view_dimension
from simulations.suntimes.suntimes_handler import SuntimesHandler
from surroundings.base_building_handler import Building
from surroundings.surrounding_handler import generate_view_surroundings
from surroundings.utils import SurrTrianglesType


class PotentialSimulationHandler:
    @classmethod
    def get_surroundings_path(
        cls,
        region: REGION,
        source_surr: SURROUNDING_SOURCES,
        simulation_version: SIMULATION_VERSION,
        building_footprint_wkt: str,
    ) -> Path:
        to_hash = f"{region.name}-{source_surr.name}-{simulation_version.name}-{building_footprint_wkt}"
        return Path(hashlib.sha256(to_hash.encode("utf-8")).hexdigest()).with_suffix(
            ".zip"
        )

    @classmethod
    def download_view_surroundings(
        cls, simulation_info: dict
    ) -> Iterator[SurrTrianglesType]:
        from surroundings.surrounding_handler import SurroundingStorageHandler

        remote_path = cls.get_surroundings_path(
            region=REGION[simulation_info["region"]],
            source_surr=SURROUNDING_SOURCES[simulation_info["source_surr"]],
            simulation_version=SIMULATION_VERSION[
                simulation_info["simulation_version"]
            ],
            building_footprint_wkt=simulation_info["building_footprint"],
        ).name
        yield from SurroundingStorageHandler.read_from_cloud(
            remote_path=GOOGLE_CLOUD_VIEW_SURROUNDINGS.joinpath(remote_path)
        )

    @classmethod
    def upload_view_surroundings(cls, triangles, path: Path):
        from surroundings.surrounding_handler import SurroundingStorageHandler

        SurroundingStorageHandler.upload(triangles=triangles, remote_path=path)

    @classmethod
    def generate_view_surroundings(
        cls,
        region: REGION,
        source_surr: SURROUNDING_SOURCES,
        simulation_version: SIMULATION_VERSION,
        building_footprint_lat_lon: MultiPolygon,
    ) -> Iterator[SurrTrianglesType]:
        building_footprint = project_geometry(
            geometry=building_footprint_lat_lon,
            crs_from=REGION.LAT_LON,
            crs_to=region,
        )

        return generate_view_surroundings(
            region=region,
            location=building_footprint.centroid,
            building_footprints=[building_footprint],
            simulation_version=simulation_version,
            surroundings_source=source_surr,
        )

    @staticmethod
    def get_building_floor_count_estimation(
        target_building_footprint: Union[Polygon, MultiPolygon],
        buildings: list[Building],
    ) -> int:
        target_footprints = filter(
            lambda building: building.footprint.intersects(target_building_footprint),
            buildings,
        )
        max_z = -math.inf
        min_z = math.inf
        for target_footprint in target_footprints:
            for pol in get_polygons(target_footprint.geometry):
                z_values = [x[2] for x in pol.exterior.coords]
                max_z = max(*z_values, max_z)
                min_z = min(*z_values, min_z)
        if max_z == -math.inf or min_z == math.inf:
            msg = f"Cant get building num floors as there is no building at {target_building_footprint.centroid.xy}"
            raise MissingTargetPotentialException(msg)
        altitude = max_z - min_z
        return math.ceil(altitude / get_floor_height())

    @staticmethod
    def get_lat_lon_location(simulation: dict) -> Point:
        return wkt.loads(simulation["building_footprint"]).centroid

    @classmethod
    def get_obs_times_height_dimensions_for_sim(
        cls,
        simulation: dict,
    ) -> tuple[list[str], float, list[datetime]]:
        if simulation["type"] == SIMULATION_TYPE.VIEW.value:
            obs_times = DEFAULT_SUN_TIMES
            obs_height = DEFAULT_OBSERVATION_HEIGHT
            dimensions = [
                vd.value
                for vd in get_view_dimension(
                    simulation_version=SIMULATION_VERSION(
                        simulation["simulation_version"]
                    )
                )
            ]
        else:  # SIMULATION_TYPE.SUN
            location = cls.get_lat_lon_location(simulation=simulation)
            obs_times = list(
                SuntimesHandler.get_sun_obs_times_from_wgs84(
                    lat=location.y, lon=location.x
                )
            )
            obs_height = DEFAULT_SUN_V2_OBSERVATION_HEIGHT
            dimensions = [f"sun-{obs_time}" for obs_time in obs_times]
        return dimensions, obs_height, obs_times

    @staticmethod
    def format_view_sun_raw_results(
        view_sun_raw_results: dict[str, dict[str, dict[str, Any]]],
        dimensions: list[str],
        simulation_region: REGION,
    ) -> DefaultDict[str, list[Union[float, dict]]]:
        """Formats view sun simulation raw results to this format:
        {
        'observation_points':[
            {
              "lat": 46.943793817019845,
              "lon": 7.450520032621462,
              "height: 135.5
            },
            ...
         ],
        'dimension1':[
                5,
                6,
                7,
                ...
            ],
         ...
        }

        From a source data like:
        {
            "<unit_id>": {
                "<area_id>": {
                        "observation_points": [...],
                        "grounds": [...],
                        "mountains": [...]
                    }
                }
        }

        If the simulation was executed on multiple apartments, the results are merged
        together.
        """
        dimension_results: DefaultDict[str, list[Union[float, dict]]] = defaultdict(
            list
        )

        for values_by_area_id in view_sun_raw_results.values():
            for area_values in values_by_area_id.values():
                for observation_point in area_values["observation_points"]:
                    north, east, height = observation_point
                    point = project_geometry(
                        crs_from=simulation_region,
                        crs_to=REGION.LAT_LON,
                        geometry=Point(east, north),
                    )
                    dimension_results["observation_points"].append(
                        {"lat": point.y, "lon": point.x, "height": height}
                    )
                for dimension in dimensions:
                    if dimension in area_values:
                        dimension_results[dimension] += [
                            round(v, IMMO_RESPONSE_PRECISION)
                            for v in area_values[dimension]
                        ]
                    else:
                        dimension_results[dimension] += [
                            0.0 for _ in range(len(area_values["observation_points"]))
                        ]

        return dimension_results
