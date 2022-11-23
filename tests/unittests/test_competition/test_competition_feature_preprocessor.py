import pytest

from brooks.types import FeatureType
from common_utils.competition_constants import CompetitionFeatures
from common_utils.constants import UNIT_USAGE
from handlers.competition import CompetitionFeaturesPreprocessor


@pytest.mark.parametrize(
    "configuration, feature_values, expected",
    [
        (
            {3.5: 0.5, 4.5: 0.5},
            {3.5: 0.5, 4.5: 0.5},
            1.0,
        ),
        (
            {3.5: 0.5, 4.5: 0.5},
            {5.5: 1},
            0.0,
        ),
        (
            {3.5: 0.5, 4.5: 0.5},
            {3.5: 0.6, 4.5: 0.4},
            0.9,
        ),
        (
            {3.5: 0.5, 4.5: 0.5},
            {5.5: 0.7, 8: 0.3},
            0.0,
        ),
        ({3.5: 0.5, 4.5: 0.5}, {5.5: 0.8, 4.5: 0.2}, 0.2),
    ],
)
def test_comp_preprocessor_room_count_distribution_deviation(
    configuration, feature_values, expected
):
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters={
            "flat_types_distribution": [
                {"apartment_type": [k], "percentage": v}
                for k, v in configuration.items()
            ]
        }
    ).preprocess(
        {CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: feature_values}
    ) == {
        CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: pytest.approx(
            expected, abs=0.01
        )
    }


@pytest.mark.parametrize(
    "feature_values, expected",
    [
        (
            {
                3.5: [
                    {
                        "features": [
                            {
                                FeatureType.SHOWER.name: 0,
                                FeatureType.TOILET.name: 0,
                                FeatureType.SINK.name: 0,
                                FeatureType.BATHTUB.name: 1,
                            }
                        ],
                        "percentage": 0.6,
                    },
                    {
                        "features": [
                            {
                                FeatureType.SHOWER.name: 1,
                                FeatureType.TOILET.name: 0,
                                FeatureType.SINK.name: 0,
                                FeatureType.BATHTUB.name: 0,
                            }
                        ],
                        "percentage": 0.4,
                    },
                ]
            },
            0.9,
        ),
        (
            {
                3.5: [
                    {
                        "features": [
                            {
                                FeatureType.SHOWER.name: 0,
                                FeatureType.TOILET.name: 0,
                                FeatureType.SINK.name: 0,
                                FeatureType.BATHTUB.name: 1,
                            }
                        ],
                        "percentage": 0.5,
                    },
                    {
                        "features": [
                            {
                                FeatureType.SHOWER.name: 1,
                                FeatureType.TOILET.name: 0,
                                FeatureType.SINK.name: 0,
                                FeatureType.BATHTUB.name: 0,
                            }
                        ],
                        "percentage": 0.5,
                    },
                ]
            },
            1,
        ),
    ],
)
def test_comp_preprocessor_shower_bathtub_distribution_deviation(
    feature_values, expected
):
    configuration = {
        3.5: [
            {
                "features": [
                    {
                        FeatureType.SHOWER.name: 0,
                        FeatureType.TOILET.name: 0,
                        FeatureType.BATHTUB.name: 1,
                        FeatureType.SINK.name: 0,
                    }
                ],
                "percentage": 0.5,
            },
            {
                "features": [
                    {
                        FeatureType.SHOWER.name: 1,
                        FeatureType.TOILET.name: 0,
                        FeatureType.BATHTUB.name: 0,
                        FeatureType.SINK.name: 0,
                    }
                ],
                "percentage": 0.5,
            },
        ]
    }

    assert CompetitionFeaturesPreprocessor(
        configuration_parameters={
            "showers_bathtubs_distribution": [
                {"apartment_type": number_of_rooms, **feature_count}
                for number_of_rooms, feature_counts in configuration.items()
                for feature_count in feature_counts
            ]
        }
    ).preprocess(
        {CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: feature_values}
    ) == {
        CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: pytest.approx(
            expected, abs=0.01
        )
    }


