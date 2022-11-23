from collections import Counter
from http import HTTPStatus

import pytest
from deepdiff import DeepDiff

from common_utils.competition_constants import RED_FLAGS_FEATURES, CompetitionFeatures
from common_utils.constants import CURRENCY, USER_ROLE
from handlers.competition.utils import CompetitionCategoryTreeGenerator
from handlers.db import CompetitionDBHandler, UnitDBHandler
from slam_api.apis.competition.endpoints import (
    AdminCompetitionView,
    AdminCompetitionViewCollection,
    CompetitionClientInputView,
    CompetitionInfo,
    CompetitionParametersView,
    CompetitionWeightsView,
    competition_app,
    get_categories,
    get_competition_categories,
    get_competitions,
    get_competitors_scores,
    get_competitors_units,
)
from tests.constants import USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.utils import login_with


@pytest.fixture
def fix_weights():
    return {
        "architecture_usage": 0.27,
        "architecture_room_programme": 0.38,
        "environmental": 0.2,
        "further_key_figures": 0.15,
    }


@pytest.fixture
def login_competition_admin_linked_to_client_db(client, client_db):
    login_with(
        client,
        {**USERS[USER_ROLE.COMPETITION_ADMIN.name], "client_id": client_db["id"]},
    )


@pytest.fixture
def competition_2_competitors_default(fix_weights, client_db, make_sites):
    site_1, site_2 = make_sites(client_db, client_db)
    return CompetitionDBHandler.add(
        competitors=[site_1["id"], site_2["id"]],
        weights=fix_weights,
        client_id=client_db["id"],
        currency=CURRENCY.EUR.value,
    )


@pytest.mark.parametrize(
    "conf_parameter, expected_response",
    [
        ({}, {}),
        [{"flat_types_distribution": []}] * 2,
        [
            {
                "flat_types_distribution": [
                    {"apartment_type": [1.5], "percentage": 0.5},
                    {"apartment_type": [2.5], "percentage": 0.5},
                    {"apartment_type": [3, 3.5], "percentage": [0.2, 0.5]},
                ]
            }
        ]
        * 2,
    ],
)
def test_competition_parameters_get(
    site,
    client,
    conf_parameter,
    expected_response,
    fix_weights,
    login_competition_admin_linked_to_client_db,
):
    # Given competition with given parameters
    comp = CompetitionDBHandler.add(
        competitors=[site["id"]],
        weights=fix_weights,
        configuration_parameters=conf_parameter,
        client_id=site["client_id"],
    )

    url = get_address_for(
        blueprint=competition_app,
        use_external_address=False,
        view_function=CompetitionParametersView,
        competition_id=comp["id"],
    )

    response = client.get(url)
    assert response.json == expected_response


@pytest.mark.parametrize(
    "put_conf_parameter, expected_response, expected_code",
    [
        ({"unit_type_programme": None}, "", HTTPStatus.UNPROCESSABLE_ENTITY),
        ({"foobar": None}, "", HTTPStatus.UNPROCESSABLE_ENTITY),
        (
            {"flat_types_distribution": [{"apartment_typO": [1.5], "percAntage": 0.5}]},
            "",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            {"flat_types_distribution": [{"apartment_type": [1.4], "percentage": 0.5}]},
            "",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            {"flat_types_distribution": [{"apartment_type": [5], "percentage": 1.1}]},
            "",
            HTTPStatus.UNPROCESSABLE_ENTITY,
        ),
        (
            *[
                {
                    "flat_types_distribution": [
                        {"apartment_type": [1.5], "percentage": 0.5},
                        {"apartment_type": [2.5], "percentage": 0.5},
                        {"apartment_type": [3, 3.5], "percentage": [0.2, 0.5]},
                    ]
                }
            ]
            * 2,
            HTTPStatus.OK,
        ),
    ],
)
def test_competition_parameters_put(
    client,
    put_conf_parameter,
    expected_code,
    expected_response,
    competition_2_competitors_default,
    login_competition_admin_linked_to_client_db,
):
    # when putting parameters
    url = get_address_for(
        blueprint=competition_app,
        use_external_address=False,
        view_function=CompetitionParametersView,
        competition_id=competition_2_competitors_default["id"],
    )
    response = client.put(url, json=put_conf_parameter)

    # then
    assert response.status_code == expected_code, response.json
    if expected_code != HTTPStatus.UNPROCESSABLE_ENTITY:
        assert response.json == expected_response


