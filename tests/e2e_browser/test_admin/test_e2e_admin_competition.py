from typing import List, Optional

import pytest

from common_utils.competition_constants import CompetitionFeatures
from common_utils.constants import USER_ROLE
from handlers.db.competition.competition_handler import CompetitionDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import (
    admin_click_delete_and_assert_successful,
    admin_click_save_and_assert_successful,
    make_login,
    navigate_to_child,
    safe_wait_for_table_and_expand_columns,
)
from tests.e2e_browser.utils_editor import clear_input


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url, USER_ROLE.ADMIN.name)


@pytest.fixture
def navigate_to_competitions_table(admin_url, browser):
    def f(client_id, expected_rows=None):
        browser.visit(admin_url + "/clients")
        safe_wait_for_table_and_expand_columns(
            browser, "clients_table", expected_rows=1
        )
        navigate_to_child(browser, f"/competitions?client_id={client_id}")
        if expected_rows:
            safe_wait_for_table_and_expand_columns(
                browser, "competitions_table", expected_rows=expected_rows
            )

    return f


def fill_competition_form(
    browser,
    name: Optional[str] = None,
    red_flags_enabled: Optional[bool] = None,
    currency: Optional[str] = None,
    competitors: Optional[List[int]] = None,
):
    if name is not None:
        browser.fill(name="name", value=name)
        clear_input(browser)
        browser.fill(name="name", value=name)

    if red_flags_enabled is not None:
        red_flags_enabled_dropdown = browser.find_by_xpath(
            "//*[contains(@class, 'form-select-red_flags_enabled')]",
            wait_time=TIME_TO_WAIT,
        ).first
        red_flags_enabled_dropdown.click()
        browser.find_by_xpath(
            f"//div[(text()='{str(red_flags_enabled).upper()}')]",
            wait_time=TIME_TO_WAIT,
        ).first.click()

    if currency is not None:
        currency_dropdown = browser.find_by_xpath(
            "//*[contains(@class, 'form-select-currency')]", wait_time=TIME_TO_WAIT
        ).first
        currency_dropdown.click()
        browser.find_by_xpath(
            f"//div[(text()='{currency}')]", wait_time=TIME_TO_WAIT
        ).first.click()

    if competitors is not None:
        # open the multiselect
        competitors_dropdown = browser.find_by_xpath(
            "//*[contains(@class, 'form-select-competitors')]", wait_time=TIME_TO_WAIT
        ).first
        competitors_dropdown.click()

        # first unselect all options
        for option in browser.find_by_xpath(
            "//*[contains(@class, 'MuiListItem-button') and @aria-selected='true']",
            wait_time=TIME_TO_WAIT,
        ):
            option.click()

        # then select the desired options
        for competitor_id in competitors:
            browser.find_by_xpath(
                f"//*[contains(@class, 'MuiListItem-button') and @data-value='{competitor_id}']",
                wait_time=TIME_TO_WAIT,
            ).first.click()

        # then click somewhere else to close the multiselect
        browser.find_by_xpath("//body").first.click()


def test_competition_add(
    admin_url, browser, navigate_to_competitions_table, client_db, site
):
    competitions_new_values = [
        dict(
            name="competition 1",
            currency="EUR",
            red_flags_enabled=False,
        ),
        dict(
            name="competition 2",
            currency="CHF",
            red_flags_enabled=True,
            competitors=[site["id"]],
        ),
    ]
    for expected_rows, new_values in enumerate(competitions_new_values, start=1):
        browser.visit(f"{admin_url}/competition/new?client_id={client_db['id']}")

        # first add a competition without competitors
        fill_competition_form(browser=browser, **new_values)
        admin_click_save_and_assert_successful(browser)

        competitors = new_values.pop("competitors", [])
        competition = CompetitionDBHandler.get_by(**new_values)
        assert competition["competitors"] == competitors
        navigate_to_competitions_table(
            client_id=client_db["id"], expected_rows=expected_rows
        )


def test_competition_edit(
    admin_url,
    browser,
    navigate_to_competitions_table,
    competition_with_fake_feature_values,
):
    # first edit an existing competition ...
    navigate_to_competitions_table(
        client_id=competition_with_fake_feature_values["client_id"], expected_rows=0
    )
    browser.find_by_text("Edit").first.click()

    competition_new_values = [
        dict(competitors=[]),
        dict(
            name="competition 1",
            currency="EUR",
            red_flags_enabled=False,
        ),
        dict(
            name="competition 2",
            currency="CHF",
            red_flags_enabled=True,
            competitors=competition_with_fake_feature_values["competitors"][1:],
        ),
    ]
    for new_values in competition_new_values:
        fill_competition_form(browser=browser, **new_values)
        admin_click_save_and_assert_successful(browser)
        updated_competition = CompetitionDBHandler.get_by(
            id=competition_with_fake_feature_values["id"]
        )
        assert updated_competition == {**updated_competition, **new_values}

    # then delete it
    admin_click_delete_and_assert_successful(browser=browser)
    assert not CompetitionDBHandler.exists(
        id=competition_with_fake_feature_values["id"],
    )
    navigate_to_competitions_table(
        client_id=competition_with_fake_feature_values["client_id"], expected_rows=0
    )


