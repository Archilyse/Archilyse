import string
from datetime import datetime
from functools import cached_property

from common_utils.competition_constants import CATEGORIES, CompetitionFeatures
from handlers.competition import CompetitionHandler
from handlers.db import ClientDBHandler, SiteDBHandler


class CustomWeightingSheetDataProvider:
    GROUP_FEATURES_TO_WEIGHT = [
        [
            CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER,
            CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER,
            CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER,
            CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER,
        ],
        [
            CompetitionFeatures.ANALYSIS_SKY,
            CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS,
            CompetitionFeatures.ANALYSIS_GREENERY,
            CompetitionFeatures.NOISE_INSULATED_ROOMS,
        ],
        [
            CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION,
            CompetitionFeatures.APT_DISTRIBUTION_TYPES,
        ],
    ]

    def __init__(self, competition_id):
        self.competition_handler = CompetitionHandler(competition_id=competition_id)
        self.categories = {
            item["key"]: {
                "category": cat["name"],
                "subcategory": sub_cat["name"],
                "unit": item.get("unit", ""),
                "name": item["name"],
            }
            for cat in CATEGORIES
            for sub_cat in cat["sub_sections"]
            for item in sub_cat["sub_sections"]
        }

    @cached_property
    def competitor_names(self):
        return {
            site["id"]: site["name"]
            for site in SiteDBHandler.find_in(
                id=self.competition_handler.competition["competitors"],
                output_columns=["id", "name"],
            )
        }

    @cached_property
    def client_name(self):
        return ClientDBHandler.get_by(
            id=self.competition_handler.competition["client_id"]
        )["name"]

    def get_title(self):
        name = self.competition_handler.competition["name"]
        today = datetime.today().strftime("%Y%m%d")
        return f"Gewichtungstabelle_{name.translate(str.maketrans({'-': '_', ' ': '_'}))}_{today}"

    def get_scores_data(self):
        features_selected = self.competition_handler.competition["features_selected"]
        competitor_ids = self.competition_handler.competition["competitors"]
        scores = {
            scores.pop("id"): scores
            for scores in self.competition_handler.compute_competitors_scores()
        }

        def get_score_formula(weight_col, score_col):
            return (
                f"=SUMPRODUCT("
                f"Gewichtung!${weight_col}$8:${weight_col}${len(features_selected) + 7}, "
                f"{score_col}$7:{score_col}${len(features_selected) + 6}"
                f")"
            )

        def get_score_group_label_formula(col):
            return f"=Gewichtung!{col}7"

        def get_total_score_formula(col):
            return f"=AVERAGE({col}{len(features_selected) + 8}:{col}{len(features_selected) + 11})"

        def get_competitors_col_letter():
            return [
                string.ascii_uppercase[i] for i in range(1, 1 + len(competitor_ids), 1)
            ]

        # add data header
        rows = [["Item", *self.competitor_names.values()]]
        # add data rows
        rows += [
            [
                self.categories[selected_feature.value]["name"],
                *[
                    scores[competitor_id][selected_feature.value]
                    for competitor_id in competitor_ids
                ],
            ]
            for selected_feature in features_selected
        ]
        # add formulas
        rows += [
            ["Scores"],
            *[
                [
                    get_score_group_label_formula(weight_col),
                    *[
                        get_score_formula(weight_col, col_letter)
                        for col_letter in get_competitors_col_letter()
                    ],
                ]
                for weight_col in ("B", "C", "D", "E")
            ],
            [
                "Total Score",
                *[
                    get_total_score_formula(col_letter)
                    for col_letter in get_competitors_col_letter()
                ],
            ],
        ]
        return rows

    def get_features_data(self):
        features_values = {
            features.pop("id"): features
            for features in self.competition_handler.get_competitors_features_values()
        }

        rows = [["Item", *self.competitor_names.values()]]
        rows += [
            [
                self.categories[selected_feature.value]["name"],
                *[
                    [
                        features[selected_feature.value],
                        self.categories[selected_feature.value]["unit"],
                    ]
                    for competitor_id, features in features_values.items()
                ],
            ]
            for selected_feature in self.competition_handler.competition[
                "features_selected"
            ]
        ]

        return rows

    def get_weighting_data(self):
        features_selected = self.competition_handler.competition["features_selected"]
        # create some fake weights for the example weighting groups
        group_features_weights = [
            1
            / sum(
                selected_feature in group_features
                for selected_feature in features_selected
            )
            for group_features in self.GROUP_FEATURES_TO_WEIGHT
        ]
        rows = [
            [
                self.categories[selected_feature.value]["name"],
                1 / len(features_selected),
                *[
                    group_features_weights[i]
                    if selected_feature in self.GROUP_FEATURES_TO_WEIGHT[i]
                    else ""
                    for i in range(3)
                ],
            ]
            for selected_feature in features_selected
        ]
        # add formulas
        rows += [
            [
                "Total",
                *[
                    f"=SUM({col_letter}8:{col_letter}{len(features_selected) + 7})"
                    for col_letter in ["B", "C", "D", "E"]
                ],
            ]
        ]
        return rows

    def get_header(self):
        return (
            f"Gewichtungstabelle\n"
            f"Client: {self.client_name}\n"
            f"Project: {self.competition_handler.competition['name']}\n"
            f"Date: {datetime.today().strftime('%d.%m.%Y')}"
        )