class TestCompetitionWeightsView:
    def test_get_competition(
        self,
        client,
        competition_2_competitors_default,
        fix_weights,
        login_competition_admin_linked_to_client_db,
    ):
        url = get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=CompetitionInfo,
            competition_id=competition_2_competitors_default["id"],
        )

        response = client.get(url)

        expected_response = {
            "name": competition_2_competitors_default["name"],
            "configuration_parameters": competition_2_competitors_default[
                "configuration_parameters"
            ],
            "weights": fix_weights,
            "currency": CURRENCY.EUR.value,
            "prices_are_rent": True,
        }

        assert response.status_code == HTTPStatus.OK, response.json
        assert response.json == expected_response

    def test_put_competition_weights(
        self,
        client,
        competition_2_competitors_default,
        login_competition_admin_linked_to_client_db,
    ):
        url = get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=CompetitionWeightsView,
            competition_id=competition_2_competitors_default["id"],
        )
        new_values = {
            "architecture_usage": 0.96,
            "architecture_room_programme": 0.01,
            "environmental": 0.02,
            "further_key_figures": 0.01,
        }
        response = client.put(url, json=new_values)

        assert response.status_code == HTTPStatus.OK, response.json
        assert response.json == new_values


class TestCompetitionClientInputView:
    def test_put_and_get_manual_input(
        self,
        client,
        competition_with_fake_feature_values,
        login_competition_admin_linked_to_client_db,
    ):
        url = get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=CompetitionClientInputView,
            competition_id=competition_with_fake_feature_values["id"],
            competitor_id=competition_with_fake_feature_values["competitors"][0],
        )
        new_data = {
            CompetitionFeatures.RESIDENTIAL_USE.value: False,
            CompetitionFeatures.DRYING_ROOM_SIZE.value: True,
            CompetitionFeatures.JANITOR_OFFICE_LIGHT.value: True,
            CompetitionFeatures.PRAMS_ROOM_BARRIER_FREE_ACCESS.value: False,
            CompetitionFeatures.BIKE_BOXES_DIMENSIONS.value: False,
            CompetitionFeatures.BIKE_BOXES_POWER_SUPPLY.value: True,
            CompetitionFeatures.PRAMS_AND_BIKES_CLOSE_TO_ENTRANCE.value: True,
            CompetitionFeatures.CAR_PARKING_SPACES.value: False,
            CompetitionFeatures.TWO_WHEELS_PARKING_SPACES.value: True,
            CompetitionFeatures.BIKE_PARKING_SPACES.value: False,
            CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.value: False,
            CompetitionFeatures.KITCHEN_ELEMENTS_REQUIREMENT.value: 0.1,
            CompetitionFeatures.ENTRANCE_WARDROBE_ELEMENT_REQUIREMENT.value: 0.82,
            CompetitionFeatures.BEDROOM_WARDROBE_ELEMENT_REQUIREMENT.value: 0.0,
            CompetitionFeatures.SINK_SIZES_REQUIREMENT.value: 1,
        }
        response = client.put(url, json=new_data)
        assert response.status_code == HTTPStatus.OK, response.json
        assert response.json["features"] == new_data

        response = client.get(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=CompetitionClientInputView,
                competition_id=competition_with_fake_feature_values["id"],
                competitor_id=competition_with_fake_feature_values["competitors"][0],
            )
        )

        assert response.status_code == HTTPStatus.OK, response.json
        assert response.json["features"] == new_data

    def test_put_manual_input_invalid(
        self,
        client,
        competition_with_fake_feature_values,
        login_competition_admin_linked_to_client_db,
    ):
        url = get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=CompetitionClientInputView,
            competition_id=competition_with_fake_feature_values["id"],
            competitor_id=competition_with_fake_feature_values["competitors"][0],
        )
        new_data = {CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: "foo"}
        response = client.put(url, json=new_data)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json


def test_get_competitors_scores(
    client,
    competition_with_fake_feature_values,
    expected_competition_scores_site_2,
    competition_first_client_features_input,
    expected_competition_scores_site_1_w_manual_input,
):
    url = get_address_for(
        blueprint=competition_app,
        use_external_address=False,
        view_function=get_competitors_scores,
        competition_id=competition_with_fake_feature_values["id"],
    )
    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    results = response.json
    for result in results:
        result.pop("id")

    expected_competition_scores_site_2.pop("id")

    expected = [
        expected_competition_scores_site_1_w_manual_input,
        expected_competition_scores_site_2,
    ]
    assert not DeepDiff(
        expected,
        results,
        ignore_order=True,
        significant_digits=3,
    )


