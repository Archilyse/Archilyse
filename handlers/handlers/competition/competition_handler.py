import typing
from collections import Counter, defaultdict
from functools import cached_property
from typing import Any, Dict, List, Tuple

from common_utils.competition_constants import FAKE_FEATURE_VALUES, CompetitionFeatures
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    TASK_TYPE,
    UNIT_BASICS_DIMENSION,
    UNIT_USAGE,
)
from common_utils.exceptions import CompetitionConfigurationMissingError
from handlers import SlamSimulationHandler
from handlers.competition import CompetitionFeaturesPreprocessor
from handlers.db import (
    CompetitionDBHandler,
    CompetitionFeaturesDBHandler,
    CompetitionManualInputDBHandler,
    SiteDBHandler,
    SlamSimulationDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_simulation_name

from .competition_score_calculator import CompetitionScoreCalculator
from .utils import CompetitionCategoryTreeGenerator


class CompetitionHandler:
    def __init__(self, competition_id: int):
        self.competition = CompetitionDBHandler.get_by(id=competition_id)
        if not self.competition["configuration_parameters"]:
            raise CompetitionConfigurationMissingError(
                "The competition needs to be configured"
            )

        self.category_tree = CompetitionCategoryTreeGenerator(
            red_flags_enabled=self.competition["red_flags_enabled"],
            features_selected=self.competition.get("features_selected"),
        ).get_category_tree()

    @classmethod
    def _get_competitor_names(cls, competitor_ids: List[int]) -> Dict[int, str]:
        return {
            site["id"]: site["name"]
            for site in SiteDBHandler.find_in(
                id=competitor_ids,
                output_columns=["id", "name"],
            )
        }

    def _get_competitor_feature_values(self, competitor_id: int):
        feature_values_unfiltered = {
            # TODO remove FAKE_FEATURE_VALUES once we calculate all features ourselves
            **FAKE_FEATURE_VALUES,
            **CompetitionFeaturesDBHandler.get_by(
                run_id=SlamSimulationDBHandler.get_latest_run_id(
                    site_id=competitor_id,
                    task_type=TASK_TYPE.COMPETITION,
                    state=ADMIN_SIM_STATUS.SUCCESS,
                )
            )["results"],
            **self._manual_features_by_competitor.get(competitor_id, {}),
        }
        features_selected = {
            f.value
            for f in (self.competition["features_selected"] or CompetitionFeatures)
        }
        return {
            k: v for k, v in feature_values_unfiltered.items() if k in features_selected
        }

    @cached_property
    def _manual_features_by_competitor(self):
        return {
            x["competitor_id"]: x["features"]
            for x in CompetitionManualInputDBHandler.find(
                competition_id=self.competition["id"],
            )
        }

    def _get_feature_values_by_competitor(self) -> Dict[int, Dict[str, Any]]:
        preprocessor = CompetitionFeaturesPreprocessor(
            configuration_parameters=self.competition["configuration_parameters"]
        )
        return {
            competitor_id: preprocessor.preprocess(
                features_values=self._get_competitor_feature_values(
                    competitor_id=competitor_id
                )
            )
            for competitor_id in self.competition["competitors"]
        }

    def _compute_leaf_feature_scores_by_competitor(
        self,
    ) -> Dict[int, Dict[str, float]]:
        """
        Compute the scores of the leaves values
        """

        sites_features = defaultdict(list)

        # get features and scores by competitor
        feature_values_by_competitor = self._get_feature_values_by_competitor()

        for _, features in feature_values_by_competitor.items():
            for feature_name, feature_value in features.items():
                sites_features[feature_name].append(feature_value)

        scores_by_feature = CompetitionScoreCalculator(
            competition_data=self.competition
        ).calculate_scores(sites_features=sites_features)

        feature_scores_by_competitor: Dict[int, Dict[str, float]] = defaultdict(dict)
        for feature_name, competitors_scores in scores_by_feature.items():
            for competitor_id, score in zip(
                feature_values_by_competitor.keys(), competitors_scores
            ):
                feature_scores_by_competitor[competitor_id][feature_name] = score

        return feature_scores_by_competitor

    def _aggregate_category_scores(
        self,
        scores: Dict[str, Any],
        category_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """Calculates total scores (archilyse and program types)"""
        category_scores, archilyse_scores = self._scores_by_category_and_archilyse(
            scores=scores
        )

        category_scores["total"] = sum(
            category_scores.get(category_key, 0.0) * weight
            for category_key, weight in category_weights.items()
        )
        category_scores["total_archilyse"] = sum(
            archilyse_scores.get(category_key, 0.0) * weight
            for category_key, weight in category_weights.items()
        )
        category_scores["total_program"] = (
            category_scores["total"] - category_scores["total_archilyse"]
        )
        return category_scores

    def _scores_by_category_and_archilyse(
        self, scores: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        category_scores: typing.Counter[str] = Counter()
        archilyse_scores: typing.Counter[str] = Counter()
        for category in self.category_tree:
            for sub_cat in category["sub_sections"]:
                for leaf in sub_cat["sub_sections"]:
                    category_scores[sub_cat["key"]] += scores[leaf["key"]]  # type: ignore
                    if leaf.get("archilyse"):
                        archilyse_scores[sub_cat["key"]] += scores[leaf["key"]]  # type: ignore

                self._agregate_sub_categories(
                    archilyse_scores, category_scores, sub_cat
                )

                category_scores[category["key"]] += category_scores[sub_cat["key"]]  # type: ignore
                archilyse_scores[category["key"]] += archilyse_scores[sub_cat["key"]]  # type: ignore

            self._agregate_sub_categories(archilyse_scores, category_scores, category)

        return dict(category_scores), dict(archilyse_scores)

    def _agregate_sub_categories(self, archilyse_scores, category_scores, sub_cat):
        if sub_cat["sub_sections"]:
            category_scores[sub_cat["key"]] /= len(sub_cat["sub_sections"])  # type: ignore
            archilyse_scores[sub_cat["key"]] /= len(sub_cat["sub_sections"])  # type: ignore
        else:
            category_scores[sub_cat["key"]] = 0
            archilyse_scores[sub_cat["key"]] = 0

    def compute_competitors_scores(self) -> List[Dict[str, float]]:
        """
        Returns:
            a list of flat dicts with competitor scores, e.g:
            [{
                "id": 1,              # site_id of the competitor
                "name": "Freilager",  # name of the competing site
                "feature_1": 10,      # a score based on a feature
                "feature_2": 10,      # a score based on a feature
                ...
                "sub_category_1": 10, # an average of feature scores
                "sub_category_2": 10,
                ...
                "category_1": 10,     # an average of sub_category_score
                "category_2": 10,
                ...
                "total": 10,          # a total weighted score based on all category scores
            }, {...}]
        """
        feature_scores = self._compute_leaf_feature_scores_by_competitor()

        feature_category_scores = {}
        for competitor_id, scores in feature_scores.items():
            feature_category_scores[competitor_id] = self._round_values(
                self._aggregate_category_scores(
                    scores=scores,
                    category_weights=self.competition["weights"],
                )
            )

        return [
            {
                "id": competitor_id,
                **feature_scores[competitor_id],
                **feature_category_scores[competitor_id],
            }
            for competitor_id in self.competition["competitors"]
        ]

    @staticmethod
    def _round_values(scores: Dict[str, float]) -> Dict[str, float]:
        for key, value in scores.items():
            scores[key] = round(value, 2)
        return scores

    def get_competitors_features_values(
        self,
    ) -> List[Dict[str, Any]]:
        """
        Returns:
            A list of competitors data features for the competition id provided.
        """
        competitors_names = self._get_competitor_names(
            competitor_ids=self.competition["competitors"]
        )
        return [
            {
                "id": competitor_id,
                "name": competitors_names[competitor_id],
                **feature_values,
            }
            for competitor_id, feature_values in self._get_feature_values_by_competitor().items()
        ]

    def get_competitors_units(self):
        competitors_units = []
        for site_id in self.competition["competitors"]:
            # deduplicate unit prices and net areas
            basic_features = SlamSimulationHandler.get_latest_results(
                site_id=site_id, task_type=TASK_TYPE.BASIC_FEATURES, success_only=True
            )
            apartments_info = {}
            for unit_info in UnitDBHandler.find(
                site_id=site_id,
                output_columns=[
                    "id",
                    "client_id",
                    "unit_usage",
                    "ph_net_area",
                    "ph_final_gross_rent_annual_m2",
                    "ph_final_sale_price_m2",
                ],
            ):
                if unit_info["unit_usage"] == UNIT_USAGE.RESIDENTIAL.name:
                    net_area = (
                        unit_info["ph_net_area"]
                        or basic_features[unit_info["id"]][0][
                            get_simulation_name(
                                dimension=UNIT_BASICS_DIMENSION.NET_AREA
                            )
                        ]
                    )
                    if self.competition["prices_are_rent"]:
                        ph_price_m2 = unit_info["ph_final_gross_rent_annual_m2"]
                    else:
                        ph_price_m2 = unit_info["ph_final_sale_price_m2"]

                    ph_gross_price = ph_price_m2 * net_area if ph_price_m2 else None
                    apartments_info[unit_info["client_id"]] = {
                        "client_id": unit_info["client_id"],
                        "ph_gross_price": ph_gross_price,
                        "net_area": net_area,
                    }
            competitors_units.append(
                {
                    "competitor_id": site_id,
                    "units": list(apartments_info.values()),
                }
            )
        return competitors_units