def test_competition_select_features(
    admin_url,
    browser,
    navigate_to_competitions_table,
    competition_with_fake_feature_values,
):
    features = CompetitionDBHandler.get_by(
        id=competition_with_fake_feature_values["id"]
    )["features_selected"]

    assert not features
    navigate_to_competitions_table(
        client_id=competition_with_fake_feature_values["client_id"], expected_rows=0
    )
    browser.find_by_text("Features Selection").first.click()
    # Deselect one feature
    browser.find_by_name(
        f"{CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.name}"
    ).click()
    admin_click_save_and_assert_successful(browser)
    features = CompetitionDBHandler.get_by(
        id=competition_with_fake_feature_values["id"]
    )["features_selected"]

    assert len(features) != 0
    assert "CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.name" not in features


@pytest.fixture
def navigate_to_competition_config_form(admin_url, browser):
    def f(competition_id):
        browser.visit(admin_url + f"/competition/{competition_id}/config")

    return f


def fill_form(browser, name, value):
    browser.fill(name=name, value=str(value))
    clear_input(browser)
    browser.fill(name=name, value=str(value))


def click_tree_element(browser, name):
    browser.find_by_xpath(
        f"//div[(text()='{name}')]",
        wait_time=TIME_TO_WAIT,
    ).first.click()


def test_competition_edit_configuration(
    browser, competition_with_fake_feature_values, navigate_to_competition_config_form
):
    navigate_to_competition_config_form(
        competition_id=competition_with_fake_feature_values["id"]
    )

    # fill form by feature
    path_and_form_values = [
        (
            ["Usage", "Residential Area"],
            {
                "residential_ratio.desired_ratio": 1.0,
                "residential_ratio.acceptable_deviation": 0.1,
            },
        ),
        (
            ["Generosity", "Minimum room size"],
            {
                "min_room_sizes.big_room_side_small": 1.0,
                "min_room_sizes.big_room_side_big": 2.0,
                "min_room_sizes.big_room_area": 2.0,
                "min_room_sizes.small_room_side_small": 2.0,
                "min_room_sizes.small_room_side_big": 3.0,
                "min_room_sizes.small_room_area": 6.0,
            },
        ),
        (
            ["Storage (in Apartment)", "Availability Storage"],
            {
                "min_reduit_size": 77.0,
            },
        ),
        (
            ["Janitor storeroom", "Size Janitor Storeroom"],
            {
                "janitor_storage_min_size": 99.0,
            },
        ),
        (
            ["Janitor Office", "Size Janitor Office"],
            {
                "janitor_office_min_size": 66.0,
            },
        ),
        (
            ["Disability Accessibility", "Handicapped Accessible Areas"],
            {
                "min_corridor_size": 1.9,
            },
        ),
        (
            ["Disability Accessibility", "Size Bathroom"],
            {
                "min_bathroom_sizes.min_small_side": 1.0,
                "min_bathroom_sizes.min_big_side": 2.0,
                "min_bathroom_sizes.min_area": 2.0,
            },
        ),
        (
            ["Bike boxes", "Quantity Bike Boxes"],
            {
                "bikes_boxes_count_min": 7,
            },
        ),
    ]

    # expand categories
    for category_name in ["Architecture – Overview", "Architecture – Project Specific"]:
        click_tree_element(browser, category_name)

    # navigate to form, fill form values and create expected results
    expected_configuration_parameters = competition_with_fake_feature_values[
        "configuration_parameters"
    ]
    for path_to_feature, form_values in path_and_form_values:
        for element in path_to_feature:
            click_tree_element(browser, element)

        for key_dot_notation, value in form_values.items():
            fill_form(browser, key_dot_notation, value)

            # create expected result
            dict_to_update = expected_configuration_parameters
            keys = key_dot_notation.split(".")
            last_key = keys.pop()
            for key in keys:
                dict_to_update = expected_configuration_parameters.setdefault(key, {})
            # percentages are submitted as decimals
            if key_dot_notation in (
                "residential_ratio.desired_ratio",
                "residential_ratio.acceptable_deviation",
            ):
                value /= 100
            dict_to_update[last_key] = value

    admin_click_save_and_assert_successful(browser)

    # check values in db
    new_configuration_parameters = CompetitionDBHandler.get_by(
        id=competition_with_fake_feature_values["id"]
    )["configuration_parameters"]

    assert new_configuration_parameters == expected_configuration_parameters