def test_get_competitors_scores_as_another_client_forbidden(
    client,
    competition_with_fake_feature_values,
    expected_competition_scores_site_2,
    competition_first_client_features_input,
    expected_competition_scores_site_1_w_manual_input,
    client_db,
    make_clients,
):
    (client_a,) = make_clients()
    user_info = {
        "login": "competition_admin",
        "password": "competition_admin",
        "roles": [USER_ROLE.COMPETITION_ADMIN],
        "email": "wrong_user@fake.com",
        "client_id": client_a["id"],
    }
    login_with(client=client, user=user_info)
    url = get_address_for(
        blueprint=competition_app,
        use_external_address=False,
        view_function=get_competitors_scores,
        competition_id=competition_with_fake_feature_values["id"],
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_competition_categories_tagged(
    client,
    login_competition_admin_linked_to_client_db,
    competition_with_fake_feature_values,
):
    response = client.get(
        get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=get_competition_categories,
            competition_id=competition_with_fake_feature_values["id"],
        )
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        response.json
        == CompetitionCategoryTreeGenerator(red_flags_enabled=True).get_category_tree()
    )
    counter = Counter(
        [
            leaf_level.get("archilyse", False)
            for category in response.json
            for sub_section in category["sub_sections"]
            for leaf_level in sub_section["sub_sections"]
        ]
    )
    expected_archilyse = 12
    expected_program = 48
    assert counter == {
        True: expected_archilyse,
        False: expected_program,
    }
    # expect 8 red flags
    red_flags_count = sum(
        [
            1 if leaf_level.get("red_flag", False) else 0
            for category in response.json
            for sub_section in category["sub_sections"]
            for leaf_level in sub_section["sub_sections"]
        ]
    )
    assert red_flags_count == len(RED_FLAGS_FEATURES)


def test_competition_categories_tagged_no_red_flags(
    client,
    client_db,
    competition_configuration,
    login_competition_admin_linked_to_client_db,
):
    comp = CompetitionDBHandler.add(
        competitors=[],
        name="Some competition",
        client_id=client_db["id"],
        weights={},
        configuration_parameters=competition_configuration,
        red_flags_enabled=False,
    )

    response = client.get(
        get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=get_competition_categories,
            competition_id=comp["id"],
        )
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        response.json
        == CompetitionCategoryTreeGenerator(red_flags_enabled=False).get_category_tree()
    )
    # expect 0 red flags
    red_flags_count = sum(
        [
            1 if leaf_level.get("red_flag", False) else 0
            for category in response.json
            for sub_section in category["sub_sections"]
            for leaf_level in sub_section["sub_sections"]
        ]
    )
    assert red_flags_count == 0


def test_competition_categories_all(
    client,
    login_competition_admin_linked_to_client_db,
    competition_with_fake_feature_values,
):
    response = client.get(
        get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=get_categories,
        )
    )
    assert response.status_code == HTTPStatus.OK
    assert (
        response.json
        == CompetitionCategoryTreeGenerator(red_flags_enabled=True).get_category_tree()
    )


def test_get_competitors_units(
    client,
    competition_with_fake_feature_values,
    login_competition_admin_linked_to_client_db,
):
    # given
    fake_price = 1000
    competitors = competition_with_fake_feature_values["competitors"]
    units_ids_by_competitor = {
        site_id: list(UnitDBHandler.find_ids(site_id=site_id))
        for site_id in competitors
    }

    UnitDBHandler.bulk_update(
        ph_final_gross_rent_annual_m2={
            unit_id: fake_price
            for unit_ids in units_ids_by_competitor.values()
            for unit_id in unit_ids
        },
    )
    # when
    response = client.get(
        get_address_for(
            blueprint=competition_app,
            use_external_address=False,
            view_function=get_competitors_units,
            competition_id=competition_with_fake_feature_values["id"],
        )
    )

    fixed_net_area = 80.51168821392893
    # then
    assert response.status_code == HTTPStatus.OK
    assert not DeepDiff(
        [
            {
                "competitor_id": competitors[0],
                "units": [
                    {
                        "ph_gross_price": fake_price * fixed_net_area,
                        "net_area": fixed_net_area,
                    }
                ],
            },
            {
                "competitor_id": competitors[1],
                "units": [
                    {
                        "ph_gross_price": fake_price * fixed_net_area,
                        "net_area": fixed_net_area,
                    }
                ],
            },
        ],
        response.json,
        ignore_order=True,
        exclude_regex_paths=r"root\[\d+\]\['units']\[\d+\]\['client_id']",
    )