def test_competition_feature_preprocess_expected(
    competition_configuration,
    expected_competition_features_site_1,
    expected_competition_features_preprocessed_site_1,
):
    preprocessed = CompetitionFeaturesPreprocessor(
        configuration_parameters=competition_configuration
    ).preprocess(expected_competition_features_site_1)
    assert preprocessed == pytest.approx(
        expected_competition_features_preprocessed_site_1
    )


@pytest.mark.parametrize("features", [({"conf": "1"}), {}])
def test_competition_feature_preprocess_no_change(features):
    assert (
        CompetitionFeaturesPreprocessor(configuration_parameters={}).preprocess(
            features
        )
        == features
    )


@pytest.mark.parametrize(
    "value, expected", [(10, True), (9, False), (11, True), (0, False)]
)
def test_competition_feature_preprocess_bikes_bool(value, expected):
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters={"bikes_boxes_count_min": 10}
    ).preprocess(
        {CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: value}
    ) == {
        CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: expected
    }


@pytest.mark.parametrize(
    "value, expected", [(0.00000001, 0.0), (1.1111, 1.111), (4.9999, 5)]
)
def test_competition_feature_preprocess_analysis_round(value, expected):
    assert CompetitionFeaturesPreprocessor(configuration_parameters={}).preprocess(
        {
            CompetitionFeatures.ANALYSIS_GREENERY.value: value,
            CompetitionFeatures.ANALYSIS_SKY.value: value,
            CompetitionFeatures.ANALYSIS_BUILDINGS.value: value,
            CompetitionFeatures.ANALYSIS_WATER.value: value,
            CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: value,
            CompetitionFeatures.ANALYSIS_STREETS.value: value,
        }
    ) == {
        CompetitionFeatures.ANALYSIS_GREENERY.value: expected,
        CompetitionFeatures.ANALYSIS_SKY.value: expected,
        CompetitionFeatures.ANALYSIS_BUILDINGS.value: expected,
        CompetitionFeatures.ANALYSIS_WATER.value: expected,
        CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: expected,
        CompetitionFeatures.ANALYSIS_STREETS.value: expected,
    }


@pytest.mark.parametrize(
    "real_size, value_expected",
    [(10, True), (9, False), (20, True), (0, False), (None, False)],
)
@pytest.mark.parametrize(
    "comp_param_name, feature_name",
    [
        (
            "janitor_office_min_size",
            CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value,
        ),
        (
            "janitor_storage_min_size",
            CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value,
        ),
    ],
)
def test_comp_preprocessor_janitor_min_size(
    comp_param_name, feature_name, real_size, value_expected
):
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters={comp_param_name: 10}
    ).preprocess({feature_name: real_size}) == {feature_name: value_expected}


@pytest.mark.parametrize(
    "conf, feature_value, expected_pct",
    [
        ({}, {"client_id1": 3.0}, 1.0),  # Use default of 3
        ({}, {}, 0.0),  # No apartments
        ({}, {"client_id1": 1.0}, 0.0),  # Use default of 3
        ({"min_reduit_size": 1.0}, {"client_id1": 1.0}, 1.0),
        ({"min_reduit_size": 1.0}, {"client_id1": 0.95}, 1.0),  # accepts margin
        ({"salpica": 1.0}, {"client_id1": 1.0}, 0.0),  # Use default of 3, wrong conf
        (
            {"min_reduit_size": 1.0},
            {
                "client_id1": 1.0,
                "client_id2": 1.0,
                "client_id3": 0.5,
                "client_id4": 0.5,
            },
            0.5,
        ),  # half pass
    ],
)
def test_comp_preprocessor_apt_percentage_w_storage(conf, feature_value, expected_pct):
    assert CompetitionFeaturesPreprocessor(configuration_parameters=conf).preprocess(
        {CompetitionFeatures.APT_PCT_W_STORAGE.value: feature_value}
    ) == {CompetitionFeatures.APT_PCT_W_STORAGE.value: expected_pct}


