from http import HTTPStatus

import pytest
from deepdiff import DeepDiff

from common_utils.competition_constants import FAKE_FEATURE_VALUES, CompetitionFeatures
from handlers.competition import CompetitionHandler
from handlers.competition.utils import CompetitionCategoryTreeGenerator
from handlers.db import CompetitionDBHandler, SiteDBHandler
from slam_api.apis.competition.endpoints import (
    CompetitionParametersView,
    competition_app,
)
from tasks.workflow_tasks import WorkflowGenerator
from tests.flask_utils import get_address_for


def test_get_competitors_features_1(
    competition_with_fake_feature_values,
    expected_competition_features_preprocessed_site_1,
    expected_competition_features_preprocessed_site_2,
):
    # Then
    features = CompetitionHandler(
        competition_id=competition_with_fake_feature_values["id"]
    ).get_competitors_features_values()

    expected_features = []
    for site_id, expected_features_by_site in zip(
        competition_with_fake_feature_values["competitors"],
        (
            expected_competition_features_preprocessed_site_1,
            expected_competition_features_preprocessed_site_2,
        ),
    ):
        site = SiteDBHandler.get_by(id=site_id)
        expected_features.append(
            {
                "id": site["id"],
                "name": site["name"],
                **FAKE_FEATURE_VALUES,
                **expected_features_by_site,
            }
        )
    assert not DeepDiff(
        expected_features,
        features,
        ignore_order=True,
        significant_digits=3,
    )


def test_get_competitors_features_with_manual_input_overwriting(
    competition_with_fake_feature_values,
    expected_competition_features_preprocessed_site_1,
    expected_competition_features_preprocessed_site_2,
    competition_first_client_features_input,
    overwritten_client_features,
):
    """Make sure the features given by the client always overwrite any value calculated by us when the flag is True"""
    competition_id = competition_with_fake_feature_values["id"]
    competitors = competition_with_fake_feature_values["competitors"]

    # Then
    features = CompetitionHandler(
        competition_id=competition_id
    ).get_competitors_features_values()

    site_0 = SiteDBHandler.get_by(id=competitors[0])

    expected_features_competitor_0 = {
        "id": site_0["id"],
        "name": site_0["name"],
        **FAKE_FEATURE_VALUES,
        **expected_competition_features_preprocessed_site_1,
        # Overwritten value. Was True, now it is False
        CompetitionFeatures.RESIDENTIAL_USE.value: False,
    }

    features_competitor_0 = [f for f in features if f["id"] == site_0["id"]][0]

    assert not DeepDiff(
        features_competitor_0,
        expected_features_competitor_0,
        ignore_order=True,
        significant_digits=3,
    )

    site_1 = SiteDBHandler.get_by(id=competitors[1])
    expected_features_competitor_1 = {
        "id": site_1["id"],
        "name": site_1["name"],
        **FAKE_FEATURE_VALUES,
        **expected_competition_features_preprocessed_site_2,
    }

    features_competitor_1 = [f for f in features if f["id"] == site_1["id"]][0]
    assert not DeepDiff(
        features_competitor_1,
        expected_features_competitor_1,
        ignore_order=True,
        significant_digits=3,
    )


def test_get_competitors_features_returns_fake_feature_values_if_no_computed_features_exist(
    site,
    competition_with_fake_feature_values,
    expected_competition_features_preprocessed_site_1,
):
    features = CompetitionHandler(
        competition_id=competition_with_fake_feature_values["id"]
    ).get_competitors_features_values()

    features[0].pop("id")
    features[0].pop("name")
    assert set(features[0].keys()) == set(FAKE_FEATURE_VALUES.keys())
    assert len(features[0]) != expected_competition_features_preprocessed_site_1


