import math
from collections import Counter, defaultdict, namedtuple
from typing import Callable, Collection, Iterator, Optional, Union

import numpy as np
from deepdiff import DeepDiff
from shapely.geometry import LineString, Polygon
from shapely.ops import split

from brooks import SpaceConnector
from brooks.classifications import CLASSIFICATIONS, BaseClassificationScheme
from brooks.models import SimArea, SimLayout, SimSpace
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType, SIACategory
from common_utils.competition_constants import (
    COMPETITION_SIZES_MARGIN,
    MINIMUM_CORRIDOR_WIDTHS,
    SERVICE_ROOM_TYPES,
    CompetitionFeatures,
)
from common_utils.constants import (
    NOISE_SURROUNDING_TYPE,
    SEASONS,
    UNIT_USAGE,
    VIEW_DIMENSION,
)
from common_utils.exceptions import CompetitionFeaturesValueError
from common_utils.logger import logger
from common_utils.typing import AreaID, NoiseAreaResultsType, UnitID
from dufresne.polygon import get_sides_as_lines_by_length
from handlers.competition.utils import f_to_str
from handlers.db import FloorDBHandler
from handlers.utils import PartialUnitInfo
from simulations.basic_features import CustomValuatorBasicFeatures2
from simulations.noise.utils import aggregate_noises
from simulations.suntimes.suntimes_handler import SuntimesHandler

AreasTotal = namedtuple("AreasTotal", ("outdoor", "indoor"))


map_automated_features_view_dimension = {
    CompetitionFeatures.ANALYSIS_GREENERY: VIEW_DIMENSION.VIEW_GREENERY,
    CompetitionFeatures.ANALYSIS_WATER: VIEW_DIMENSION.VIEW_WATER,
    CompetitionFeatures.ANALYSIS_BUILDINGS: VIEW_DIMENSION.VIEW_BUILDINGS,
    CompetitionFeatures.ANALYSIS_SKY: VIEW_DIMENSION.VIEW_SKY,
    CompetitionFeatures.ANALYSIS_STREETS: VIEW_DIMENSION.VIEW_STREETS,
    CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS: VIEW_DIMENSION.VIEW_RAILWAY_TRACKS,
}