@pytest.mark.parametrize(
    "conf, feature_value, expected_pct",
    [
        # Use default conf
        ({}, {}, 0.0),  # No apartments
        ({}, {"client_id1": []}, 0.0),  # No rooms
        ({}, {"client_id1": [[14, 3, 5]]}, 1.0),  # One room
        ({}, {"client_id1": [[14, 3, 5], [14, 3, 5]]}, 1.0),  # 2 rooms big
        ({}, {"client_id1": [[14, 3, 5], [12, 3, 4]]}, 1.0),  # 2 rooms big and small
        ({}, {"client_id1": [[12, 3, 4], [12, 3, 4]]}, 0.0),  # 2 rooms small
        (  # 1 big room 2 smalls
            {},
            {"client_id1": [[25, 5, 5], [12, 3, 4], [12, 3, 4]]},
            1.0,
        ),
        (  # 2 clients
            {},
            {"client_id1": [[14, 3, 5]], "client_id2": [[14, 3, 5]]},
            1.0,
        ),
        (  # 2 clients 1 doesnt pass
            {},
            {"client_id1": [[14, 3, 5]], "client_id2": [[12, 3, 4]]},
            0.5,
        ),
        # Defining configuration like for germany
        ("germany_configuration", {"client_id1": [[2.5, 2.5, 1]]}, 0),
        ("germany_configuration", {"client_id1": [[14, 3, 5]]}, 1),
        ("germany_configuration", {"client_id1": [[12, 2.95, 2.95]]}, 1),
        (
            "germany_configuration",
            {"client_id1": [[12, 2.95, 2.95], [6.25, 2.5, 2.5]]},
            0,
        ),
    ],
)
def test_comp_preprocessor_check_rooms_min_sizes(conf, feature_value, expected_pct):
    if conf:
        # That is all rooms minimum 12 meters and one side of 2.95 at least
        conf = {
            "min_room_sizes": {
                "big_room_area": 12,
                "big_room_side_small": 2.95,
                "big_room_side_big": 0,
                "small_room_area": 12,
                "small_room_side_small": 2.95,
                "small_room_side_big": 0,
            }
        }
    assert CompetitionFeaturesPreprocessor(configuration_parameters=conf).preprocess(
        {CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: feature_value}
    ) == {CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: expected_pct}


@pytest.mark.parametrize(
    "conf, feature_value, expected_pct",
    [
        # Use default conf
        ({}, {}, 0.0),  # No apartments
        ({}, {"client_id1": []}, 0.0),  # No bathrooms
        ({}, {"client_id1": [[14, 3, 5]]}, 1.0),  # One bathroom pass
        ({}, {"client_id1": [[1, 1, 1]]}, 0.0),  # One bathroom not pass
        ({}, {"client_id1": [[14, 3, 5], [14, 3, 5]]}, 1.0),  # 2 bathrooms pass
        (
            {},
            {"client_id1": [[14, 3, 5], [1, 1, 1]]},
            1.0,
        ),  # 2 bathrooms one dont pass but that is ok
        ({}, {"client_id1": [[1, 1, 1], [1, 1, 1]]}, 0.0),  # 2 bathrooms none pass
        (  # 2 clients
            {},
            {"client_id1": [[14, 3, 5]], "client_id2": [[14, 3, 5]]},
            1.0,
        ),
        (  # 2 clients 1 doesnt pass
            {},
            {"client_id1": [[14, 3, 5]], "client_id2": [[1, 1, 1]]},
            0.5,
        ),
        # # Defining configuration like for germany
        ("germany_configuration", {"client_id1": [[10, 5, 2]]}, 0.0),
        ("germany_configuration", {"client_id1": [[12, 4, 3]]}, 1.0),
        ("germany_configuration", {"client_id1": [[2.25**2, 2.25, 2.25]]}, 1.0),
        ("germany_configuration", {"client_id1": [[4, 2, 2]]}, 0.0),
        ("germany_configuration", {"client_id1": [[12, 4, 3], [1, 1, 1]]}, 1.0),
    ],
)
def test_comp_preprocessor_check_bathroom_min_sizes(conf, feature_value, expected_pct):
    if conf:
        # That is both sides should be at least (no matter about the area)
        conf = {
            "min_bathroom_sizes": {
                "min_area": 0,
                "min_small_side": 2.25,
                "min_big_side": 2.25,
            }
        }
    assert CompetitionFeaturesPreprocessor(configuration_parameters=conf).preprocess(
        {CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: feature_value}
    ) == {CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: expected_pct}


