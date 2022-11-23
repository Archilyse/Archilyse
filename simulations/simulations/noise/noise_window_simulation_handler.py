from collections import defaultdict
from functools import cached_property
from typing import Dict, List, Set, Tuple

from shapely.geometry import Point

from brooks.utils import get_floor_height
from common_utils.constants import (
    NOISE_SOURCE_TYPE,
    NOISE_SURROUNDING_TYPE,
    NOISE_TIME_TYPE,
    REGION,
    SIMULATION_VERSION,
)
from common_utils.typing import (
    AreaID,
    Distance,
    FloorNumber,
    LocationTuple,
    NoiseAreaResultsType,
    PLanID,
    UnitID,
)
from handlers import PlanHandler, PlanLayoutHandler, SiteHandler
from handlers.db import FloorDBHandler, SiteDBHandler, UnitAreaDBHandler, UnitDBHandler
from simulations.noise import NoiseBlockingElementsHandler, NoiseRayTracerSimulator
from simulations.noise.noise_sources_levels_generator import get_noise_sources
from simulations.noise.utils import (
    get_noise_surrounding_type,
    get_surrounding_footprints,
    sample_locations_by_area,
)
from surroundings.constants import BOUNDING_BOX_EXTENSION_NOISE


class NoiseWindowSimulationHandler:
    DEFAULT_ISOLATION_FACTOR = 1.0

    def __init__(self, site_id: int):
        self.site_id = site_id

    @cached_property
    def site_plans(self):
        return PlanHandler.get_site_plans_layouts_with_building_floor_numbers(
            site_id=self.site_id
        )

    @cached_property
    def __common_args(self) -> dict:
        site_info = SiteDBHandler.get_by(id=self.site_id)
        return dict(
            site_id=self.site_id,
            location=SiteHandler.get_projected_location(site_info=site_info),
            region=REGION[site_info["georef_region"]],
            bounding_box_extension=BOUNDING_BOX_EXTENSION_NOISE,
            simulation_version=SIMULATION_VERSION[site_info["simulation_version"]],
        )

    @cached_property
    def blocking_elements_handler(self) -> NoiseBlockingElementsHandler:
        return NoiseBlockingElementsHandler(
            site_plans=self.site_plans,
            site_surroundings=get_surrounding_footprints(**self.__common_args),
        )

    @cached_property
    def noise_simulators(self) -> Dict[NOISE_SOURCE_TYPE, NoiseRayTracerSimulator]:
        return {
            noise_type: NoiseRayTracerSimulator(
                noise_sources=list(
                    get_noise_sources(
                        **self.__common_args, noise_source_type=noise_type
                    )
                )
            )
            for noise_type in NOISE_SOURCE_TYPE
        }

    def _get_plan_layout_handler(self, plan_id: int) -> PlanLayoutHandler:
        for plan_info in self.site_plans:
            if plan_info["id"] == plan_id:
                return plan_info["plan_layout_handler"]
        raise ValueError(f"Plan {plan_id} not found")

    @staticmethod
    def get_locations_by_area(
        layout_handler: PlanLayoutHandler,
    ) -> Dict[int, List[LocationTuple]]:
        plan_layout = layout_handler.get_layout(
            classified=True, georeferenced=True, scaled=True
        )
        private_layout = layout_handler.get_private_layout(
            scaled=True, georeferenced=True
        )

        locations_by_area = sample_locations_by_area(
            plan_layout=plan_layout, target_layout=private_layout
        )

        return locations_by_area

    def get_noise_for_site(
        self,
    ) -> Dict[UnitID, Dict[AreaID, NoiseAreaResultsType]]:
        units_areas_by_plan_floor_number = self._get_entities()

        site_results = {}

        for (
            plan_id,
            units_areas_by_floor_number,
        ) in units_areas_by_plan_floor_number.items():
            layout_handler = self._get_plan_layout_handler(plan_id=plan_id)
            plan_floor_height = get_floor_height(
                default=layout_handler.get_layout(
                    scaled=True, raise_on_inconsistency=False
                ).default_element_heights
            )

            loc_by_area = self.get_locations_by_area(layout_handler=layout_handler)

            noises_by_location = self.get_2d_noises_for_plan(
                locations={p for points in loc_by_area.values() for p in points},
                plan_id=plan_id,
            )

            for floor_number, unit_areas in units_areas_by_floor_number.items():
                # Todo floor height should really consider the real height of floors below
                floor_height = plan_floor_height * floor_number
                real_noise_by_location = self.get_real_floor_noise(
                    floor_height=floor_height,
                    noises_by_location=noises_by_location,
                )
                for unit_id, areas in unit_areas.items():
                    site_results[unit_id] = self.get_noise_for_unit(
                        floor_height=floor_height,
                        locations_by_area=loc_by_area,
                        real_noise_by_location=real_noise_by_location,
                        unit_areas_ids=areas,
                    )
        return site_results

    def _get_entities(
        self,
    ) -> Dict[PLanID, Dict[FloorNumber, Dict[UnitID, List[AreaID]]]]:
        units = {
            u["id"]: u
            for u in UnitDBHandler.find(
                site_id=self.site_id,
                output_columns=["id", "plan_id", "floor_id"],
            )
        }
        floor_number_by_id = {
            f["id"]: f["floor_number"]
            for f in FloorDBHandler.find_in(
                id={u["floor_id"] for u in units.values()},
                output_columns=["id", "floor_number"],
            )
        }
        unit_areas = UnitAreaDBHandler.find_in(
            unit_id=set(units.keys()),
            output_columns=["unit_id", "area_id"],
        )

        units_areas_by_plan_floor_number: Dict[
            PLanID, Dict[FloorNumber, Dict[UnitID, List[AreaID]]]
        ] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for unit_area in unit_areas:
            unit = units[unit_area["unit_id"]]
            floor_number = floor_number_by_id[unit["floor_id"]]
            plan_id = unit["plan_id"]
            units_areas_by_plan_floor_number[plan_id][floor_number][unit["id"]].append(
                unit_area["area_id"]
            )
        return dict(units_areas_by_plan_floor_number)

    @staticmethod
    def get_noise_for_unit(
        floor_height: float,
        locations_by_area: Dict[AreaID, List[LocationTuple]],
        real_noise_by_location: Dict[
            NOISE_SURROUNDING_TYPE, Dict[LocationTuple, float]
        ],
        unit_areas_ids: List[int],
    ) -> Dict[AreaID, NoiseAreaResultsType]:
        unit_result: Dict[AreaID, NoiseAreaResultsType] = {}
        for db_area_id in unit_areas_ids:
            if area_obs_points := locations_by_area.get(db_area_id):
                real_locations = [
                    (loc[0], loc[1], loc[2] + floor_height) for loc in area_obs_points
                ]
                unit_result[db_area_id] = {"observation_points": real_locations}
                for (noise_type, locations_noise) in real_noise_by_location.items():
                    area_noise_values = [
                        locations_noise[obs_point] for obs_point in area_obs_points
                    ]
                    unit_result[db_area_id][noise_type.value] = area_noise_values  # type: ignore
        return unit_result

    @staticmethod
    def get_real_floor_noise(
        floor_height: float,
        noises_by_location: Dict[
            NOISE_SOURCE_TYPE,
            Dict[LocationTuple, List[Tuple[Dict[NOISE_TIME_TYPE, float], Distance]]],
        ],
    ) -> Dict[NOISE_SURROUNDING_TYPE, Dict[LocationTuple, float]]:
        # noise_name ->  obs_point -> real_noise_value
        real_noise_by_location = {}
        for noise_source_type, location_noises in noises_by_location.items():
            for noise_time_type in NOISE_TIME_TYPE:
                noise_type = get_noise_surrounding_type(
                    noise_source=noise_source_type, noise_time=noise_time_type
                )
                real_noise_by_location[noise_type] = {
                    location: NoiseRayTracerSimulator.calculate_noise_3d(
                        noises=noises,
                        height=floor_height + location[2],
                        noise_time=noise_time_type,
                    )
                    for location, noises in location_noises.items()
                }
        return real_noise_by_location

    def get_2d_noises_for_plan(
        self, locations: Set[LocationTuple], plan_id: int
    ) -> Dict[
        NOISE_SOURCE_TYPE,
        Dict[LocationTuple, List[Tuple[Dict[NOISE_TIME_TYPE, float], Distance]]],
    ]:
        # noise_name ->  obs_point -> [noise_values, distance]
        # where noise_values is a dict of noise levels by NOISE_TIME_TYPE
        noises_by_location = {}
        for noise_type in NOISE_SOURCE_TYPE:
            # We calculate noise for each plan
            noises_by_location[noise_type] = self._get_noises_and_2d_distances(
                noise_type=noise_type, plan_id=plan_id, locations=locations
            )
        return noises_by_location

    def _get_noises_and_2d_distances(
        self,
        noise_type: NOISE_SOURCE_TYPE,
        plan_id: int,
        locations: Set[LocationTuple],
    ) -> Dict[LocationTuple, List[Tuple[Dict[NOISE_TIME_TYPE, float], Distance]]]:
        blocking_elements = (
            self.blocking_elements_handler.get_blocking_elements_by_plan_id(plan_id)
        )
        return {
            location: self.noise_simulators[noise_type].get_noises_2d_distances_at(
                location=Point(location[:2]),
                blocking_elements=blocking_elements,
            )
            for location in locations
        }