class CompetitionFeaturesCalculator:

    MIN_USABLE_SPACE_IN_PERCENT = math.pi / 4
    DIRECT_SUN_THRESHOLD_SUMMER = 20
    DIRECT_SUN_THRESHOLD_WINTER = 10

    MAX_DISTANCE_TO_WATER = 1.0
    REDUIT_WASHING_MACHINE_MIN_SIZE = 2.0
    REDUIT_WASHING_MACHINE_MIN_DIMENSION = 1.0

    JANITOR_MAX_TOILET_DISTANCE = 10.0

    SMALLER_SIDE_REQ_ELEVATOR = 1.1
    BIGGER_SIDE_REQ_ELEVATOR = 1.4

    NOISE_INSULATION_THRESHOLD = 55
    NOISE_INSULATION_AREA_TYPES = [
        AreaType.LIVING_DINING,
        AreaType.ROOM,
        AreaType.LIVING_ROOM,
        AreaType.BEDROOM,
    ]

    def __init__(self, classification_schema: BaseClassificationScheme):
        self.classification_schema = classification_schema

    def calculate_all_features(
        self,
        plans: list[dict],
        public_layouts: dict[int, SimLayout],
        units_layouts_w_info: list[tuple[PartialUnitInfo, SimLayout]],
        view_unit_area_stats: dict[int, dict[int, dict[str, dict[str, float]]]],
        noise_unit_area_stats: dict[int, dict[int, dict[str, dict[str, float]]]],
        sun_unit_area_stats: dict[int, dict[int, dict[str, dict[str, float]]]],
        noise_window_per_area: dict[UnitID, dict[AreaID, NoiseAreaResultsType]],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> dict[str, float]:
        """
        plans: A list of dicts with keys 'plan_layout' and 'floor_numbers' of full plan layout
        public_layouts: A dict of public layouts by floor_id
        units_layouts_w_info: A list of tuples of unit layouts with the unit_info (id, client_id and floor_id)
        view_unit_area_stats: A dict of view stats by unit_id, area_id and dimension
        sun_unit_area_stats: A dict of sun_v2 stats by unit_id, area_id and dimension
        """

        sun_stats_by_apartment_area: defaultdict[str, dict] = defaultdict(dict)
        apartment_db_area_ids: defaultdict[str, list[int]] = defaultdict(list)
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]] = defaultdict(
            dict
        )
        layouts_by_type: defaultdict[str, list[SimLayout]] = defaultdict(list)
        residential_units_layouts_with_id: list[tuple[UnitID, SimLayout]] = []
        janitor_layouts_by_floor: defaultdict[int, list[SimLayout]] = defaultdict(list)
        plan_layouts: list[SimLayout] = [x["plan_layout"] for x in plans]
        full_site_layouts: list[SimLayout] = []
        for plan in plans:
            for _ in plan["floor_numbers"]:
                full_site_layouts.append(plan["plan_layout"])

        for unit_info, layout in units_layouts_w_info:
            if unit_info["client_id"]:
                layouts_by_type[unit_info["unit_usage"]].append(layout)
                if unit_info["unit_usage"] == UNIT_USAGE.JANITOR.name:
                    janitor_layouts_by_floor[unit_info["floor_id"]].append(layout)
                elif unit_info["unit_usage"] == UNIT_USAGE.RESIDENTIAL.name:
                    layouts_per_apartment[unit_info["client_id"]][
                        unit_info["id"]
                    ] = layout
                    sun_stats_by_apartment_area[unit_info["client_id"]].update(
                        sun_unit_area_stats[int(unit_info["id"])]
                    )
                    apartment_db_area_ids[unit_info["client_id"]] += [
                        area.db_area_id for area in layout.areas
                    ]
                    residential_units_layouts_with_id.append((unit_info["id"], layout))

        total_bike_parkings_count = self.bike_parking_count(layouts=plan_layouts)
        residential_ratio = self.m2_by_usage_type(layouts_by_type=layouts_by_type)
        features = {
            CompetitionFeatures.RESIDENTIAL_USE.value: residential_ratio,
            CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: residential_ratio,
            CompetitionFeatures.RESIDENTIAL_TOTAL_HNF_REQ.value: self.calculate_total_hnf_area(
                layouts=full_site_layouts
            ),
            CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: self.private_outdoor_areas_percent(
                units_layouts=layouts_by_type[UNIT_USAGE.RESIDENTIAL.name]
            ),
            CompetitionFeatures.APT_PCT_W_OUTDOOR.value: self.apartments_with_outdoor_percentage(
                layouts_per_apartment=layouts_per_apartment
            ),
            CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: self.sum_specific_area_sizes_by_apt_type(
                layouts_by_apt_type=self.layouts_by_apartment_type(
                    layouts_per_apartment=layouts_per_apartment
                ),
                area_types={
                    AreaType.KITCHEN,
                    AreaType.KITCHEN_DINING,
                    AreaType.DINING,
                    AreaType.LIVING_DINING,
                },
            ),
            CompetitionFeatures.BUILDING_AVG_MAX_RECT_ALL_APT_AREAS.value: self.average_largest_rectangle_all_areas(
                max_rectangle_by_area_id=max_rectangle_by_area_id,
                units_layouts=layouts_by_type[UNIT_USAGE.RESIDENTIAL.name],
            ),
            CompetitionFeatures.APT_MAX_RECT_IN_PRIVATE_OUTDOOR.value: self.private_outdoor_spaces_spaciousness(
                max_rectangle_by_area_id=max_rectangle_by_area_id,
                units_layouts=layouts_by_type[UNIT_USAGE.RESIDENTIAL.name],
            ),
            CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: self.dinning_sizes_per_apt(
                layouts_per_apartment=layouts_per_apartment,
                max_rectangle_by_area_id=max_rectangle_by_area_id,
            ),
            CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: self.sum_specific_area_sizes_by_apt(
                layouts_per_apartment=layouts_per_apartment,
                area_types=CLASSIFICATIONS.UNIFIED.value().get_children(
                    SIACategory.ANF
                ),
            ),
            CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.value: self.avg_darkest_summer_area(
                layouts_per_apartment=layouts_per_apartment,
                sun_stats_by_apartment_area=sun_stats_by_apartment_area,
            ),
            CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER.value: self.avg_brightest_in_winter(
                layouts_per_apartment=layouts_per_apartment,
                sun_stats_by_apartment_area=sun_stats_by_apartment_area,
            ),
            CompetitionFeatures.BUILDING_PCT_CIRCULATION_RESIDENTIAL.value: (
                self.pct_circulation_over_total_residential_space(
                    units_layouts=layouts_by_type[UNIT_USAGE.RESIDENTIAL.name]
                )
            ),
            CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value: self.reduit_with_water_connection(
                apartment_db_area_ids=apartment_db_area_ids,
                plan_layouts=plan_layouts,
                max_rectangle_by_area_id=max_rectangle_by_area_id,
            ),
            CompetitionFeatures.APT_HAS_WASHING_MACHINE.value: self.check_feature_is_present_per_apt_percentage(
                layouts_per_apartment=layouts_per_apartment,
                targe_feature_type=FeatureType.WASHING_MACHINE,
            ),
            CompetitionFeatures.APT_PCT_W_STORAGE.value: self.apartment_with_storerooms_sizes(
                layouts_per_apartment=layouts_per_apartment
            ),
            CompetitionFeatures.BUILDING_BICYCLE_BOXES_AVAILABLE.value: bool(
                total_bike_parkings_count
            ),
            CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: self.apartment_types_percentage(
                layouts_per_apartment=layouts_per_apartment
            ),
            CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: self.apartment_types_area(
                layouts_per_apartment=layouts_per_apartment
            ),
            CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: self.bathrooms_features_distribution(
                layouts_per_apartment=layouts_per_apartment
            ),
            CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value: self.bathrooms_toilets_distribution(
                layouts_per_apartment=layouts_per_apartment
            ),
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: self.avg_apt_bathroom_sia500_size(
                layouts_per_apartment=layouts_per_apartment,
                max_rectangle_by_area_id=max_rectangle_by_area_id,
            ),
            CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: self.avg_apt_bedroom_minimum(
                layouts_per_apartment=layouts_per_apartment,
                max_rectangle_by_area_id=max_rectangle_by_area_id,
            ),
            # JANITOR FEATURES
            CompetitionFeatures.JANITOR_HAS_WC.value: self.any_layout_have_area_type(
                layouts=layouts_by_type[UNIT_USAGE.JANITOR.name],
                area_type=AreaType.BATHROOM,
            ),
            CompetitionFeatures.JANITOR_HAS_STORAGE.value: self.any_layout_have_area_type(
                layouts=layouts_by_type[UNIT_USAGE.JANITOR.name],
                area_type=AreaType.STOREROOM,
            ),
            CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value: self.max_area_size(
                layouts=layouts_by_type[UNIT_USAGE.JANITOR.name],
                area_types={AreaType.OFFICE, AreaType.ROOM},
            ),
            CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value: self.max_area_size(
                layouts=layouts_by_type[UNIT_USAGE.JANITOR.name],
                area_types={AreaType.STOREROOM},
            ),
            CompetitionFeatures.JANITOR_WC_CLOSENESS.value: self.janitor_wc_adjacent_or_adjoining(
                janitor_layouts=janitor_layouts_by_floor, public_layouts=public_layouts
            ),
            CompetitionFeatures.JANITOR_WATER_CONN_AVAILABLE.value: self.janitor_storerooms_water_connections_available(
                janitor_layouts=layouts_by_type[UNIT_USAGE.JANITOR.name],
                plan_layouts=plan_layouts,
            ),
            CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: total_bike_parkings_count,
            CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: self.ratio_of_navigable_spaces_area(
                plans=plans
            ),
            CompetitionFeatures.BUILDING_MINIMUM_ELEVATOR_DIMENSIONS.value: self.minimum_elevator_dimensions(
                plans=plans
            ),
            CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER.value: (
                self.avg_total_hours_of_sunshine_outside_areas(
                    plan_layouts=plan_layouts,
                    sun_stats_by_apartment_area=sun_stats_by_apartment_area,
                    season=SEASONS.WINTER,
                )
            ),
            CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER.value: (
                self.avg_total_hours_of_sunshine_outside_areas(
                    plan_layouts=plan_layouts,
                    sun_stats_by_apartment_area=sun_stats_by_apartment_area,
                    season=SEASONS.SUMMER,
                )
            ),
            CompetitionFeatures.NOISE_STRUCTURAL.value: self.avg_noise_feature(
                layouts_per_apartment=layouts_per_apartment,
                noise_unit_area_stats=noise_unit_area_stats,
            ),
            CompetitionFeatures.NOISE_INSULATED_ROOMS.value: self.noise_insulated_rooms(
                residential_units_layouts_with_id=residential_units_layouts_with_id,
                noise_window_per_area=noise_window_per_area,
            ),
            CompetitionFeatures.AGF_W_REDUIT.value: self.calculate_total_living_area(
                residential_units_layouts=layouts_by_type[UNIT_USAGE.RESIDENTIAL.name]
            ),
        }
        for (
            view_automated_feature,
            view_dimension,
        ) in map_automated_features_view_dimension.items():
            features[view_automated_feature.value] = self.avg_analysis_feature(
                dimension=view_dimension,
                layouts_per_apartment=layouts_per_apartment,
                unit_area_stats=view_unit_area_stats,
            )
        return features

    @staticmethod
    def m2_by_usage_type(
        layouts_by_type: dict[str, list[SimLayout]]
    ) -> dict[str, float]:
        distribution_m2: dict[str, float] = defaultdict(float)
        for usage, layouts in layouts_by_type.items():
            for layout in layouts:
                distribution_m2[usage] += layout.footprint.area
        return dict(distribution_m2)

    def apartment_with_storerooms_sizes(
        self, layouts_per_apartment: defaultdict[str, dict[int, SimLayout]]
    ) -> dict[str, float]:
        result = {}
        for client_id, unit_layouts in layouts_per_apartment.items():
            store_area_sizes = [
                area.footprint.area
                for layout in unit_layouts.values()
                for area_store_type in self.classification_schema.STOREROOM_AREAS
                for area in layout.areas_by_type.get(area_store_type, [])
            ]
            result[client_id] = max(store_area_sizes, default=0.0)
        return result

    def private_outdoor_areas_percent(
        self, units_layouts: Collection[SimLayout]
    ) -> float:
        """percent of total residential outdoor area vs total residential area"""
        outdoor, indoor = self._get_outdoor_indoor_areas(layouts=units_layouts)
        if total := indoor + outdoor:
            return outdoor / total
        raise CompetitionFeaturesValueError("No residential apartments found")

    def apartments_with_outdoor_percentage(
        self, layouts_per_apartment: defaultdict[str, dict[int, SimLayout]]
    ) -> float:
        """percentage of apartments that at least have some outdoor space"""
        apartments_w_outdoor = sum(
            (
                1
                for unit_layouts in layouts_per_apartment.values()
                if self._get_outdoor_indoor_areas(layouts=unit_layouts.values()).outdoor
            )
        )

        if len(layouts_per_apartment):
            return apartments_w_outdoor / len(layouts_per_apartment)
        raise CompetitionFeaturesValueError("No residential apartments found")

    def sum_specific_area_sizes_by_apt_type(
        self,
        layouts_by_apt_type: dict[str, list[list[SimLayout]]],
        area_types: set[AreaType],
    ) -> dict[str, list[float]]:
        result = defaultdict(list)
        for apt_type, individual_apt_layouts in layouts_by_apt_type.items():
            for layouts in individual_apt_layouts:
                area_sizes_sum = self.sum_area_size(
                    layouts=layouts, area_types=area_types
                )
                result[apt_type].append(area_sizes_sum)
        return result

    def sum_specific_area_sizes_by_apt(
        self,
        layouts_per_apartment: dict[str, dict[int, SimLayout]],
        area_types: set[AreaType],
    ) -> dict[str, float]:
        result = {}
        for client_id, layouts_by_id in layouts_per_apartment.items():
            area_sizes_sum = self.sum_area_size(
                layouts=list(layouts_by_id.values()), area_types=area_types
            )
            result[client_id] = area_sizes_sum
        return result

    def average_largest_rectangle_all_areas(
        self,
        units_layouts: Collection[SimLayout],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> float:
        valid_area_types: set[AreaType] = {
            AreaType.ROOM,
            AreaType.KITCHEN,
            AreaType.KITCHEN_DINING,
            AreaType.LIVING_DINING,
            AreaType.LIVING_ROOM,
            AreaType.BEDROOM,
            AreaType.BATHROOM,
            AreaType.LOGGIA,
            AreaType.BALCONY,
            AreaType.WINTERGARTEN,
        }

        return self._average_max_rectangles_in_layouts(
            valid_area_types=valid_area_types,
            units_layouts=units_layouts,
            max_rectangle_by_area_id=max_rectangle_by_area_id,
        )

    def private_outdoor_spaces_spaciousness(
        self,
        units_layouts: Collection[SimLayout],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> float:
        return self._average_max_rectangles_in_layouts(
            valid_area_types=self.classification_schema.OUTDOOR_AREAS,
            units_layouts=units_layouts,
            max_rectangle_by_area_id=max_rectangle_by_area_id,
        )

    def avg_analysis_feature(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        unit_area_stats: dict[int, dict[int, dict[str, dict[str, float]]]],
        dimension: VIEW_DIMENSION,
    ) -> float:
        return self._average_callable_room_by_sim_dimension(
            layouts_per_apartment=layouts_per_apartment,
            unit_area_stats=unit_area_stats,
            dimension=dimension.value,
            aggregation_func=np.mean,
        )

    def avg_noise_feature(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        noise_unit_area_stats: dict[int, dict[int, dict[str, dict[str, float]]]],
    ) -> float:
        total_noise = []
        for noise_type in NOISE_SURROUNDING_TYPE:
            total_noise.append(
                self._average_callable_room_by_sim_dimension(
                    layouts_per_apartment=layouts_per_apartment,
                    unit_area_stats=noise_unit_area_stats,
                    dimension=noise_type.value,
                    aggregation_func=np.mean,
                )
            )
        return float(np.mean(total_noise))

    def _avg_callable_room_by_sun_v2(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        season: SEASONS,
        sun_stats_by_apartment_area: defaultdict[str, dict],
        aggregation_func: Callable,
    ) -> float:
        aggregated_observations = {}
        for client_id, units_layouts in layouts_per_apartment.items():
            apartment_area_stats = sun_stats_by_apartment_area[client_id]
            living_bedrooms_kitchens = [
                area.db_area_id
                for layout in units_layouts.values()
                for area in layout.areas
                if area.type
                in self.classification_schema.LIVING_AND_BEDROOMS | {AreaType.KITCHEN}
            ]
            if living_bedrooms_kitchens:
                aggregated_observations[client_id] = aggregation_func(
                    (
                        stats["median"]
                        for db_area_id in living_bedrooms_kitchens
                        for dimension, stats in apartment_area_stats[db_area_id].items()
                        if SuntimesHandler.get_datetime_from_sun_key(
                            key=dimension
                        ).date()
                        == season.value.date()
                    )
                )

        if aggregated_observations:
            return sum(aggregated_observations.values()) / len(aggregated_observations)
        raise CompetitionFeaturesValueError(
            "No apartments found with living and bedrooms."
        )

    def avg_darkest_summer_area(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        sun_stats_by_apartment_area: defaultdict[str, dict],
    ):
        return self._avg_callable_room_by_sun_v2(
            layouts_per_apartment=layouts_per_apartment,
            season=SEASONS.SUMMER,
            sun_stats_by_apartment_area=sun_stats_by_apartment_area,
            aggregation_func=min,
        )

    def avg_brightest_in_winter(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        sun_stats_by_apartment_area: defaultdict[str, dict],
    ):
        return self._avg_callable_room_by_sun_v2(
            layouts_per_apartment=layouts_per_apartment,
            season=SEASONS.WINTER,
            sun_stats_by_apartment_area=sun_stats_by_apartment_area,
            aggregation_func=max,
        )

    @staticmethod
    def _average_max_rectangles_in_layouts(
        valid_area_types: set[AreaType],
        units_layouts: Collection[SimLayout],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> float:
        valid_areas = [
            area
            for layout in units_layouts
            for area in layout.areas
            if area.type in valid_area_types
        ]
        value = float(
            np.mean(
                [max_rectangle_by_area_id[area.db_area_id].area for area in valid_areas]
            )
        )
        if np.isnan(value):
            return 0.0
        return value

    def _average_callable_room_by_sim_dimension(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        unit_area_stats: dict[int, dict[int, dict[str, dict[str, float]]]],
        dimension: str,
        aggregation_func: Callable,
    ) -> float:
        """Returns an average of observations applying a func (like min, max, mean...) of all unit layouts"""
        func_observations = []
        for unit_ids_layouts in layouts_per_apartment.values():
            mean_values = []
            for unit_id, layout in unit_ids_layouts.items():
                mean_values.extend(
                    [
                        unit_area_stats[unit_id][area.db_area_id][dimension]["mean"]
                        for area in layout.areas
                        if area.type in self.classification_schema.LIVING_AND_BEDROOMS
                    ]
                )
            if mean_values:
                func_observations.append(aggregation_func(mean_values))

        if not func_observations:
            raise CompetitionFeaturesValueError(
                f"Can't calculate {dimension} for units: {layouts_per_apartment.keys()}"
            )

        return float(np.mean(func_observations))

    def _get_outdoor_indoor_areas(self, layouts: Collection[SimLayout]) -> AreasTotal:
        outdoor_area = 0
        indoor_area = 0

        all_areas = (area for layout in layouts for area in layout.areas)
        for area in all_areas:
            if area.type in self.classification_schema.OUTDOOR_AREAS:
                outdoor_area += area.footprint.area
            else:
                indoor_area += area.footprint.area

        return AreasTotal(outdoor_area, indoor_area)

    def pct_circulation_over_total_residential_space(
        self, units_layouts: Collection[SimLayout]
    ) -> float:
        """The return value is a percentage"""
        circulation_area = 0.0
        total_area = 0.0
        stairs_area = 0.0

        all_areas = (area for layout in units_layouts for area in layout.areas)
        for area in all_areas:
            total_area += area.footprint.area
            if area.type in self.classification_schema.STAIR_AREA:
                # If the area is staircase we count all the space
                stairs_area += area.footprint.area
            else:
                if area.type in self.classification_schema.CIRCULATION_AREAS:
                    circulation_area += area.footprint.area

                # Otherwise we count the feature stair size in any other area type
                stairs_area += sum(
                    feature.footprint.area
                    for feature in area.features
                    if feature.type == FeatureType.STAIRS
                )

        if total_area:
            return (circulation_area + stairs_area) / total_area
        return 0.0

    @staticmethod
    def bike_parking_count(layouts: Collection[SimLayout]) -> int:
        all_features_counter = Counter(
            [
                feature.type
                for layout in layouts
                for area in layout.areas
                for feature in area.features
            ]
        )
        return int(all_features_counter[FeatureType.BIKE_PARKING])

    @staticmethod
    def apartment_types_percentage(
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]]
    ) -> dict[str, float]:
        """
        Returns: A dict with key as the type of apartment and the value as the percentage over all the apartments
        """
        number_of_rooms = [
            CustomValuatorBasicFeatures2().number_of_rooms(units_layouts.values())[0][1]
            for units_layouts in layouts_per_apartment.values()
        ]

        return {
            f"{flat_type:.1f}": count / len(layouts_per_apartment)
            for flat_type, count in Counter(number_of_rooms).items()
        }

    @staticmethod
    def apartment_types_area(
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]]
    ) -> list[tuple[str, float]]:
        """
        Returns: list of tuple with room_type, apt_area_size
        """
        base_features = CustomValuatorBasicFeatures2()
        apt_data = [
            (
                f"{base_features.number_of_rooms(units_layouts.values())[0][1]:.1f}",
                base_features.sia_dimensions(layouts=units_layouts.values())[
                    SIACategory.HNF.name
                ],
            )
            for units_layouts in layouts_per_apartment.values()
        ]

        return apt_data

    @staticmethod
    def any_layout_have_area_type(
        layouts: Collection[SimLayout], area_type: AreaType
    ) -> bool:
        """Checks if at least one layout have this area type"""
        return area_type in {area.type for layout in layouts for area in layout.areas}

    @staticmethod
    def all_layout_have_area_type(
        layouts: Collection[SimLayout], area_type: AreaType
    ) -> bool:
        """Check if all the layouts have at least an area_type"""
        return all(
            [area_type in {a.type for a in layout.areas} for layout in layouts]
            or [False]  # In case there are no layouts this is False
        )

    @staticmethod
    def _get_bathrooms_features(unit_layouts: list[SimLayout]) -> list[dict[str, int]]:
        """Returns a list of features per bathroom"""
        bathroom_feature_types = {
            FeatureType.SHOWER,
            FeatureType.TOILET,
            FeatureType.BATHTUB,
            FeatureType.SINK,
        }

        bathrooms_features = []
        bathrooms = (
            bathroom
            for layout in unit_layouts
            for bathroom in layout.areas_by_type[AreaType.BATHROOM]
        )
        for bathroom in bathrooms:
            feature_counts = Counter(
                [
                    feature.type.name
                    for feature in bathroom.features
                    if feature.type in bathroom_feature_types
                ]
            )
            # We check there is at least one element in the feature_counts
            bathrooms_features.append(
                {
                    feature.name: 1 if feature_counts.get(feature.name, 0) else 0
                    for feature in bathroom_feature_types
                }
            )

        return bathrooms_features

    @staticmethod
    def _update_bathrooms_features_distribution(
        number_of_rooms: str,
        number_of_apartments: int,
        bathrooms_features: list[dict[str, int]],
        bathrooms_features_distribution: dict[
            str, list[dict[str, Union[float, list[dict[str, int]]]]]
        ],
    ):
        for layout_variant in bathrooms_features_distribution[number_of_rooms]:
            if not DeepDiff(
                layout_variant["features"],
                bathrooms_features,
                ignore_order=True,
            ):
                layout_variant["percentage"] += 1 / number_of_apartments  # type: ignore
                break
        else:
            bathrooms_features_distribution[number_of_rooms].append(
                {
                    "features": bathrooms_features,
                    "percentage": 1 / number_of_apartments
                    if number_of_apartments
                    else 0.0,
                }
            )

    @staticmethod
    def layouts_by_apartment_type(
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]]
    ) -> dict[str, list[list[SimLayout]]]:
        apartments_by_number_of_rooms = defaultdict(list)
        for unit_layouts in layouts_per_apartment.values():
            number_of_rooms = f_to_str(
                CustomValuatorBasicFeatures2().number_of_rooms(unit_layouts.values())[
                    0
                ][1]
            )
            apartments_by_number_of_rooms[number_of_rooms].append(
                list(unit_layouts.values())
            )
        return apartments_by_number_of_rooms

    def bathrooms_features_distribution(
        self, layouts_per_apartment: defaultdict[str, dict[int, SimLayout]]
    ) -> dict[str, list[dict[str, Union[float, list[dict[str, int]]]]]]:
        layouts_by_apartment_type = self.layouts_by_apartment_type(
            layouts_per_apartment
        )

        features_distribution: dict[
            str, list[dict[str, Union[float, list[dict[str, int]]]]]
        ] = defaultdict(list)
        for number_of_rooms, apartment_layouts in layouts_by_apartment_type.items():
            for apartment_layout in apartment_layouts:
                bathrooms_features = self._get_bathrooms_features(
                    unit_layouts=apartment_layout
                )
                self._update_bathrooms_features_distribution(
                    number_of_rooms=number_of_rooms,
                    number_of_apartments=len(apartment_layouts),
                    bathrooms_features=bathrooms_features,
                    bathrooms_features_distribution=features_distribution,
                )

        return features_distribution

    def bathrooms_toilets_distribution(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
    ) -> dict[str, list[list[str]]]:
        """
        return Structure:
        apt_type: list for each apartment listing all bathrooms and toilets. Ex:
            {"1.5" : [[BATHROOM, BATHROOM], [BATHROOM, TOILET]]}
            A site with two 1.5ers, one with 2 bathrooms and 1 with a bathroom and toilet
        """
        features_of_interest = {
            FeatureType.SHOWER,
            FeatureType.BATHTUB,
            FeatureType.TOILET,
        }

        features_distribution: defaultdict[str, list[list[str]]] = defaultdict(list)
        for number_of_rooms, apartments in self.layouts_by_apartment_type(
            layouts_per_apartment=layouts_per_apartment
        ).items():
            for apartment in apartments:
                apt_data: list[str] = []
                for layout in apartment:
                    for space in layout.spaces:
                        if relevant_features := {
                            feature.type
                            for feature in space.features
                            if feature.type in features_of_interest
                        }:
                            if (
                                FeatureType.SHOWER in relevant_features
                                or FeatureType.BATHTUB in relevant_features
                            ):
                                apt_data.append(SERVICE_ROOM_TYPES.BATHROOM.name)
                            else:
                                apt_data.append(SERVICE_ROOM_TYPES.TOILET.name)
                features_distribution[number_of_rooms].append(apt_data)

        return dict(features_distribution)

    @staticmethod
    def max_area_size(
        layouts: list[SimLayout], area_types: set[AreaType]
    ) -> Union[float, None]:
        """Takes the bigger area type of all layouts provided"""
        return max(
            (
                a.footprint.area
                for layout in layouts
                for a in layout.areas
                if a.type in area_types
            ),
            default=None,
        )

    @staticmethod
    def sum_area_size(layouts: list[SimLayout], area_types: set[AreaType]) -> float:
        """Sum all area_types area of all layouts provided"""
        return sum(
            [
                a.footprint.area
                for layout in layouts
                for a in layout.areas
                if a.type in area_types
            ]
        )

    def _find_connected_public_spaces_recursively(
        self,
        space_id: str,
        space_connections: dict[str, list[dict[str, str]]],
        public_spaces: dict[str, SimSpace],
        scanned_spaces: Optional[set] = None,
    ) -> Iterator[SimSpace]:
        """Yields all public spaces connected to the provided space_id.

        Args:
            space_id: The space for which you want to find connected public spaces.
            space_connections: Space connections' dict with key space_id and
                                value list of dicts with key door_id and value space_id
            public_spaces: Dictionary of public spaces by space_id
            scanned_spaces: Optional set of space_ids which were already found and yielded (to avoid infinite recursion)
        """
        yield public_spaces[space_id]

        # NOTE: to avoid infinite recursion we track
        # which spaces were already found and returned
        if scanned_spaces is None:
            scanned_spaces = set()
        scanned_spaces.add(space_id)

        # loop over all connected spaces
        for connected_space_by_door_id in space_connections[space_id]:
            for connected_space_id in connected_space_by_door_id.values():
                # if the connected space is a public space and wasn't yet found
                if (
                    connected_space_id in public_spaces
                    and connected_space_id not in scanned_spaces
                ):
                    # then find and yield all its connected public spaces
                    yield from self._find_connected_public_spaces_recursively(
                        space_id=connected_space_id,
                        space_connections=space_connections,
                        public_spaces=public_spaces,
                        scanned_spaces=scanned_spaces,
                    )

    def _wc_is_in_public_space(
        self,
        layout: SimLayout,
        public_layout: SimLayout,
        maximum_distance_in_meters: float = 5.0,
    ) -> bool:
        entrance_doors = layout.openings_by_type[OpeningType.ENTRANCE_DOOR]
        space_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=entrance_doors | public_layout.openings_by_type[OpeningType.DOOR],
            spaces_or_areas=public_layout.spaces | layout.spaces,
        )
        public_spaces = {space.id: space for space in public_layout.spaces}
        for entrance_door in entrance_doors:
            # find the public space connected to the private layout by entrance door
            if connected_public_spaces := [
                space_id
                for space_id, connected_spaces_by_door in space_connections.items()
                if space_id in public_spaces
                and any(
                    entrance_door.id in connected_space_by_door
                    for connected_space_by_door in connected_spaces_by_door
                )
            ]:
                space_id = connected_public_spaces[0]

                # extend the entrance door footprint
                extended_door_footprint = entrance_door.footprint.buffer(
                    maximum_distance_in_meters
                )
                # find all public connected spaces
                connected_spaces = list(
                    self._find_connected_public_spaces_recursively(
                        space_id=space_id,
                        public_spaces=public_spaces,
                        space_connections=space_connections,
                    )
                )
                for connected_space in connected_spaces:
                    # make sure at least one toilet intersects
                    # with the extended door footprint
                    if any(
                        any(
                            feature.type == FeatureType.TOILET
                            for feature in area.features
                        )
                        and area.footprint.intersects(extended_door_footprint)
                        for area in connected_space.areas
                    ):
                        return True

        return False

    def janitor_wc_adjacent_or_adjoining(
        self,
        janitor_layouts: defaultdict[int, list[SimLayout]],
        public_layouts: dict[int, SimLayout],
    ) -> bool:
        janitor_office_layouts = [
            (floor_id, layout)
            for floor_id, layouts in janitor_layouts.items()
            for layout in layouts
            if any(a.type == AreaType.OFFICE for a in layout.areas)
        ]
        if not janitor_office_layouts:
            return False

        for floor_id, layout in janitor_office_layouts:
            if not (
                # eiter a toilet exists within the janitor office layout
                any(f.type == FeatureType.TOILET for f in layout.features)
                # or a toilet exists in public space
                or (
                    floor_id in public_layouts
                    and self._wc_is_in_public_space(
                        layout=layout,
                        public_layout=public_layouts[floor_id],  # type: ignore
                        maximum_distance_in_meters=self.JANITOR_MAX_TOILET_DISTANCE,
                    )
                )
            ):
                return False
        return True

    @staticmethod
    def _get_janitor_storeroom_areas(
        janitor_layouts: list[SimLayout], plan_layouts: list[SimLayout]
    ):
        area_by_db_area_id = {
            area.db_area_id: area
            for plan_layout in plan_layouts
            for area in plan_layout.areas
        }

        layouts_storeroom_areas = []
        for layout in janitor_layouts:
            storeroom_areas = [
                area_by_db_area_id[area.db_area_id]
                for area in layout.areas
                if area.type is AreaType.STOREROOM
            ]
            if storeroom_areas:
                layouts_storeroom_areas.append(storeroom_areas)

        return layouts_storeroom_areas

    @staticmethod
    def _get_plan_by_db_area_id(plan_layouts: list[SimLayout]) -> dict[int, SimLayout]:
        return {
            area.db_area_id: plan_layout
            for plan_layout in plan_layouts
            for area in plan_layout.areas
        }

    def _get_areas_with_water_supply_by_plan(
        self, plan_layouts: list[SimLayout]
    ) -> dict[SimLayout, list[SimArea]]:
        return {
            plan_layout: [
                area
                for area in plan_layout.areas
                if area.type in self.classification_schema.AREA_TYPES_WITH_WATER_SUPPLY
            ]
            for plan_layout in plan_layouts
        }

    def janitor_storerooms_water_connections_available(
        self, janitor_layouts: list[SimLayout], plan_layouts: list[SimLayout]
    ) -> bool:
        """
        Checks if all janitor storerooms are connected to an area type with water supply via a shared wall.
        """
        plan_by_db_area_id = self._get_plan_by_db_area_id(plan_layouts=plan_layouts)
        areas_with_water_supply_by_plan = self._get_areas_with_water_supply_by_plan(
            plan_layouts=plan_layouts
        )

        if not (
            layouts_storeroom_areas := self._get_janitor_storeroom_areas(
                janitor_layouts=janitor_layouts, plan_layouts=plan_layouts
            )
        ):
            return False

        apartments_matching_criteria = 0
        for storeroom_areas in layouts_storeroom_areas:
            if all(
                self.area_is_connected_by_wall(
                    area=area,
                    layout=plan_by_db_area_id[area.db_area_id],
                    areas_of_interest=areas_with_water_supply_by_plan[
                        plan_by_db_area_id[area.db_area_id]
                    ],
                    max_distance=self.MAX_DISTANCE_TO_WATER,
                )
                for area in storeroom_areas
            ):
                apartments_matching_criteria += 1

        return apartments_matching_criteria == len(layouts_storeroom_areas)

    @staticmethod
    def _get_areas_by_apartment(
        plan_layouts: list[SimLayout],
        apartment_db_area_ids: defaultdict[str, list[int]],
    ) -> Iterator[Iterator[SimArea]]:
        area_by_db_area_id = {
            area.db_area_id: area for layout in plan_layouts for area in layout.areas
        }
        for db_area_ids in apartment_db_area_ids.values():
            yield (area_by_db_area_id[db_area_id] for db_area_id in db_area_ids)

    def reduit_with_water_connection(
        self,
        apartment_db_area_ids: defaultdict[str, list[int]],
        plan_layouts: list[SimLayout],
        max_rectangle_by_area_id: dict[int, Polygon],
    ):
        plan_by_db_area_id = self._get_plan_by_db_area_id(plan_layouts=plan_layouts)
        areas_with_water_supply_by_plan = self._get_areas_with_water_supply_by_plan(
            plan_layouts=plan_layouts
        )
        areas_by_apartment = self._get_areas_by_apartment(
            plan_layouts=plan_layouts, apartment_db_area_ids=apartment_db_area_ids
        )
        apartments_passed = 0
        for apartment_areas in areas_by_apartment:
            if any(
                self._rectangle_has_minimum_width_length_and_area(
                    polygon=max_rectangle_by_area_id[area.db_area_id],
                    bigger_side_req=self.REDUIT_WASHING_MACHINE_MIN_DIMENSION,
                    smaller_side_req=self.REDUIT_WASHING_MACHINE_MIN_DIMENSION,
                    min_area_req=self.REDUIT_WASHING_MACHINE_MIN_SIZE,
                )
                and self.area_is_connected_by_wall(
                    area=area,
                    layout=plan_by_db_area_id[area.db_area_id],
                    areas_of_interest=areas_with_water_supply_by_plan[
                        plan_by_db_area_id[area.db_area_id]
                    ],
                    max_distance=self.MAX_DISTANCE_TO_WATER,
                )
                for area in apartment_areas
                if area.type is AreaType.STOREROOM
            ):
                apartments_passed += 1
        if len(apartment_db_area_ids):
            return apartments_passed / len(apartment_db_area_ids)
        raise CompetitionFeaturesValueError("No residential apartments found")

    @staticmethod
    def area_is_connected_by_wall(
        area: SimArea,
        layout: SimLayout,
        areas_of_interest: list[SimArea],
        max_distance: float,
    ) -> bool:
        """Checks if area shares a wall with any of areas_of_interest"""
        area_walls = (
            s for s in layout.areas_separators[area.id] if s.type is SeparatorType.WALL
        )
        for wall in area_walls:
            if any(
                area.footprint.distance(area_with_water_supply.footprint)
                <= max_distance
                and wall in layout.areas_separators[area_with_water_supply.id]
                for area_with_water_supply in areas_of_interest
            ):
                return True
        return False

    @staticmethod
    def _get_navigable_space(space_footprint: Polygon, corridor_width: float):
        tolerance = 0.975
        return space_footprint.buffer(-corridor_width * tolerance / 2).buffer(
            corridor_width * tolerance / 2
        )

    @classmethod
    def is_navigable(
        cls,
        space_footprint: Polygon,
        opening_footprints: list[Polygon],
        corridor_width: float,
    ) -> bool:
        navigable_space = cls._get_navigable_space(
            space_footprint=space_footprint, corridor_width=corridor_width
        )
        if not isinstance(navigable_space, Polygon):
            logger.debug(f"A passage is smaller than {corridor_width} ...")
            return False

        navigable_space_is_usable = (
            navigable_space.area / space_footprint.area
            >= cls.MIN_USABLE_SPACE_IN_PERCENT
        )
        if not navigable_space_is_usable:
            logger.debug("Navigable space is too small ...")
            return False

        all_openings_intersect_space = all(
            navigable_space.intersects(opening_footprint)
            for opening_footprint in opening_footprints
        )
        if not all_openings_intersect_space:
            logger.debug("Openings do not intersect ...")
            return False

        return True

    def ratio_of_navigable_spaces_area(self, plans: list[dict]) -> dict[str, float]:
        spaces_to_check = [
            (
                space.footprint,
                [
                    o.reference_geometry()
                    for o in plan["plan_layout"].spaces_openings[space.id]
                    if o.is_door
                ],
                plan["floor_numbers"],
            )
            for plan in plans
            for space in plan["plan_layout"].spaces
            if not any(fn < 0 for fn in plan["floor_numbers"])  # plan is underground
            and not any(area.type == AreaType.SHAFT for area in space.areas)
        ]

        # total area of all spaces to check
        all_spaces_area = sum(
            space_footprint.area * len(floor_numbers)
            for space_footprint, _, floor_numbers in spaces_to_check
        )
        result = {}
        for corridor_width in MINIMUM_CORRIDOR_WIDTHS:
            # total area of navigable spaces
            navigable_spaces_area = sum(
                space_footprint.area * len(floor_numbers)
                for space_footprint, openings_footprints, floor_numbers in spaces_to_check
                if self.is_navigable(
                    space_footprint=space_footprint,
                    opening_footprints=openings_footprints,
                    corridor_width=corridor_width,
                )
            )
            result[f"{corridor_width:.1f}"] = (
                navigable_spaces_area / all_spaces_area if all_spaces_area else 0.0
            )

        return result

    def minimum_elevator_dimensions(self, plans: list[dict]) -> bool:
        elevator_dimensions = [
            self._rectangle_has_minimum_width_length(
                polygon=elevator.footprint,
                bigger_side_req=self.BIGGER_SIDE_REQ_ELEVATOR,
                smaller_side_req=self.SMALLER_SIDE_REQ_ELEVATOR,
            )
            for plan in plans
            for elevator in plan["plan_layout"].features_by_type[FeatureType.ELEVATOR]
        ]
        return all(elevator_dimensions or [False])

    @staticmethod
    def _get_periods_of_direct_sunshine(
        sun_observations: list[tuple[int, float]],
        min_threshold: float,
    ) -> list[tuple[float, float]]:
        """
        Args:
            sun_observations: A list of tuples with hour of day and sun value e.g.: [(6, 20.0), (12, 30.0), (18, 20.0)]
            min_threshold: A minimum threshold to determine direct sunlight (anything above is direct sunlight)

        Returns:
            A list of tuples, each tuple representing a time frame during which the sun observations
            are above the minimum threshold. Start and end of a period are expressed in hours of the day
            e.g.: [(9.33, 15.66)]
        """
        sub_observations_sorted = sorted(sun_observations, key=lambda obs: obs[0])
        interpolated_sunshine = LineString(sub_observations_sorted)
        threshold_line = LineString(
            [
                (sub_observations_sorted[0][0], min_threshold),
                (sub_observations_sorted[-1][0], min_threshold),
            ]
        )
        periods_of_sunshine = []
        for line in split(interpolated_sunshine, threshold_line).geoms:
            x, y = line.xy
            if min(y) >= min_threshold:
                periods_of_sunshine.append((min(x), max(x)))

        return periods_of_sunshine or [(0, 0)]

    @staticmethod
    def _aggregate_periods_of_sunshine(periods: list[tuple[float, float]]) -> float:
        if len(periods) == 1:
            start, end = periods[0]
            return end - start

        periods_sorted = sorted(periods, key=lambda p: p[0])
        total_hours_of_sunshine = 0.0
        prev_end = None
        for start, end in periods_sorted:
            if prev_end and start < prev_end:
                total_hours_of_sunshine += end - prev_end
            else:
                total_hours_of_sunshine += end - start
            prev_end = end

        return total_hours_of_sunshine

    def _get_apartments_outdoor_areas_sun_values(
        self,
        plan_layouts: list[SimLayout],
        sun_stats_by_apartment_area: defaultdict[str, dict],
        season: SEASONS,
    ) -> dict[Union[str, int], dict[int, list[tuple[int, float]]]]:

        outdoor_db_area_ids = {
            area.db_area_id
            for plan_layout in plan_layouts
            for area in plan_layout.areas
            if area.type in self.classification_schema.OUTDOOR_AREAS
        }

        apartments_outdoor_areas_sun_values: dict[
            Union[str, int], dict[int, list[tuple[int, float]]]
        ] = defaultdict(dict)
        for client_unit_id, stats_by_area in sun_stats_by_apartment_area.items():
            for db_area_id, stats_by_dimension in stats_by_area.items():
                if db_area_id in outdoor_db_area_ids:
                    apartments_outdoor_areas_sun_values[client_unit_id][db_area_id] = [
                        (
                            SuntimesHandler.get_datetime_from_sun_key(dimension).hour,
                            values["max"],
                        )
                        for dimension, values in stats_by_dimension.items()
                        if SuntimesHandler.get_datetime_from_sun_key(dimension).date()
                        == season.value.date()
                    ]

        return apartments_outdoor_areas_sun_values

    def avg_total_hours_of_sunshine_outside_areas(
        self,
        plan_layouts: list[SimLayout],
        sun_stats_by_apartment_area: defaultdict[str, dict],
        season: SEASONS,
    ) -> float:
        apartments_outdoor_areas_sun_values = (
            self._get_apartments_outdoor_areas_sun_values(
                plan_layouts=plan_layouts,
                sun_stats_by_apartment_area=sun_stats_by_apartment_area,
                season=season,
            )
        )
        if not apartments_outdoor_areas_sun_values:
            return 0.0

        min_threshold = self.DIRECT_SUN_THRESHOLD_SUMMER
        if season is SEASONS.WINTER:
            min_threshold = self.DIRECT_SUN_THRESHOLD_WINTER

        total_hours_of_sun = 0.0
        for sun_observations_by_area in apartments_outdoor_areas_sun_values.values():
            total_hours_of_sun += self._aggregate_periods_of_sunshine(
                [
                    period_of_sunshine
                    for area_sun_observations in sun_observations_by_area.values()
                    for period_of_sunshine in self._get_periods_of_direct_sunshine(
                        sun_observations=area_sun_observations,
                        min_threshold=min_threshold,
                    )
                ]
            )

        return total_hours_of_sun / len(apartments_outdoor_areas_sun_values)

    def avg_apt_bathroom_sia500_size(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> dict[str, list[tuple[float, float, float]]]:
        """Collects area info for bathrooms"""
        apartments_bathrooms_data = {}

        for client_id, units_layouts in layouts_per_apartment.items():
            selected_areas = [
                area
                for unit_layout in units_layouts.values()
                for area in unit_layout.areas_by_type[AreaType.BATHROOM]
            ]
            apartments_bathrooms_data[client_id] = [
                self._extract_area_info(rectangles=max_rectangle_by_area_id, area=area)
                for area in selected_areas
            ]

        return apartments_bathrooms_data

    @staticmethod
    def _rectangle_has_minimum_width_length(
        polygon: Polygon,
        bigger_side_req: float,
        smaller_side_req: float,
    ) -> bool:
        bigger_side_req, smaller_side_req = (
            bigger_side_req * COMPETITION_SIZES_MARGIN,
            smaller_side_req * COMPETITION_SIZES_MARGIN,
        )
        side_lines = get_sides_as_lines_by_length(polygon=polygon)
        short_side, long_side = side_lines[0].length, side_lines[-1].length

        big_side_checks = long_side >= bigger_side_req
        small_side_checks = short_side >= smaller_side_req
        return small_side_checks and big_side_checks

    @classmethod
    def _rectangle_has_minimum_width_length_and_area(
        cls,
        polygon: Polygon,
        bigger_side_req: float,
        smaller_side_req: float,
        min_area_req: float = None,
    ) -> bool:
        if min_area_req is None:
            min_area_req = smaller_side_req * bigger_side_req

        if (
            polygon.area
            >= min_area_req
            * COMPETITION_SIZES_MARGIN  # Allows area to be slightly smaller
            and cls._rectangle_has_minimum_width_length(
                polygon=polygon,
                bigger_side_req=bigger_side_req,
                smaller_side_req=smaller_side_req,
            )
        ):
            return True
        return False

    def avg_apt_bedroom_minimum(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> dict[str, list[tuple[float, float, float]]]:
        apartments_rooms_data = {}
        for client_id, units_layouts in layouts_per_apartment.items():
            selected_areas = [
                area
                for unit_layout in units_layouts.values()
                for area in unit_layout.areas
                if area.type in {AreaType.BEDROOM, AreaType.ROOM}
            ]
            if not selected_areas:
                selected_areas = [
                    area
                    for unit_layout in units_layouts.values()
                    for area in unit_layout.areas
                    if area.type in {AreaType.LIVING_DINING, AreaType.LIVING_ROOM}
                ]
            apartments_rooms_data[client_id] = [
                self._extract_area_info(rectangles=max_rectangle_by_area_id, area=area)
                for area in selected_areas
            ]
        return apartments_rooms_data

    def dinning_sizes_per_apt(
        self,
        layouts_per_apartment: defaultdict[str, dict[int, SimLayout]],
        max_rectangle_by_area_id: dict[int, Polygon],
    ) -> dict[str, list[tuple[float, float, float]]]:
        apartments_dininng_data = {}
        for client_id, units_layouts in layouts_per_apartment.items():
            selected_areas = [
                area
                for unit_layout in units_layouts.values()
                for area in unit_layout.areas
                if area.type in {AreaType.LIVING_DINING, AreaType.LIVING_ROOM}
            ]
            apartments_dininng_data[client_id] = [
                self._extract_area_info(rectangles=max_rectangle_by_area_id, area=area)
                for area in selected_areas
            ]
        return apartments_dininng_data

    def noise_insulated_rooms(
        self,
        residential_units_layouts_with_id: list[tuple[UnitID, SimLayout]],
        noise_window_per_area: dict[UnitID, dict[AreaID, NoiseAreaResultsType]],
    ) -> float:
        """Rooms percentage that can be ventilated from the noise.
        This is considered as such if at least one opening to the outside have a noise lower than the threshold"""
        # aggregate DAY noise in one new dimension:
        noises_per_area: dict[UnitID, dict[AreaID, list[float]]] = {
            unit_id: {
                area_id: [
                    aggregate_noises([n1, n2])
                    for n1, n2 in zip(
                        noise_vals["noise_TRAFFIC_DAY"], noise_vals["noise_TRAIN_DAY"]
                    )
                ]
                for area_id, noise_vals in area_vals.items()
            }
            for unit_id, area_vals in noise_window_per_area.items()
        }

        total_rooms = 0
        total_insulated = 0
        for unit_id, unit_layout in residential_units_layouts_with_id:
            area_to_consider = [
                area
                for area in unit_layout.areas
                if area.type in self.NOISE_INSULATION_AREA_TYPES
                and any(unit_layout.get_windows_and_outdoor_doors(area=area))
            ]
            total_rooms += len(area_to_consider)

            total_insulated += sum(
                [
                    any(
                        noise_value <= self.NOISE_INSULATION_THRESHOLD
                        for noise_value in noises_per_area[unit_id][area.db_area_id]
                    )
                    for area in area_to_consider
                ]
            )

        return total_insulated / total_rooms if total_insulated else 0.0

    @staticmethod
    def _get_floor_number_by_id(
        floors_ids: set[Union[str, int]]
    ) -> dict[Union[str, int], int]:
        floors = FloorDBHandler.find_in(
            id=floors_ids,
            output_columns=["id", "floor_number"],
        )
        floor_number_by_floor_id = {
            floor["id"]: floor["floor_number"] for floor in floors
        }
        return floor_number_by_floor_id

    @staticmethod
    def _extract_area_info(
        rectangles: dict[int, Polygon], area: SimArea
    ) -> tuple[float, float, float]:
        rectangle = rectangles[area.db_area_id]
        side_lines = get_sides_as_lines_by_length(polygon=rectangle)
        short_side, long_side = side_lines[0].length, side_lines[-1].length
        return rectangle.area, long_side, short_side

    @staticmethod
    def calculate_total_living_area(residential_units_layouts: list[SimLayout]):
        return CustomValuatorBasicFeatures2().net_area_by_sia(
            layouts=residential_units_layouts
        )

    @staticmethod
    def calculate_total_hnf_area(layouts: list[SimLayout]):
        return CustomValuatorBasicFeatures2().sia_dimensions(layouts=layouts)[
            SIACategory.HNF.name
        ]

    @staticmethod
    def check_feature_is_present_per_apt_percentage(
        layouts_per_apartment: dict[str, dict[int, SimLayout]],
        targe_feature_type: FeatureType,
    ) -> float:
        apt_that_have_feature = 0
        for layouts in layouts_per_apartment.values():
            features_types = {
                f.type for layout in layouts.values() for f in layout.features
            }
            if targe_feature_type in features_types:
                apt_that_have_feature += 1

        return (
            apt_that_have_feature / len(layouts_per_apartment)
            if layouts_per_apartment
            else 0.0
        )