@pytest.mark.parametrize(
    "flat_types_distribution_config, actual_distribution, expected_degree_of_fulfillment",
    [
        (
            [
                {"apartment_type": [3.5, 3.0], "percentage": 0.5},
                {"apartment_type": [1.5], "percentage": 0.5},
            ],
            {3.5: 0.25, 3.0: 0.25, 1.5: 0.5},
            1.0,
        ),
        (
            [
                {"apartment_type": [3.5, 3.0], "percentage": 0.5},
                {"apartment_type": [1.5], "percentage": 0.5},
            ],
            {3.0: 0.4, 1.5: 0.6},
            0.9,
        ),
        (
            [
                {"apartment_type": [3.5, 3.0], "percentage": 0.5},
                {"apartment_type": [1.5], "percentage": 0.5},
            ],
            {5.5: 0.6, 1.5: 0.4},
            0.4,
        ),
        # With ranges
        (
            [
                {"apartment_type": [3.5], "percentage": [0, 0.5]},
                {"apartment_type": [4.5], "percentage": [0, 0.5]},
            ],
            {4.5: 0.5, 3.5: 0.5},
            1.0,
        ),
        (
            [
                {"apartment_type": [3.0, 3.5], "percentage": [0.3, 0.5]},
                {"apartment_type": [4.0, 4.5], "percentage": [0, 0.1]},
            ],
            {4.5: 0.5, 3.5: 0.5},
            0.5,
        ),
        (
            [
                {"apartment_type": [4.0, 4.5], "percentage": [1.0, 1.0]},
            ],
            {4.5: 1.0},
            1.0,
        ),
    ],
)
def test_flat_types_distribution_fulfillment(
    flat_types_distribution_config, actual_distribution, expected_degree_of_fulfillment
):
    config = {"flat_types_distribution": flat_types_distribution_config}
    assert (
        CompetitionFeaturesPreprocessor(
            configuration_parameters=config
        ).flat_types_distribution_fulfillment(feature_value=actual_distribution)
        == expected_degree_of_fulfillment
    )


@pytest.mark.parametrize(
    "flat_types_distribution_config, actual_distribution, expected_degree_of_fulfillment",
    [
        (
            [
                {"apartment_type": [3.5], "percentage": [0, 0.5]},
                {"apartment_type": [4.5], "percentage": [0, 0.5]},
            ],
            {3.5: 0.6, 4.5: 0.6},
            0.5,
        ),
        (
            [
                {"apartment_type": [3.0, 3.5], "percentage": [0.3, 0.5]},
                {"apartment_type": [4.0, 4.5], "percentage": [0, 0.1]},
            ],
            {3.5: 0.15, 4.5: 0.3},
            0.125,
        ),
        (
            [
                {"apartment_type": [4.0, 4.5], "percentage": [1.0, 1.0]},
            ],
            {4.5: 0.8},
            0.0,
        ),
        (
            [
                {"apartment_type": [4.0, 4.5], "percentage": [0.4, 0.5]},
            ],
            {4.5: 0.51},
            0.95,
        ),
    ],
)
def test_flat_types_distribution_fulfillment_ranges_acceptable_deviation(
    flat_types_distribution_config, actual_distribution, expected_degree_of_fulfillment
):
    config = {
        "flat_types_distribution": flat_types_distribution_config,
        "flat_types_distribution_acceptable_deviation": 0.2,
    }
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters=config
    ).flat_types_distribution_fulfillment(
        feature_value=actual_distribution
    ) == pytest.approx(
        expected_degree_of_fulfillment
    )


