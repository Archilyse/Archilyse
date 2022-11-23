from collections import Counter, defaultdict
from functools import partial
from typing import Any, Callable, Dict, List, Tuple, Union

from deepdiff import DeepDiff

from common_utils.competition_constants import (
    AREA_REQ_BATHROOM,
    BIG_ROOM_AREA_REQ,
    COMPETITION_SIZES_MARGIN,
    DEFAULT_MIN_STORE_ROOM_AREA,
    DEFAULT_MIN_TOTAL_AREA,
    DINING_AREA_TABLE_MIN_BIG_SIDE,
    DINING_AREA_TABLE_MIN_SMALL_SIDE,
    MINIMUM_CORRIDOR_WIDTHS,
    SERVICE_ROOM_TYPES,
    SMALL_ROOM_AREA_REQ,
    SMALL_ROOM_SIDE_REQ,
    SMALLER_SIDE_REQ_BATHROOM,
    CompetitionFeatures,
)
from common_utils.constants import UNIT_USAGE
from handlers.competition.utils import f_to_str


class CompetitionFeaturesPreprocessor:
    def __init__(self, configuration_parameters):
        self.conf_params = configuration_parameters

    @property
    def preprocessors(self) -> Dict[str, Callable]:
        return {
            CompetitionFeatures.RESIDENTIAL_USE.value: self.is_only_residential,
            CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: self.residential_ratio,
            CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: self.flat_types_distribution_fulfillment,
            CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: self.flat_types_area_fulfillment,
            CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: self.living_dining_min_req_per_apt_type,
            CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: self.check_rooms_min_sizes,
            CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: self.check_dining_table_min_size,
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: self.check_bathrooms_min_sizes,
            CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: self.shower_bathtub_distribution_fulfillment,
            CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value: self.bathroom_toilet_distribution_fulfillment,
            CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: self.navigable_area_corridor_size,
            CompetitionFeatures.APT_PCT_W_STORAGE.value: partial(
                self.percent_bigger_than,
                minimum_threshold=self.conf_params.get(
                    "min_reduit_size", DEFAULT_MIN_STORE_ROOM_AREA
                )
                * COMPETITION_SIZES_MARGIN,
            ),
            CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: partial(
                self.percent_bigger_than,
                minimum_threshold=self.conf_params.get(
                    "min_outdoor_area_per_apt", DEFAULT_MIN_TOTAL_AREA
                ),
            ),
            CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: lambda x: (
                x >= self.conf_params.get("bikes_boxes_count_min", 10) if x else False
            ),
            CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value: lambda x: (
                x
                >= self.conf_params.get("janitor_office_min_size", 10.0)
                * COMPETITION_SIZES_MARGIN
                if x
                else False
            ),
            CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value: lambda x: (
                x
                >= self.conf_params.get("janitor_storage_min_size", 25.0)
                * COMPETITION_SIZES_MARGIN
                if x
                else False
            ),
            CompetitionFeatures.ANALYSIS_GREENERY.value: partial(round, ndigits=3),
            CompetitionFeatures.ANALYSIS_SKY.value: partial(round, ndigits=3),
            CompetitionFeatures.ANALYSIS_BUILDINGS.value: partial(round, ndigits=3),
            CompetitionFeatures.ANALYSIS_WATER.value: partial(round, ndigits=3),
            CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: partial(
                round, ndigits=3
            ),
            CompetitionFeatures.ANALYSIS_STREETS.value: partial(round, ndigits=3),
        }

    def preprocess(self, features_values: Dict[str, Any]) -> Dict[str, Any]:
        return {
            k: self.preprocessors.get(k, self.identity)(v)
            for k, v in features_values.items()
        }

    @classmethod
    def _room_has_minimum_width_length_and_area(
        cls,
        area_info: Tuple[float, float, float],
        bigger_side_req: float,
        smaller_side_req: float,
        min_area_req: float,
    ) -> bool:
        if not area_info:
            return False
        area, (short_side, long_side) = area_info[0], sorted(area_info[1:])
        area_check = area >= min_area_req
        big_side_check = long_side >= bigger_side_req
        small_side_check = short_side >= smaller_side_req
        return area_check and small_side_check and big_side_check

    @staticmethod
    def identity(feature_value: Any) -> Any:
        return feature_value

    def flat_types_distribution_fulfillment(
        self, feature_value: Dict[float, float]
    ) -> float:
        """
        This feature checks whether the distribution gets to a minimum or between a range,
        depending on the configuration.

        If we only have 1 number, we calculate the degree of fulfillment.
        Ex:
          - Desired: 50%  Real: 50% Fulfillment: 100%
          - Desired: 50%  Real: 25% Fulfillment:  50%

        If a tuple is passed as the configuration, it is checked whether the existing percentage is
         inside the range or not. Ex:
          - Desired: 20-50%  Real: 45% Fulfillment: 100%
          - Desired: 20-50%  Real: 10% Fulfillment:   0%
        If flat_types_distribution_acceptable_deviation is set and we have a tuple for configuration, we still
        give some fullfillment value even if out of range if the deviation is acceptable.
        """
        # Make sure the keys are normalized str
        flat_distributions = {f_to_str(k): v for k, v in feature_value.items()}
        desired_distribution = [
            (map(f_to_str, i["apartment_type"]), i["percentage"])
            for i in self.conf_params.get("flat_types_distribution", [])
        ]

        degree_of_fulfillment = []
        for number_of_rooms, desired_percentage in desired_distribution:
            actual_percentage = sum(
                flat_distributions.get(n, 0) for n in number_of_rooms
            )
            if isinstance(desired_percentage, (int, float)):
                if not actual_percentage:
                    degree_of_fulfillment.append(0.0)
                elif actual_percentage >= desired_percentage:
                    degree_of_fulfillment.append(1.0)
                else:
                    degree_of_fulfillment.append(actual_percentage / desired_percentage)
            elif isinstance(desired_percentage, (tuple, list)):
                min_per, max_per = desired_percentage
                if min_per <= actual_percentage <= max_per:
                    degree_of_fulfillment.append(1.0)
                else:
                    if max_acceptable_deviation := self.conf_params.get(
                        "flat_types_distribution_acceptable_deviation", 0.0
                    ):
                        degree_of_fulfillment.append(
                            self._deviation_fulfillment(
                                actual_percentage,
                                max_acceptable_deviation,
                                max_per,
                                min_per,
                            )
                        )
                    else:
                        degree_of_fulfillment.append(0.0)

        total_degree_of_fulfillment = (
            sum(degree_of_fulfillment) / len(degree_of_fulfillment)
            if degree_of_fulfillment
            else 0
        )
        return total_degree_of_fulfillment

    def flat_types_area_fulfillment(
        self, feature_value: list[tuple[str, float]]
    ) -> float:
        # Make sure the flat types are normalized str
        flat_type_and_area = [
            (f_to_str(f_type), area) for f_type, area in feature_value
        ]
        desired_areas_per_type = {
            f_to_str(i["apartment_type"]): i["area"] * COMPETITION_SIZES_MARGIN
            for i in self.conf_params.get("flat_types_area_fulfillment", [])
        }

        apt_matching_criteria = 0
        for number_of_rooms, area in flat_type_and_area:
            min_desired_area = desired_areas_per_type.get(number_of_rooms, 0)
            if area >= min_desired_area:
                apt_matching_criteria += 1
        return (
            apt_matching_criteria / len(flat_type_and_area)
            if len(flat_type_and_area)
            else 0.0
        )

    @staticmethod
    def _deviation_fulfillment(
        actual_percentage: float,
        max_acceptable_deviation: float,
        max_per: float,
        min_per: float,
    ) -> float:
        deviation = min(
            abs(actual_percentage - max_per),
            abs(min_per - actual_percentage),
        )
        normalized_deviation = min(deviation / max_acceptable_deviation, 1.0)
        return 1.0 - normalized_deviation

    def shower_bathtub_distribution_fulfillment(
        self, feature_value: dict[str, dict]
    ) -> float:
        """
        Example:
             The client expects 3.5 room apartments of which
             - 50% are equipped with 1 shower and 0 bathtubs
             - 50% are equipped with 1 bathtub and 1 shower

             Competitor A delivers a site with 3.5 room apartments of which
             - 50% have 0 shower and 1 bathtubs -> requirement fullfilled
             - 50% have 1 shower and 1 bathtub -> requirement fullfilled
             This results in a degree of fullfillment of 100%

             Competitor B delivers a site with 3.5 room apartments of which
             - 40% have 1 shower and 0 bathtubs -> requirement partially fullfilled (80%)
             - 60% have 1 shower and 1 bathtub -> requirement fullfilled
             This results in a degree of fullfillment of 90%

             Competitor C delivers a site with 3.5 room apartments of which
             - 60% have 0 shower and 1 bathtubs -> requirement not fullfilled (0%)
             - 40% have 1 shower and 1 bathtub -> requirement partially fullfilled (80%)
             This results in a degree of fullfillment of 40%

             Based on the degree of fullfillment scores are calculated:
             Competitor A gets 10 points
             Competitor B gets 9 points
             Competitor C gets 4 points
        """
        # Make sure the keys are normalized str
        actual_layout_distribution: dict[str, dict] = {
            f_to_str(k): v for k, v in feature_value.items()
        }

        desired_layout_distribution = defaultdict(list)
        for i in self.conf_params.get("showers_bathtubs_distribution", []):
            desired_layout_distribution[f_to_str(i["apartment_type"])].append(i)

        degree_of_fulfillment: Dict[str, float] = {}
        distributions = [
            (number_of_rooms, desired_layout)
            for number_of_rooms, desired_layout_variants in desired_layout_distribution.items()
            for desired_layout in desired_layout_variants
        ]
        for number_of_rooms, desired_layout in distributions:
            # find the actual layout by mapping the feature counts ...
            actual_layouts: List[Dict] = [
                actual_layout
                for actual_layout in actual_layout_distribution.get(number_of_rooms, [])
                if not DeepDiff(
                    actual_layout["features"],
                    desired_layout["features"],
                    ignore_order=True,
                )
            ]
            degree_of_fulfillment.setdefault(number_of_rooms, 0.0)
            if actual_layouts:
                actual_layout = actual_layouts[0]
                if actual_layout["percentage"] >= desired_layout["percentage"]:
                    degree_of_fulfillment[number_of_rooms] += 1.0 / len(
                        desired_layout_distribution[number_of_rooms]
                    )
                else:
                    degree_of_fulfillment[number_of_rooms] += (
                        actual_layout["percentage"] / desired_layout["percentage"]
                    ) / len(desired_layout_distribution[number_of_rooms])

        return (
            (sum(degree_of_fulfillment.values()) / len(degree_of_fulfillment))
            if degree_of_fulfillment
            else 0.0
        )

    def bathroom_toilet_distribution_fulfillment(
        self, feature_value: Dict[str, List[List[str]]]
    ) -> float:
        # Make sure the keys are normalized str
        actual_distribution: Dict[str, List[List[str]]] = {
            f_to_str(k): v for k, v in feature_value.items()
        }
        desired_distribution = {
            f_to_str(i["apartment_type"]): [SERVICE_ROOM_TYPES[d] for d in i["desired"]]
            for i in self.conf_params.get("bathrooms_toilets_distribution", [])
        }
        result_accum = []
        for apt_type, apt_distributions in actual_distribution.items():
            desired_service_room_types_count = Counter(
                desired_distribution.get(apt_type, [])
            )
            for apt_details in apt_distributions:
                apt_details_count = Counter(
                    [SERVICE_ROOM_TYPES[a] for a in apt_details]
                )
                for room_type, count in desired_service_room_types_count.items():
                    if apt_details_count.get(room_type, 0) < count:
                        # apartment fails condition
                        result_accum.append(0)
                        break
                else:
                    result_accum.append(1)
        return sum(result_accum) / len(result_accum) if result_accum else 0

    def living_dining_min_req_per_apt_type(
        self, feature_value: dict[str, list[float]]
    ) -> float:
        min_sizes = {
            f_to_str(i["apartment_type"]): i["desired"]
            for i in self.conf_params.get(
                "living_dining_desired_sizes_per_apt_type", []
            )
        }
        num_apartments = sum(len(v) for v in feature_value.values())

        passing_apts = 0
        for apt_type, apt_total_area_living in feature_value.items():
            passing_apts += sum(
                1
                for size in apt_total_area_living
                if size >= min_sizes.get(f_to_str(apt_type), 0)
            )
        return passing_apts / num_apartments if num_apartments else 1.0

    @staticmethod
    def percent_bigger_than(feature_value: dict[str, float], minimum_threshold):
        if not feature_value:
            return 0.0

        return sum(
            1 if value >= minimum_threshold else 0 for value in feature_value.values()
        ) / len(feature_value)

    def navigable_area_corridor_size(self, feature_value: dict[str, float]) -> float:
        min_corridor_size = self.conf_params.get(
            "min_corridor_size", MINIMUM_CORRIDOR_WIDTHS[0]
        )
        return feature_value[f"{float(min_corridor_size):.1f}"]

    def check_bathrooms_min_sizes(
        self, areas_info_by_apartment: Dict[str, List[Tuple[float, float, float]]]
    ) -> float:
        if not areas_info_by_apartment:
            return 0.0

        criteria = self.conf_params.get("min_bathroom_sizes", {})
        min_area = (
            criteria.get("min_area", AREA_REQ_BATHROOM) * COMPETITION_SIZES_MARGIN
        )
        min_small_side = (
            criteria.get("min_small_side", SMALLER_SIDE_REQ_BATHROOM)
            * COMPETITION_SIZES_MARGIN
        )
        min_big_side = (
            criteria.get("min_big_side", SMALLER_SIDE_REQ_BATHROOM)
            * COMPETITION_SIZES_MARGIN
        )

        apt_matching_criteria = 0
        for apartment_areas_info in areas_info_by_apartment.values():
            if any(
                self._room_has_minimum_width_length_and_area(
                    area_info=area_info,
                    min_area_req=min_area,
                    bigger_side_req=min_big_side,
                    smaller_side_req=min_small_side,
                )
                for area_info in apartment_areas_info
            ):
                apt_matching_criteria += 1

        return apt_matching_criteria / len(areas_info_by_apartment)

    def check_rooms_min_sizes(
        self, areas_info_by_apartment: Dict[str, List[Tuple[float, float, float]]]
    ) -> float:
        if not areas_info_by_apartment:
            return 0.0
        criteria = self.conf_params.get("min_room_sizes", {})
        big_room_area = (
            criteria.get("big_room_area", BIG_ROOM_AREA_REQ) * COMPETITION_SIZES_MARGIN
        )
        big_room_side_small = (
            criteria.get("big_room_side_small", SMALL_ROOM_SIDE_REQ)
            * COMPETITION_SIZES_MARGIN
        )
        big_room_side_big = (
            criteria.get("big_room_side_big", SMALL_ROOM_SIDE_REQ)
            * COMPETITION_SIZES_MARGIN
        )

        small_room_area = (
            criteria.get("small_room_area", SMALL_ROOM_AREA_REQ)
            * COMPETITION_SIZES_MARGIN
        )
        small_room_side_small = (
            criteria.get("small_room_side_small", SMALL_ROOM_SIDE_REQ)
            * COMPETITION_SIZES_MARGIN
        )
        small_room_side_big = (
            criteria.get("small_room_side_big", SMALL_ROOM_SIDE_REQ)
            * COMPETITION_SIZES_MARGIN
        )

        apt_matching_criteria = 0
        for areas_info in areas_info_by_apartment.values():
            rooms_pass_bigger_req = [
                self._room_has_minimum_width_length_and_area(
                    area_info=area_info,
                    bigger_side_req=big_room_side_big,
                    smaller_side_req=big_room_side_small,
                    min_area_req=big_room_area,
                )
                for area_info in areas_info
            ]

            rooms_pass_smaller_req = [
                self._room_has_minimum_width_length_and_area(
                    area_info=area_info,
                    bigger_side_req=small_room_side_big,
                    smaller_side_req=small_room_side_small,
                    min_area_req=small_room_area,
                )
                for area_info in areas_info
            ]
            if all(rooms_pass_smaller_req) and any(rooms_pass_bigger_req):
                apt_matching_criteria += 1

        return apt_matching_criteria / len(areas_info_by_apartment)

    def check_dining_table_min_size(
        self, areas_info_by_apartment: Dict[str, List[Tuple[float, float, float]]]
    ) -> float:
        dining_area_table_min_big_side = (
            self.conf_params.get(
                "dining_area_table_min_big_side", DINING_AREA_TABLE_MIN_BIG_SIDE
            )
            * COMPETITION_SIZES_MARGIN
        )
        dining_area_table_min_small_side = (
            self.conf_params.get(
                "dining_area_table_min_small_side", DINING_AREA_TABLE_MIN_SMALL_SIDE
            )
            * COMPETITION_SIZES_MARGIN
        )
        area_req = dining_area_table_min_big_side * dining_area_table_min_small_side
        apt_matching_criteria = 0

        for areas_info in areas_info_by_apartment.values():
            room_can_fit_table = [
                self._room_has_minimum_width_length_and_area(
                    area_info=area_info,
                    bigger_side_req=dining_area_table_min_big_side,
                    smaller_side_req=dining_area_table_min_small_side,
                    min_area_req=area_req,
                )
                for area_info in areas_info
            ]
            if any(room_can_fit_table):
                apt_matching_criteria += 1
        return (
            apt_matching_criteria / len(areas_info_by_apartment)
            if areas_info_by_apartment
            else 0.0
        )

    @staticmethod
    def is_only_residential(distribution_m2: Dict[str, float]) -> float:
        """Checks that there is no commercial area"""
        return not bool(distribution_m2.get(UNIT_USAGE.COMMERCIAL.value, False))

    @staticmethod
    def residential_ratio(distribution_m2: Dict[str, float]) -> Union[float, bool]:
        residential = distribution_m2.get(UNIT_USAGE.RESIDENTIAL.value, 0)
        commercial = distribution_m2.get(UNIT_USAGE.COMMERCIAL.value, 0)
        return residential / (residential + commercial)
