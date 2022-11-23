import pytest

from common_utils.competition_constants import CompetitionFeatures
from common_utils.constants import UNIT_USAGE
from handlers.competition import CompetitionHandler
from handlers.db import SlamSimulationDBHandler
from handlers.db.competition.competition_client_input import (
    CompetitionManualInputDBHandler,
)
from handlers.db.competition.competition_features_db_handler import (
    CompetitionFeaturesDBHandler,
)
from handlers.db.competition.competition_handler import CompetitionDBHandler


@pytest.mark.parametrize(
    "net_area, prices_are_rent, ph_net_area, ph_rent_price, ph_sale_price, expected_net_area, expected_ph_gross_price",
    [
        (100, True, 1000, 100, None, 1000, 100000),
        (100, True, None, 100, None, 100, 10000),
        (100, True, None, None, None, 100, None),
        (100, True, 10000, None, None, 10000, None),
        (100, True, 1000, None, 100, 1000, None),
        (100, False, 1000, None, 100, 1000, 100000),
    ],
)
def test_get_competitors_units(
    mocker,
    net_area,
    ph_net_area,
    expected_net_area,
    ph_rent_price,
    ph_sale_price,
    expected_ph_gross_price,
    prices_are_rent,
):
    from handlers import SlamSimulationHandler
    from handlers.db import CompetitionDBHandler, UnitDBHandler

    fake_competitor_ids = [1, 2, 3]
    fake_competition_id = 77
    fake_units_info = [
        {
            "id": 1,
            "client_id": "A",
            "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
            "ph_net_area": ph_net_area,
            "ph_final_gross_rent_annual_m2": ph_rent_price,
            "ph_final_sale_price_m2": ph_sale_price,
        },
        # janitor unit to be excluded
        {
            "id": 2,
            "client_id": "janitor_",
            "unit_usage": UNIT_USAGE.JANITOR.name,
            "ph_net_area": ph_net_area,
            "ph_final_gross_rent_annual_m2": ph_rent_price,
            "ph_final_sale_price_m2": ph_sale_price,
        },
        # gewerbe unit to be excluded
        {
            "id": 3,
            "client_id": "gewerbe_",
            "unit_usage": UNIT_USAGE.COMMERCIAL.name,
            "ph_net_area": ph_net_area,
            "ph_final_gross_rent_annual_m2": ph_rent_price,
            "ph_final_sale_price_m2": ph_sale_price,
        },
        # placeholder unit to be excluded
        {
            "id": 4,
            "client_id": "placeholder",
            "unit_usage": UNIT_USAGE.PLACEHOLDER.name,
            "ph_net_area": ph_net_area,
            "ph_final_gross_rent_annual_m2": ph_rent_price,
            "ph_final_sale_price_m2": ph_sale_price,
        },
    ] * 2
    mocker.patch.object(
        UnitDBHandler, UnitDBHandler.find.__name__, return_value=fake_units_info
    )
    mocker.patch.object(
        SlamSimulationHandler,
        SlamSimulationHandler.get_latest_results.__name__,
        return_value={
            1: [{"UnitBasics.net-area": net_area}],
            2: [{"UnitBasics.net-area": net_area}],
        },
    )
    mocker.patch.object(
        CompetitionDBHandler,
        CompetitionDBHandler.get_by.__name__,
        return_value={
            "competitors": fake_competitor_ids,
            "configuration_parameters": {"fake_params"},
            "red_flags_enabled": True,
            "prices_are_rent": prices_are_rent,
        },
    )

    res = CompetitionHandler(competition_id=fake_competition_id).get_competitors_units()

    assert res == [
        {
            "competitor_id": competitor_id,
            "units": [
                {
                    "client_id": "A",
                    "net_area": expected_net_area,
                    "ph_gross_price": expected_ph_gross_price,
                }
            ],
        }
        for competitor_id in fake_competitor_ids
    ]


class TestGetCompetitorFeatureValues:
    fake_competitor_id = 9999

    @pytest.mark.parametrize(
        "automated_features, manual_features, features_selected, expected_feature_values",
        [
            ({}, [], [], {f.value: 0.0 for f in CompetitionFeatures}),
            (
                {},
                [],
                [
                    CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR,
                    CompetitionFeatures.CAR_PARKING_SPACES,
                ],
                {
                    CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 0.0,
                    CompetitionFeatures.CAR_PARKING_SPACES.value: 0.0,
                },
            ),
            (
                {CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 99999},
                [
                    {
                        "competitor_id": fake_competitor_id,
                        "features": {CompetitionFeatures.CAR_PARKING_SPACES.value: 70},
                    }
                ],
                [],
                {
                    **{f.value: 0.0 for f in CompetitionFeatures},
                    CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 99999,
                    CompetitionFeatures.CAR_PARKING_SPACES.value: 70,
                },
            ),
            (
                {CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 99999},
                [
                    {
                        "competitor_id": fake_competitor_id,
                        "features": {CompetitionFeatures.CAR_PARKING_SPACES.value: 70},
                    }
                ],
                [
                    CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR,
                    CompetitionFeatures.CAR_PARKING_SPACES,
                ],
                {
                    CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 99999,
                    CompetitionFeatures.CAR_PARKING_SPACES.value: 70,
                },
            ),
        ],
    )
    def test_get_competitor_feature_values(
        self,
        mocker,
        automated_features,
        manual_features,
        features_selected,
        expected_feature_values,
    ):
        fake_config = {"some-fake-config"}

        mocker.patch.object(
            CompetitionManualInputDBHandler, "find", return_value=manual_features
        )
        mocker.patch.object(
            CompetitionFeaturesDBHandler,
            "get_by",
            return_value={"results": automated_features},
        )
        mocker.patch.object(SlamSimulationDBHandler, "get_latest_run_id")
        mocker.patch.object(
            CompetitionDBHandler,
            "get_by",
            return_value={
                "id": mocker.ANY,
                "red_flags_enabled": False,
                "features_selected": features_selected,
                "configuration_parameters": fake_config,
            },
        )

        feature_values = CompetitionHandler(
            competition_id=mocker.ANY
        )._get_competitor_feature_values(competitor_id=self.fake_competitor_id)

        assert feature_values == expected_feature_values