class TestGetCompetitions:
    @staticmethod
    @pytest.fixture
    def create_4_competitions(make_clients, client_db, fix_weights):
        CompetitionDBHandler.add(
            competitors=[], weights=fix_weights, client_id=client_db["id"]
        )
        for additional_client in make_clients(3):
            CompetitionDBHandler.add(
                competitors=[], weights=fix_weights, client_id=additional_client["id"]
            )

    @staticmethod
    @login_as([USER_ROLE.ADMIN.name])
    def test_get_competitions_as_admin(login, client, create_4_competitions):
        response = client.get(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=get_competitions,
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 4

    @staticmethod
    def test_get_competitions_as_competition_user(
        client,
        create_4_competitions,
        login_competition_admin_linked_to_client_db,
    ):
        response = client.get(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=get_competitions,
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1


class TestAdminCompetitionViewCollection:
    @login_as([USER_ROLE.ADMIN.name])
    def test_get(self, login, client, client_db, competition_with_fake_feature_values):
        response = client.get(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionViewCollection,
                client_id=client_db["id"],
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert not DeepDiff(
            response.json, [competition_with_fake_feature_values], ignore_order=True
        )

    @login_as([USER_ROLE.ADMIN.name])
    def test_post(self, login, client, client_db):
        values_to_post = dict(
            name="funny competition",
            red_flags_enabled=True,
            currency="EUR",
            client_id=client_db["id"],
        )
        response = client.post(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionViewCollection,
            ),
            json=values_to_post,
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json == {**response.json, **values_to_post}
        assert CompetitionDBHandler.get_by(**values_to_post) == response.json

    @pytest.mark.parametrize("method", ["get", "post"])
    @login_as([role.name for role in USER_ROLE if role != USER_ROLE.ADMIN])
    def test_endpoints_are_blocked_for_non_admins(
        self, login, client, client_db, method
    ):
        response = getattr(client, method)(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionViewCollection,
                client_id=client_db["id"],
            )
        )
        assert response.json == {"msg": "Access to this resource is forbidden."}
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestAdminCompetitionView:
    @login_as([USER_ROLE.ADMIN.name])
    def test_get(self, login, client, competition_with_fake_feature_values):
        response = client.get(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionView,
                competition_id=competition_with_fake_feature_values["id"],
            )
        )
        assert not DeepDiff(
            response.json, competition_with_fake_feature_values, ignore_order=True
        )
        assert response.status_code == HTTPStatus.OK

    @login_as([USER_ROLE.ADMIN.name])
    def test_put_compe(self, login, client, competition_with_fake_feature_values):
        values_to_patch = dict(
            name="funny competition",
            red_flags_enabled=True,
            currency="EUR",
            features_selected=[CompetitionFeatures.TWO_WHEELS_PARKING_SPACES.name],
        )
        response = client.put(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionView,
                competition_id=competition_with_fake_feature_values["id"],
            ),
            json=values_to_patch,
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json == {**response.json, **values_to_patch}
        db_competition = CompetitionDBHandler.get_by(
            id=competition_with_fake_feature_values["id"],
        )
        db_competition["features_selected"] = [
            f.name for f in db_competition["features_selected"]
        ]
        assert db_competition == response.json

    @login_as([USER_ROLE.ADMIN.name])
    def test_delete(self, login, client, competition_with_fake_feature_values):
        response = client.delete(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionView,
                competition_id=competition_with_fake_feature_values["id"],
            ),
        )
        assert response.status_code == HTTPStatus.NO_CONTENT
        assert not CompetitionDBHandler.exists(
            id=competition_with_fake_feature_values["id"]
        )

    @pytest.mark.parametrize("method", ["get", "put", "delete"])
    @login_as([role.name for role in USER_ROLE if role != USER_ROLE.ADMIN])
    def test_endpoints_are_blocked_for_non_admins(
        self, login, client, client_db, method, competition_with_fake_feature_values
    ):
        response = getattr(client, method)(
            get_address_for(
                blueprint=competition_app,
                use_external_address=False,
                view_function=AdminCompetitionView,
                competition_id=competition_with_fake_feature_values["id"],
            )
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json == {"msg": "Access to this resource is forbidden."}
