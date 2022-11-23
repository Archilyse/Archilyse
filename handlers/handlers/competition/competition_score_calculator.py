from functools import partial
from typing import Any, Callable, Dict, List

from common_utils.competition_constants import CompetitionFeatures
from common_utils.exceptions import CompetitionConfigurationMissingError


class CompetitionScoreCalculator:
    MAX_SCORE = 10.0

    def __init__(self, competition_data: dict):
        self.conf_param = competition_data["configuration_parameters"]
        self.red_flags_enabled = competition_data.get("red_flags_enabled", False)

    @property
    def score_funcs(self) -> Dict[str, Callable]:
        return {
            CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: self.percentage,
            CompetitionFeatures.ANALYSIS_BUILDINGS.value: self.min_weighted_score,
            CompetitionFeatures.ANALYSIS_STREETS.value: self.min_weighted_score,
            CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: self.min_weighted_score,
            CompetitionFeatures.NOISE_STRUCTURAL.value: self.min_weighted_score,
            CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.value: self.min_weighted_score,
            CompetitionFeatures.BUILDING_PCT_CIRCULATION_RESIDENTIAL.value: self.percentage_reverse,
            CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: self.percentage,
            CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: self.percentage,
            CompetitionFeatures.NOISE_INSULATED_ROOMS.value: self.percentage,
            CompetitionFeatures.RESIDENTIAL_USE.value: self.residential_use,
            CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: self.residential_ratio,
            CompetitionFeatures.RESIDENTIAL_TOTAL_HNF_REQ.value: partial(
                self.more_than_minimum_requirement,
                min_value=self.conf_param.get("total_hnf_req", 1.0),
            ),
            CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: self.percentage,
            CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: self.percentage,
            CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: self.percentage,
            CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: self.percentage,
            CompetitionFeatures.APT_HAS_WASHING_MACHINE.value: self.percentage,
            # RED FLAGS
            CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value: self._red_flag_percentage(),
            CompetitionFeatures.APT_PCT_W_STORAGE.value: self._red_flag_percentage(),
            CompetitionFeatures.APT_PCT_W_OUTDOOR.value: self._red_flag_percentage(),
            CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: self._red_flag_percentage(),
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: self._red_flag_percentage(),
            # This does not change either with red flags or not
            CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.value: self.reversed_bool,
            # Manual
            CompetitionFeatures.KITCHEN_ELEMENTS_REQUIREMENT.value: self.percentage,
            CompetitionFeatures.ENTRANCE_WARDROBE_ELEMENT_REQUIREMENT.value: self.percentage,
            CompetitionFeatures.BEDROOM_WARDROBE_ELEMENT_REQUIREMENT.value: self.percentage,
            CompetitionFeatures.SINK_SIZES_REQUIREMENT.value: self.percentage,
        }

    def _red_flag_percentage(self) -> Callable:
        if self.red_flags_enabled:
            return partial(
                self.more_than_minimum_requirement,
                min_value=1.00,
            )
        return self.percentage

    def calculate_scores(self, sites_features: Dict[str, List[Any]]) -> Dict:
        """
        Args:
            sites_features: A dict with the features per site in an ordered list
                ex: {'feature_1': [site_1_val, site_2_val]}
        Returns:
            A dict with the features scores per site in an ordered list
                ex: {'feature_1': [site_1_score, site_2_score]}
        """
        return {
            feature_name: [
                round(x, 1)
                for x in self.score_funcs.get(feature_name, self.max_weighted_score)(
                    sites_values=feature_values
                )
            ]
            for feature_name, feature_values in sites_features.items()
        }

    @classmethod
    def percentage(cls, sites_values: List[float]) -> List[float]:
        return [cls.MAX_SCORE * feature_val for feature_val in sites_values]

    @classmethod
    def percentage_reverse(cls, sites_values: List[float]) -> List[float]:
        return cls.percentage([1 - feature_val for feature_val in sites_values])

    @classmethod
    def max_weighted_score(cls, sites_values: List) -> List[float]:
        """Max value gets MAX_SCORE and the rest are weighted. Booleans get MAX_SCORE for True and 0 for False"""
        max_value = max([x or 0.0 for x in sites_values])  # Clean None values
        return [
            cls.MAX_SCORE * feature_val / max_value
            if max_value and feature_val
            else 0.0
            for feature_val in sites_values
        ]

    @classmethod
    def min_weighted_score(cls, sites_values: List[float]) -> List[float]:
        min_val = min(sites_values)
        max_val = max(sites_values)
        if max_val > min_val:
            return [
                cls.MAX_SCORE * (1 - (feature_val - min_val) / (max_val - min_val))
                for feature_val in sites_values
            ]
        return [cls.MAX_SCORE for _ in sites_values]

    @classmethod
    def more_than_minimum_requirement(
        cls, min_value: float, sites_values: List[float]
    ) -> List[float]:
        """Checks if value is bigger than minimum or it is 0"""
        return [
            cls.MAX_SCORE if val and val >= min_value else 0.0 for val in sites_values
        ]

    @classmethod
    def reversed_bool(cls, sites_values: List[bool]) -> List[float]:
        return [cls.MAX_SCORE if not val else 0 for val in sites_values]

    def residential_use(self, sites_values: List[bool]) -> List[float]:
        """Sites values are True if only_residential"""
        commercial_use_desired = self.conf_param.get("commercial_use_desired", False)
        return (
            self.reversed_bool(sites_values=sites_values)
            if commercial_use_desired
            else self.max_weighted_score(sites_values=sites_values)
        )

    def residential_ratio(self, sites_values: List[float]):
        """Values are percentage of residential"""
        try:
            conf = self.conf_param["residential_ratio"]
            residential_desired_ratio = conf["desired_ratio"]
        except KeyError:
            raise CompetitionConfigurationMissingError(
                "Competition missing configuration residential_ratio in commercial_use_desired feature"
            )
        # In case the acceptable deviation is 0, we put a very small margin or all would fail
        max_acceptable_deviation = max(conf.get("acceptable_deviation", 0.1), 0.01)

        deviations = []

        for residential_ratio in sites_values:
            deviation = abs(residential_desired_ratio - residential_ratio)
            deviations.append(min(deviation / max_acceptable_deviation, 1.0))
        # The lowest deviation score best
        return self.percentage_reverse(sites_values=deviations)