class TestCompetitionScores:
    def test_compute_competitors_scores(
        self,
        competition_with_fake_feature_values,
        expected_competition_scores_site_2,
        competition_first_client_features_input,
        expected_competition_scores_site_1_w_manual_input,
    ):

        scores = CompetitionHandler(
            competition_id=competition_with_fake_feature_values["id"]
        ).compute_competitors_scores()

        for score in scores:
            score.pop("id")
        expected_competition_scores_site_2.pop("id")

        assert len(scores) == 2
        assert not DeepDiff(
            expected_competition_scores_site_1_w_manual_input,
            scores[0],
            ignore_order=True,
            significant_digits=3,
        )
        assert not DeepDiff(
            expected_competition_scores_site_2,
            scores[1],
            ignore_order=True,
            significant_digits=3,
        )

    def test_compute_competitors_scores_selected_features(
        self,
        competition_with_fake_feature_values,
        expected_competition_scores_site_2,
        competition_first_client_features_input,
        expected_competition_scores_site_1_w_manual_input,
    ):
        """Check that competition filters out scores at sub category level too"""
        CompetitionDBHandler.update(
            item_pks={"id": competition_with_fake_feature_values["id"]},
            new_values={"features_selected": [CompetitionFeatures.NOISE_STRUCTURAL]},
        )
        scores = CompetitionHandler(
            competition_id=competition_with_fake_feature_values["id"]
        ).compute_competitors_scores()

        # Only this top level category and subcategory actually have scores
        assert scores[0].pop("architecture_usage") == 10
        assert scores[0].pop("noise") == 10
        assert scores[0].pop("total_archilyse") == 2.7
        assert scores[0].pop("total") == 2.7

        # All the other categories and subcategories should be 0.0
        # We dont really care about leaves as they are not shown
        full_category_tree = CompetitionCategoryTreeGenerator(
            red_flags_enabled=False
        ).get_category_tree()
        for top_level_category in full_category_tree:
            assert scores[0].get(top_level_category["key"], 0) == 0
            for sub_category in top_level_category["sub_sections"]:
                assert scores[0].get(sub_category["key"], 0) == 0

    def test_full_competition_flow(
        self,
        celery_eager,
        client,
        site,
        site_prepared_for_competition,
        expected_competition_scores_site_1,
        competition_configuration,
    ):
        # Given a competition
        competition = CompetitionDBHandler.add(
            competitors=[site["id"]],
            weights={
                "architecture_usage": 0.27,
                "architecture_room_programme": 0.38,
                "environmental": 0.2,
                "further_key_figures": 0.15,
            },
            client_id=site["client_id"],
        )
        # First calculate competition features
        WorkflowGenerator(
            site_id=site["id"]
        ).get_competition_features_task_chain().delay()

        # Then prepare competition configuration parameters
        url = get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=CompetitionParametersView,
            competition_id=competition["id"],
        )
        response = client.put(url, json=competition_configuration)
        assert response.status_code == HTTPStatus.OK

        scores = CompetitionHandler(
            competition_id=competition["id"]
        ).compute_competitors_scores()

        # Expected scores are defined to work with the site 2, so there are changes in view values
        expected = {
            **expected_competition_scores_site_1,
            **{
                "environmental_design": 10.0,
                "environmental": 10.0,
                "total": 6.61,
                "total_archilyse": 2.97,
                "total_program": 3.64,
                CompetitionFeatures.ANALYSIS_GREENERY.value: 10.0,
                CompetitionFeatures.ANALYSIS_SKY.value: 10.0,
                CompetitionFeatures.ANALYSIS_WATER.value: 10.0,
                CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: 10.0,
                CompetitionFeatures.ANALYSIS_STREETS.value: 10.0,
                CompetitionFeatures.ANALYSIS_BUILDINGS.value: 10.0,
                CompetitionFeatures.NOISE_INSULATED_ROOMS.value: 0.0,
            },
        }
        assert not DeepDiff(
            expected,
            scores[0],
            ignore_order=True,
            significant_digits=3,
        )


@pytest.mark.parametrize(
    "features_selected",
    [
        ([]),
        ([CompetitionFeatures.NOISE_INSULATED_ROOMS]),
        (
            [
                CompetitionFeatures.NOISE_INSULATED_ROOMS,
                CompetitionFeatures.ANALYSIS_GREENERY,
            ]
        ),
    ],
)
def test_competition_features_selected_add_serialization(site, features_selected):
    """Test the serialization of the array of enums on the DB and that it works as expected"""
    competition_db = CompetitionDBHandler.add(
        competitors=[site["id"]],
        weights={
            "architecture_usage": 0.27,
            "architecture_room_programme": 0.38,
            "environmental": 0.2,
            "further_key_figures": 0.15,
        },
        client_id=site["client_id"],
        features_selected=features_selected,
    )
    assert competition_db["features_selected"] == features_selected


@pytest.mark.parametrize(
    "features_selected_existing, update",
    [
        ([], []),
        ([CompetitionFeatures.NOISE_INSULATED_ROOMS], []),
        (
            [
                CompetitionFeatures.NOISE_INSULATED_ROOMS,
                CompetitionFeatures.ANALYSIS_GREENERY,
            ],
            [
                CompetitionFeatures.AGF_W_REDUIT,
                CompetitionFeatures.ANALYSIS_GREENERY,
            ],
        ),
    ],
)
def test_competition_features_selected_update_serialization(
    site, features_selected_existing, update
):
    competition_db = CompetitionDBHandler.add(
        competitors=[site["id"]],
        weights={"something": 1.0},
        client_id=site["client_id"],
        features_selected=features_selected_existing,
    )
    CompetitionDBHandler.update(
        item_pks={"id": competition_db["id"]},
        new_values=dict(features_selected=update),
    )
    competition_db = CompetitionDBHandler.get_by(id=competition_db["id"])
    assert competition_db["features_selected"] == update
