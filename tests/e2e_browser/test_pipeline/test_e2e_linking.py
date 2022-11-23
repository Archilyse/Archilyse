import pytest

from handlers.db import UnitDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_editor import (
    assert_error_is_visible_in_page,
    assert_snack_bar_error,
    assert_snack_bar_successful,
    click_save_and_wait_till_saved,
    make_login,
    wait_for_preview_img,
)
from tests.e2e_utils import SlamUIClient


@pytest.fixture(autouse=True)
def do_login(browser, login_url):
    make_login(browser, login_url)


def test_linking_window_appears_with_an_error(browser, linking_url_wrong_plan):
    """
    Go to the linking window as a non-dev user and a plan_id that doesn't exist
    When the linking window opens we check that the users gets an error
    """
    browser.visit(linking_url_wrong_plan)

    assert_error_is_visible_in_page(browser=browser)


def test_linking_link_all_units(
    browser,
    recreate_test_gcp_client_bucket,
    linking_url_default_plan,
    add_background_plan_image_to_gcloud,
    plan,
):
    """
    Go to the linking window as a non-dev user
    Assign a client ID to all units and save
    Reload the window and verify the units have the proper client IDs.
    """

    add_background_plan_image_to_gcloud(plan_info=plan)
    browser.visit(linking_url_default_plan)
    wait_for_preview_img(browser)

    # We add apartment ids to all units
    dummy_client_id = "1.23"
    input_list = browser.find_by_css(".client-input")
    assert len(input_list) > 0
    for client_input in input_list:
        client_input.fill(dummy_client_id)

    # We assign usage type "commercial" to all units and try to save (fails as the area types are not for commercial units)
    for option in browser.find_by_xpath("//option[contains(text(), 'COMMERCIAL')]"):
        option.click()

    browser.find_by_id("save_button").first.click()
    assert_snack_bar_error(
        browser=browser,
        error_message="Error saving the linking, check the error list and the dots in the floorplan.",
        close_snackbar=True,
    )

    # We correctly assign usage type "residential" and save successfully
    for option in browser.find_by_xpath("//option[contains(text(), 'RESIDENTIAL')]"):
        option.click()

    browser.find_by_id("save_button").first.click()
    assert_snack_bar_successful(
        browser=browser, msg_to_check="Linking saved successfully"
    )

    # Reload to ensure everything is linked and usage types are set
    browser.visit(linking_url_default_plan)
    input_list = browser.find_by_css(".client-input")
    for client_input in input_list:
        assert client_input.value == dummy_client_id

    for select in browser.find_by_xpath(
        "//select[contains(@class, 'client-unit-usage-input')]"
    ):
        assert select["id"] == "RESIDENTIAL"


def test_auto_linking(
    site_834,
    plan,
    browser,
    recreate_test_gcp_client_bucket,
    add_background_plan_image_to_gcloud,
):
    """
    Go to the linking window as a non-dev user
    Click on the button to perform auto link & save
    Reload the window and verify all the units have been linked.
    """
    add_background_plan_image_to_gcloud(plan_info=plan)
    browser.visit(SlamUIClient._linking_url_plan(plan_id=plan["id"]))
    wait_for_preview_img(browser)

    browser.find_by_css(".autoLink", wait_time=TIME_TO_WAIT).first.click()
    assert_snack_bar_successful(
        browser=browser, msg_to_check="Successfully linked automatically 5 units"
    )

    click_save_and_wait_till_saved(browser)

    assert {unit["client_id"] for unit in UnitDBHandler.find()} == {
        "Apartment.01.01.0001",
        "Apartment.01.01.0002",
        "Apartment.01.01.0003",
        "Apartment.01.03.0001",
        "Apartment.01.03.0002",
    }

    # Reload to ensure everything is linked
    browser.reload()
    wait_for_preview_img(browser)
    input_list = browser.find_by_css(".client-input")
    assert len(input_list) == 5
    for client_input in input_list:
        assert client_input.value
