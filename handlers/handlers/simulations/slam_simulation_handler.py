from collections import defaultdict
from typing import Optional

from pygeos import Geometry, get_x, get_y, get_z
from shapely.geometry import Point

from brooks.models import SimLayout
from brooks.util.projections import pygeos_project
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    REGION,
    SIMULATION_VERSION,
    TASK_TYPE,
    VIEW_DIMENSION,
    VIEW_DIMENSION_2,
)
from common_utils.exceptions import DBNotFoundException, SimulationNotSuccessException
from common_utils.typing import SimulationResults
from connectors.db_connector import get_db_session_scope
from handlers import FloorHandler
from handlers.db import (
    SiteDBHandler,
    SlamSimulationDBHandler,
    UnitDBHandler,
    UnitSimulationDBHandler,
)
from handlers.db.utils import retry_on_db_operational_error


class SlamSimulationHandler:
    @staticmethod
    def _raise_if_not_success(simulation: dict):
        if simulation["state"] != ADMIN_SIM_STATUS.SUCCESS.name:
            raise SimulationNotSuccessException(
                f"{simulation['type']} simulation must be in {ADMIN_SIM_STATUS.SUCCESS.name} state. "
                f"Current state: {simulation['state']}"
            )

    @classmethod
    def register_simulation(
        cls,
        site_id: int,
        run_id: str,
        task_type: TASK_TYPE,
        state: ADMIN_SIM_STATUS = ADMIN_SIM_STATUS.PENDING,
    ) -> dict:
        return SlamSimulationDBHandler.add(
            site_id=site_id,
            run_id=run_id,
            type=task_type.name,
            state=state.name,
        )

    @classmethod
    def update_state(cls, run_id: str, state: ADMIN_SIM_STATUS, errors: dict = None):
        return SlamSimulationDBHandler.update(
            item_pks={"run_id": run_id},
            new_values={"state": state.value, "errors": errors},
        )

    @classmethod
    @retry_on_db_operational_error()
    def store_results(cls, run_id: str, results: SimulationResults):
        with get_db_session_scope():
            UnitSimulationDBHandler.bulk_insert(
                items=[
                    dict(run_id=run_id, unit_id=unit_id, results=unit_results)
                    for unit_id, unit_results in results.items()
                ]
            )
            task_type = SlamSimulationDBHandler.get_by(
                run_id=run_id, output_columns=["type"]
            )["type"]
            if TASK_TYPE(task_type) in [
                TASK_TYPE.VIEW_SUN,
                TASK_TYPE.SUN_V2,
                TASK_TYPE.NOISE,
                TASK_TYPE.NOISE_WINDOWS,
                TASK_TYPE.CONNECTIVITY,
            ]:
                from handlers import StatsHandler

                StatsHandler(run_id=run_id, results=results).compute_and_store_stats()

    @classmethod
    def get_results(
        cls, unit_id: int, site_id: int, task_type: TASK_TYPE, check_status: bool = True
    ) -> dict:
        simulation = cls.get_simulation(site_id=site_id, task_type=task_type)
        if check_status:
            cls._raise_if_not_success(simulation=simulation)
        return UnitSimulationDBHandler.get_by(
            unit_id=unit_id,
            run_id=simulation["run_id"],
        )["results"]

    @classmethod
    def get_all_results(
        cls, site_id: int, task_type: TASK_TYPE, check_status: bool = True
    ) -> list[dict]:
        simulation = cls.get_simulation(site_id=site_id, task_type=task_type)
        if check_status:
            cls._raise_if_not_success(simulation=simulation)
        return UnitSimulationDBHandler.find(run_id=simulation["run_id"])

    @staticmethod
    def get_latest_results(
        site_id: int, task_type: TASK_TYPE, success_only: bool = True
    ) -> dict:
        run_id = SlamSimulationDBHandler.get_latest_run_id(
            site_id=site_id,
            task_type=task_type,
            state=ADMIN_SIM_STATUS.SUCCESS if success_only else None,
        )
        return {
            u["unit_id"]: u["results"]
            for u in UnitSimulationDBHandler.find(run_id=run_id)
        }

    @classmethod
    def get_simulation(cls, site_id: int, task_type: TASK_TYPE) -> dict:
        return SlamSimulationDBHandler.get_by(
            run_id=SlamSimulationDBHandler.get_latest_run_id(
                site_id=site_id, task_type=task_type
            ),
        )

    @classmethod
    def view_sun_v2_format(
        cls, view_sun_result, unit_id
    ) -> dict[str, dict[str, list[float]]]:
        site_id = UnitDBHandler.get_by(id=unit_id, output_columns=["site_id"])[
            "site_id"
        ]
        try:
            sun_v2 = cls.get_results(
                unit_id=unit_id, task_type=TASK_TYPE.SUN_V2, site_id=site_id
            )
        except DBNotFoundException:
            return view_sun_result

        for area_id, dimensions in sun_v2.items():
            # delete old sun observations
            for sun_v1_dim in [
                d for d in view_sun_result[area_id].keys() if d.startswith("sun-")
            ]:
                del view_sun_result[area_id][sun_v1_dim]
            # add sun_v2 dimensions
            for sun_v2_dim, observations in (
                (d, o) for d, o in dimensions.items() if d.startswith("sun-")
            ):
                view_sun_result[area_id][sun_v2_dim] = observations

        return view_sun_result

    @staticmethod
    def _ungeoreferenced_obs_points(floor_id: int, raw_results: dict) -> dict:
        georef_transformation = FloorHandler.get_georeferencing_transformation(
            floor_id=floor_id
        )
        raw_results["observation_points"] = georef_transformation.invert(
            raw_results["observation_points"]
        ).tolist()
        return raw_results

    @staticmethod
    def _format_results(raw_results: dict, flattened: Optional[bool] = True) -> dict:
        # HACK: Because we want to be able to access _old_ view results which were only stored by
        #       unit and not by area_id, we have to aggregate them for new ones
        if flattened and "observation_points" not in raw_results:
            # new raw_results of format {<area_id>: {"observation_points": [...]}, }
            results = defaultdict(list)
            for area_results in raw_results.values():
                for dimension, values in area_results.items():
                    results[dimension].extend(values)
            return results
        # old raw_results aggregated over the whole unit of format {"observation_points": [...]}
        return raw_results

    @classmethod
    def get_simulation_results_formatted(
        cls,
        unit_id: int,
        simulation_type: TASK_TYPE,
        georeferenced: Optional[bool] = True,
        project: bool = True,
    ) -> dict:
        site_id = UnitDBHandler.get_by(id=unit_id, output_columns=["site_id"])[
            "site_id"
        ]
        raw_results = cls.get_results(
            unit_id=unit_id, site_id=site_id, task_type=simulation_type
        )

        if simulation_type == TASK_TYPE.VIEW_SUN:
            raw_results = cls.view_sun_v2_format(
                view_sun_result=raw_results, unit_id=unit_id
            )

        resolution = raw_results.pop("resolution", None)
        results = cls._format_results(raw_results=raw_results, flattened=True)

        site_info = SiteDBHandler.get_by(
            id=site_id,
            output_columns=["georef_region", "simulation_version"],
        )
        if not georeferenced:
            unit_floor_id = UnitDBHandler.get_by(
                id=unit_id, output_columns=["floor_id"]
            )["floor_id"]
            results = cls._ungeoreferenced_obs_points(
                floor_id=unit_floor_id, raw_results=results
            )
        else:  # We convert to latlon
            georef_region = site_info["georef_region"]

            if project:
                pygeos_geometries = [
                    Geometry(f"POINT ({p[1]} {p[0]} {p[2]})")
                    for p in results["observation_points"]
                ]
                transformed_pygeos = pygeos_project(
                    geometries=pygeos_geometries,
                    crs_from=REGION[georef_region],
                    crs_to=REGION.LAT_LON,
                )
                results["observation_points"] = []
                for x, y, z in zip(
                    get_x(transformed_pygeos),
                    get_y(transformed_pygeos),
                    get_z(transformed_pygeos),
                ):
                    results["observation_points"].append([x, y, z])

        if resolution:
            results["resolution"] = resolution

        if (
            simulation_type == TASK_TYPE.VIEW_SUN
            and site_info["simulation_version"] == SIMULATION_VERSION.PH_2022_H1.value
        ):
            # We add streets as an extra dimension, aggregating all the streets dimensions
            street_values = [
                results[key.value]
                for key in (
                    VIEW_DIMENSION_2.VIEW_TERTIARY_STREETS,
                    VIEW_DIMENSION_2.VIEW_SECONDARY_STREETS,
                    VIEW_DIMENSION_2.VIEW_PRIMARY_STREETS,
                    VIEW_DIMENSION_2.VIEW_HIGHWAYS,
                    VIEW_DIMENSION_2.VIEW_PEDESTRIAN,
                )
            ]
            results[VIEW_DIMENSION.VIEW_STREETS.value] = [
                sum(x) for x in zip(*street_values)
            ]
        return dict(results)

    @staticmethod
    def format_results_by_area(
        obs_points: list[tuple[float, float, float]],
        simulation_results: dict[str, list[float]],
        unit_layout: SimLayout,
    ) -> dict:
        """
        Returns: dictionary per area_id containing a dict with:
          observation_points: a list with x,y,z of each obs point
          dimensions: one entry per 'dimension' containing a list of the same size of obs points
                      with a float value of that particular dimension for that obs point
        """
        footprint_by_area_id = {
            area.db_area_id: area.footprint for area in unit_layout.areas
        }

        area_results: dict[
            int | str,
            dict[str, list[tuple[float, float, float] | float]],
        ] = defaultdict(lambda: defaultdict(list))
        for i, (y, x, z) in enumerate(obs_points):
            for area_id, footprint in footprint_by_area_id.items():
                if footprint.contains(Point(x, y)):
                    area_results[area_id]["observation_points"].append((y, x, z))
                    for sim_dimension, results in simulation_results.items():
                        area_results[area_id][sim_dimension].append(results[i])
        return area_results
