import pytest

from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import (
    admin_click_save_and_assert_successful,
    expand_screen_size,
    make_login,
)
from tests.e2e_browser.utils_editor import clear_input


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url)


def building_default_values():
    return {
        "street": "somewhere",
        "zipcode": "1111",
        "city": "somecity",
    }


def test_add_building(site, admin_url, browser):
    building_new_values = [
        {"client_building_id": "1", "housenumber": "1"},
        {"client_building_id": "2", "housenumber": "2"},
        {"client_building_id": "3", "housenumber": "3"},
    ]
    browser.visit(admin_url + f"/pipelines?site_id={site['id']}")

    for new_values in building_new_values:
        building_values = building_default_values()
        building_values.update(new_values)

        browser.find_by_css(
            ".add-building-button", wait_time=TIME_TO_WAIT
        ).first.click()

        for k, v in building_values.items():
            browser.fill(name=k, value=v)
        admin_click_save_and_assert_successful(browser)

        assert browser.find_by_xpath(
            f"//td[contains(text(), 'Building: {new_values['client_building_id']}')]",
            wait_time=TIME_TO_WAIT,
        ).first


def test_add_building_floors(
    site, building, admin_url, browser, valid_image, recreate_test_gcp_client_bucket
):
    """
    Given an existing building
    Add floors with floor numbers between 0 and 2
    When the Save button is pressed in the admin-ui
    Then floors are succesfully created
    """

    with expand_screen_size(browser=browser):
        browser.visit(admin_url + f"/pipelines?site_id={site['id']}")
        # Expand building and click on the add button to add floors
        browser.find_by_css(".building-name").first.click()
        browser.find_by_css(".building-pipelines .add-button").first.click()

        # The focus field is cleared before typing the value on the second attempt
        browser.type("floor_lower_range", "0")
        clear_input(browser)
        browser.type("floor_lower_range", "0")

        browser.type("floor_upper_range", "2")
        clear_input(browser)
        browser.type("floor_upper_range", "2")
        browser.attach_file("floorplan", valid_image.as_posix())
        admin_click_save_and_assert_successful(browser=browser)


def test_edit_building(building, site, admin_url, browser):
    building_new_values = [
        {"client_building_id": "3"},
        {"client_building_id": ""},
    ]
    for new_values in building_new_values:
        browser.visit(admin_url + f"/pipelines?site_id={site['id']}")
        browser.find_by_css(".edit-building-button").first.click()

        for k, v in new_values.items():
            browser.fill(name=k, value=v)
        admin_click_save_and_assert_successful(browser)