@pytest.mark.parametrize(
    "actual_distribution, expected_degree_of_fulfillment",
    [
        ([("3.5", 20), ("4.5", 20)], 0.0),
        ([("3.5", 30), ("4.5", 50)], 1.0),
        ([("5.5", 30), ("6.5", 50)], 1.0),  # No conditions for these, they pass
        ([("3.5", 29), ("4.5", 49)], 1.0),  # Tests the small margin of error allowed
        ([("3.5", 35), ("4.5", 39)], 0.5),
        ([(3.5, 35), (4.5, 39)], 0.5),  # Format testing
    ],
)
def test_flat_types_area_fulfillment(
    actual_distribution, expected_degree_of_fulfillment
):
    config = {
        "flat_types_area_fulfillment": [
            {"apartment_type": 3.5, "area": 30},
            {"apartment_type": 4.5, "area": 50},
        ],
    }
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters=config
    ).flat_types_area_fulfillment(feature_value=actual_distribution) == pytest.approx(
        expected_degree_of_fulfillment
    )


@pytest.mark.parametrize(
    "distribution_config, actual_distribution, expected_degree_of_fulfillment",
    [
        (
            [{"apartment_type": 1.5, "desired": ["BATHROOM"]}],
            {"1.5": [["BATHROOM"], ["BATHROOM"]]},
            1.0,
        ),
        (
            [
                {"apartment_type": 1.5, "desired": ["BATHROOM"]},
                {"apartment_type": 4.5, "desired": ["BATHROOM", "BATHROOM"]},
            ],
            {
                "1.5": [["BATHROOM"], ["BATHROOM"]],
                "4.5": [["BATHROOM"], ["BATHROOM", "BATHROOM"]],
            },
            0.75,
        ),
        (
            [
                {"apartment_type": 1.5, "desired": ["BATHROOM"]},
                {"apartment_type": 4.5, "desired": ["BATHROOM", "TOILET"]},
            ],
            {
                "1.5": [  # both pass as fulfill the minimum requirement
                    ["BATHROOM"],
                    ["BATHROOM", "TOILET"],
                ],
                "4.5": [  # Only 2 last pass
                    ["BATHROOM", "BATHROOM"],
                    ["BATHROOM", "TOILET"],
                    ["BATHROOM", "BATHROOM", "TOILET"],
                ],
            },
            0.8,
        ),
        (  # No desired requirement for the existing types
            [
                {"apartment_type": 1.5, "desired": ["BATHROOM"]},
            ],
            {
                "3.5": [["BATHROOM"], ["BATHROOM", "BATHROOM"]],
            },
            1.0,
        ),
        (  # No desired requirements at all
            [],
            {"3.5": [["BATHROOM"], ["BATHROOM", "BATHROOM"]]},
            1.0,
        ),
    ],
)
def test_bathroom_toilet_distribution_fulfillment(
    distribution_config, actual_distribution, expected_degree_of_fulfillment
):
    config = {"bathrooms_toilets_distribution": distribution_config}
    assert (
        CompetitionFeaturesPreprocessor(
            configuration_parameters=config
        ).bathroom_toilet_distribution_fulfillment(feature_value=actual_distribution)
        == expected_degree_of_fulfillment
    )


@pytest.mark.parametrize(
    "distribution_config, actual_distribution, expected_degree_of_fulfillment",
    [
        (
            [
                {
                    "apartment_type": 3.5,
                    "features": [{"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0}],
                    "percentage": 1.0,
                },
                {
                    "apartment_type": 4.5,
                    "features": [
                        {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0},
                        {"SHOWER": 0, "TOILET": 1, "SINK": 1, "BATHTUB": 1},
                    ],
                    "percentage": 1.0,
                },
            ],
            {
                "3.5": [
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0}
                        ],
                        "percentage": 1.0,
                    }
                ]
            },
            0.5,
        ),
        (
            [
                {
                    "apartment_type": 3.5,
                    "features": [{"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0}],
                    "percentage": 1.0,
                },
                {
                    "apartment_type": 4.5,
                    "features": [
                        {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0},
                        {"SHOWER": 0, "TOILET": 1, "SINK": 1, "BATHTUB": 1},
                    ],
                    "percentage": 1.0,
                },
            ],
            {
                "4.5": [
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0}
                        ],
                        "percentage": 1.0,
                    }
                ]
            },
            0.0,
        ),
    ],
)
def test_shower_bathtub_distribution_fulfillment(
    distribution_config, actual_distribution, expected_degree_of_fulfillment
):
    config = {"showers_bathtubs_distribution": distribution_config}
    assert (
        CompetitionFeaturesPreprocessor(
            configuration_parameters=config
        ).shower_bathtub_distribution_fulfillment(feature_value=actual_distribution)
        == expected_degree_of_fulfillment
    )


