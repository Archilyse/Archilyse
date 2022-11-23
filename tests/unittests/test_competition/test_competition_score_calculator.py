import pytest
from deepdiff import DeepDiff

from handlers.competition.competition_score_calculator import CompetitionScoreCalculator


def test_competition_score_calculator_accept_expected_competition_features_w_red_flags(
    expected_competition_features_preprocessed_site_1,
    expected_competition_features_preprocessed_site_2,
    expected_competition_scores_site_1,
    expected_competition_scores_site_2,
    competition_configuration,
):
    features_dict = {
        feature: [
            expected_competition_features_preprocessed_site_1[feature],
            expected_competition_features_preprocessed_site_2[feature],
        ]
        for feature in expected_competition_features_preprocessed_site_1.keys()
    }
    scores_by_competitor = CompetitionScoreCalculator(
        competition_data={
            "configuration_parameters": competition_configuration,
            "red_flags_enabled": True,
        }
    ).calculate_scores(sites_features=features_dict)

    #  we take the features from the list we sent to the score calculator
    expected_scores = {
        feature: [
            expected_competition_scores_site_1[feature],
            expected_competition_scores_site_2[feature],
        ]
        for feature in features_dict.keys()
    }
    assert not DeepDiff(
        dict(scores_by_competitor), expected_scores, significant_digits=3
    )


def test_competition_score_calculator_accept_expected_competition_features_without_red_flags(
    expected_competition_features_preprocessed_site_1,
    expected_competition_features_preprocessed_site_2,
    expected_competition_scores_site_1_no_red_flags,
    expected_competition_scores_site_2_no_red_flags,
    competition_configuration,
):
    features_dict = {
        feature: [
            expected_competition_features_preprocessed_site_1[feature],
            expected_competition_features_preprocessed_site_2[feature],
        ]
        for feature in expected_competition_features_preprocessed_site_1.keys()
    }
    scores_by_competitor = CompetitionScoreCalculator(
        competition_data={
            "configuration_parameters": competition_configuration,
            "red_flags_enabled": False,
        }
    ).calculate_scores(sites_features=features_dict)

    #  we take the features from the list we sent to the score calculator
    expected_scores = {
        feature: [
            expected_competition_scores_site_1_no_red_flags[feature],
            expected_competition_scores_site_2_no_red_flags[feature],
        ]
        for feature in features_dict.keys()
    }
    assert not DeepDiff(
        expected_scores, dict(scores_by_competitor), significant_digits=3
    )


class TestScorerBasicFuncs:
    @pytest.mark.parametrize(
        "test_values, expected",
        [
            ([5, 2, 1], [10, 4, 2]),
            ([1, 1, 1], [10, 10, 10]),
            ([1], [10]),
            ([0], [0]),
            ([1, 0.8], [10, 8]),
            ([1, 0.8, 0.2], [10, 8, 2]),
            ([45, 120, 89], [3.75, 10.0, 7.41666]),
        ],
    )
    def test_max_weighted_score(self, test_values, expected):
        assert CompetitionScoreCalculator.max_weighted_score(
            sites_values=test_values
        ) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "test_values, expected",
        [
            ([5, 2, 1], [0, 7.5, 10]),
            ([1, 1, 1], [10, 10, 10]),
            ([1], [10]),
            ([0], [10]),
            ([0, 1, 2], [10, 5, 0]),
            ([1, 0.8], [0, 10]),
            ([1, 0.8, 0.2], [0, 2.5, 10]),
        ],
    )
    def test_min_weighted_score(self, test_values, expected):
        assert CompetitionScoreCalculator.min_weighted_score(
            sites_values=test_values
        ) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "test_values, expected",
        [
            ([0.5, 0.2, 0.1], [5, 2, 1]),
            ([1, 1, 1], [10, 10, 10]),
            ([1], [10]),
            ([0], [0]),
            ([1, 0.8], [10, 8]),
            ([1, 0.8, 0.2], [10, 8, 2]),
        ],
    )
    def test_percentage_score(self, test_values, expected):
        assert CompetitionScoreCalculator.percentage(
            sites_values=test_values
        ) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "test_values, expected",
        [
            ([0.5, 0.2, 0.1], [5, 8, 9]),
            ([1, 1, 1], [0, 0, 0]),
            ([1], [0]),
            ([0], [10]),
            ([1, 0.8], [0, 2]),
            ([1, 0.8, 0.2], [0, 2, 8]),
        ],
    )
    def test_reverse_percentage_score(self, test_values, expected):
        assert CompetitionScoreCalculator.percentage_reverse(
            sites_values=test_values
        ) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "test_values, expected",
        [
            ([True, False], [0, 10.0]),
            ([True, True, True], [0, 0, 0]),
            ([False, False, False], [10.0, 10.0, 10.0]),
        ],
    )
    def test_reversed_bool(self, test_values, expected):
        assert CompetitionScoreCalculator.reversed_bool(
            sites_values=test_values
        ) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "test_values, conf,  expected",
        [
            ([True, True], False, [10.0, 10.0]),
            ([True, True], True, [0, 0]),
            ([False, False], False, [0, 0]),
            ([False, False], True, [10, 10]),
            ([True, False], True, [0, 10]),
        ],
    )
    def test_score_residential_use(self, test_values, conf, expected):
        assert CompetitionScoreCalculator(
            {"configuration_parameters": {"commercial_use_desired": conf}}
        ).residential_use(sites_values=test_values) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "sites_values, conf,  expected",
        [
            (
                [0, 0.5, 0.3, 0.2, 0.25],
                {"desired_ratio": 0.2},
                [0, 0, 0, 10, 5],
            ),
            (
                [0, 0.5, 0.3, 0.2, 0.25],
                {"desired_ratio": 0.2, "acceptable_deviation": 0.3},
                [3.333, 0, 6.666, 10, 8.333],
            ),
            (
                [0, 0.5, 0.3, 0.2, 0.25],
                {"desired_ratio": 0.2, "acceptable_deviation": 0.0},
                [0, 0, 0, 10, 0],
            ),
        ],
    )
    def test_score_residential_ratio(self, sites_values, conf, expected):
        assert CompetitionScoreCalculator(
            {"configuration_parameters": {"residential_ratio": conf}}
        ).residential_ratio(sites_values=sites_values) == pytest.approx(
            expected, abs=0.01
        )
