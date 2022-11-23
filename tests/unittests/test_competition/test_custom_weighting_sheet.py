import json

import pytest

from common_utils.competition_constants import CompetitionFeatures
from handlers.competition import CompetitionHandler
from handlers.competition.custom_weighting_sheet import CustomWeightingSheetDataProvider
from handlers.db import ClientDBHandler, SiteDBHandler
from handlers.db.competition.competition_handler import CompetitionDBHandler


class TestCustomWeightingSheetDataprovider:
    @pytest.fixture
    def fake_competitors(self):
        return [1, 2, 3]

    @pytest.fixture
    def expected_weighting_data(self, fixtures_path):
        with open(
            fixtures_path.joinpath(
                "competition/custom_weighting_sheet/weighting_data.json"
            )
        ) as f:
            return json.load(f)

    @pytest.fixture
    def expected_scores_data(self, fixtures_path):
        with open(
            fixtures_path.joinpath("competition/custom_weighting_sheet/score_data.json")
        ) as f:
            return json.load(f)

    @pytest.fixture
    def expected_features_data(self, fixtures_path):
        with open(
            fixtures_path.joinpath(
                "competition/custom_weighting_sheet/features_data.json"
            )
        ) as f:
            return json.load(f)

    @pytest.fixture
    def mocked_db_entities(self, mocker, fake_competitors):
        def _internal(
            features_selected=None, competition_name=None, client_name="Fake Client"
        ):
            mocker.patch.object(
                CompetitionDBHandler,
                "get_by",
                return_value={
                    "client_id": "Fake ID",
                    "name": competition_name,
                    "configuration_parameters": {"some": "fake"},
                    "red_flags_enabled": False,
                    "competitors": fake_competitors,
                    "features_selected": features_selected or CompetitionFeatures,
                },
            )
            mocker.patch.object(
                SiteDBHandler,
                "find_in",
                return_value=[
                    {"id": fake_site, "name": f"Site {fake_site}"}
                    for fake_site in fake_competitors
                ],
            )
            mocker.patch.object(
                ClientDBHandler,
                "get_by",
                return_value={"name": client_name},
            )

        return _internal

    @pytest.mark.freeze_time("2021-12-31")
    @pytest.mark.parametrize(
        "name, expected_title",
        zip(
            ["happy", "HI-HO", "BO HO"],
            [
                "Gewichtungstabelle_happy_20211231",
                "Gewichtungstabelle_HI_HO_20211231",
                "Gewichtungstabelle_BO_HO_20211231",
            ],
        ),
    )
    def test_get_title(self, name, expected_title, mocker):
        mocker.patch.object(
            CompetitionDBHandler,
            "get_by",
            return_value={
                "name": name,
                "configuration_parameters": {"some": "fake"},
                "red_flags_enabled": False,
            },
        )
        assert (
            CustomWeightingSheetDataProvider(competition_id=mocker.ANY).get_title()
            == expected_title
        )

    def test_get_score_data(
        self, mocker, mocked_db_entities, fake_competitors, expected_scores_data
    ):
        mocked_db_entities(
            features_selected=[CompetitionFeatures.NOISE_INSULATED_ROOMS]
        )
        mocker.patch.object(
            CompetitionHandler,
            "compute_competitors_scores",
            return_value=[
                {
                    "id": fake_site,
                    CompetitionFeatures.NOISE_INSULATED_ROOMS.value: fake_score,
                }
                for fake_site, fake_score in zip(fake_competitors, [0, 5, 10])
            ],
        )
        assert (
            CustomWeightingSheetDataProvider(
                competition_id=mocker.ANY
            ).get_scores_data()
            == expected_scores_data
        )

    def test_get_weighting_data(
        self,
        mocker,
        mocked_db_entities,
        expected_weighting_data,
        fixtures_path,
        update_fixture=False,
    ):
        mocked_db_entities()
        data = CustomWeightingSheetDataProvider(
            competition_id=mocker.ANY
        ).get_weighting_data()
        if update_fixture:
            with open(
                fixtures_path.joinpath(
                    "competition/custom_weighting_sheet/weighting_data.json"
                ),
                "w",
            ) as f:
                json.dump(data, f, indent=1)
        assert data == expected_weighting_data

    def test_get_features_data(
        self, mocker, mocked_db_entities, fake_competitors, expected_features_data
    ):
        mocked_db_entities(
            features_selected=[CompetitionFeatures.NOISE_INSULATED_ROOMS]
        )
        mocker.patch.object(
            CompetitionHandler,
            "get_competitors_features_values",
            return_value=[
                {
                    "id": fake_site,
                    CompetitionFeatures.NOISE_INSULATED_ROOMS.value: fake_feature_value,
                }
                for fake_site, fake_feature_value in zip(fake_competitors, [0, 5, 10])
            ],
        )
        assert (
            CustomWeightingSheetDataProvider(
                competition_id=mocker.ANY
            ).get_features_data()
            == expected_features_data
        )

    @pytest.mark.freeze_time("2021-12-31")
    def test_get_header(self, mocked_db_entities, mocker):
        mocked_db_entities(competition_name="Fake Competition", client_name="Client 1")
        assert CustomWeightingSheetDataProvider(
            competition_id=mocker.ANY
        ).get_header() == (
            "Gewichtungstabelle\n"
            "Client: Client 1\n"
            "Project: Fake Competition\n"
            "Date: 31.12.2021"
        )