@pytest.mark.parametrize(
    "distribution, expected",
    [
        ({2.5: [10, 9, 11]}, 0.666),
        ({"2.5": [10, 9, 11]}, 0.666),
        ({"2.5": [10, 9, 11], 3.5: [20, 20, 20], 4.5: [20, 25, 20]}, 0.555),
        ({"1.5": [10], 4.5: [30]}, 1.0),
        ({"5.5": [10]}, 1.0),  # No configuration for this one
        ({}, 1.0),
    ],
)
def test_living_dining_min_req_per_apt_type(distribution, expected):
    config = {
        "living_dining_desired_sizes_per_apt_type": [
            {"apartment_type": "1.5", "desired": 5},
            {"apartment_type": "2.5", "desired": 10},
            {"apartment_type": 3.5, "desired": 20},
            {"apartment_type": "4.5", "desired": 30},
        ]
    }
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters=config
    ).living_dining_min_req_per_apt_type(feature_value=distribution) == pytest.approx(
        expected, 0.01
    )


@pytest.mark.parametrize(
    "feature_value, expected",
    [
        ({"1": 10, "2": 20}, 0.5),
    ],
)
def test_percent_bigger_than(feature_value, expected):
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters={}
    ).percent_bigger_than(
        feature_value=feature_value, minimum_threshold=12
    ) == pytest.approx(
        expected, 0.01
    )


@pytest.mark.parametrize(
    "distribution_m2, expected",
    [
        ((10, 0), True),
        ((10, 1), False),
    ],
)
def test_preprocessing_is_only_residential(distribution_m2, expected):
    assert (
        CompetitionFeaturesPreprocessor({}).is_only_residential(
            distribution_m2={
                UNIT_USAGE.RESIDENTIAL.value: distribution_m2[0],
                UNIT_USAGE.COMMERCIAL.value: distribution_m2[1],
            }
        )
        == expected
    )


@pytest.mark.parametrize(
    "distribution_m2,  expected",
    [
        (
            (8, 2),
            0.8,
        ),
        (
            (9, 1),
            0.9,
        ),
        (
            (10, 0),
            1.0,
        ),
        (
            (7, 3),
            0.7,
        ),
        (
            (0, 3),
            0.0,
        ),
    ],
)
def test_preprocessing_residential_ratio(distribution_m2, expected):
    assert CompetitionFeaturesPreprocessor({}).residential_ratio(
        distribution_m2={
            UNIT_USAGE.RESIDENTIAL.value: distribution_m2[0],
            UNIT_USAGE.COMMERCIAL.value: distribution_m2[1],
        }
    ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "apt_areas_info, expected",
    [
        (  # simple case, all pass except the 4th that is too small
            {
                "apt_1": [(6, 2, 3)],
                "apt_2": [(8, 4, 4)],
                "apt_3": [(9, 3, 3)],
                "apt_4": [(2, 2, 1)],
            },
            0.75,
        ),
        (  # case with more than one room
            {
                "apt_1": [(6, 2, 3), (8, 4, 4)],  # both room pass
                "apt_2": [
                    (8, 4, 4),
                    (2, 1, 2),
                ],  # One room pass, the other not, apt pass
                "apt_3": [(2, 1, 2), (2, 1, 2)],  # Both room fail
            },
            0.66666,
        ),
        (  # With no rooms
            {
                "apt_1": [(6, 2, 3), (8, 4, 4)],  # both rooms pass
                "apt_2": [],  # Empty, it fails
            },
            0.5,
        ),
    ],
)
def test_check_dining_table_min_size(apt_areas_info, expected):
    config = {
        "dining_area_table_min_big_side": 3,
        "dining_area_table_min_small_side": 2,
    }
    assert CompetitionFeaturesPreprocessor(
        configuration_parameters=config
    ).check_dining_table_min_size(
        areas_info_by_apartment=apt_areas_info
    ) == pytest.approx(
        expected, abs=0.01
    )
