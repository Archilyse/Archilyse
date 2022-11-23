import pytest

from handlers.db import SiteDBHandler
from tests.constants import TIME_TO_WAIT, USERS
from tests.db_fixtures import create_user_context
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.utils import javascript_click_by_data_value

QA_URL = "/qa"


def log_into_qa(browser, client_db, dashboard_url):
    context = create_user_context(USERS["ADMIN"])["user"]

    browser.visit(dashboard_url + "/login")
    browser.fill("user", context["login"])
    browser.fill("password", context["password"])
    browser.find_by_text("Sign in").first.click()
    assert browser.is_element_visible_by_css(".qa", wait_time=TIME_TO_WAIT)


@pytest.fixture
def do_login(browser, client_db, dashboard_url):
    log_into_qa(browser, client_db, dashboard_url)


def test_qa_user_saves_notes_and_validates(
    browser,
    client_db,
    do_login,
    dashboard_url,
    site_1439_simulated,
):
    """
    Open QA page
    Saves the notes
    Sets the heatmaps as validated
    """
    with expand_screen_size(browser=browser):
        site_id = site_1439_simulated["site"]["id"]

        # Make sure that the heatmaps are not validated on load
        SiteDBHandler.update(
            item_pks={"id": site_id}, new_values={"heatmaps_qa_complete": False}
        )

        browser.visit(dashboard_url + f"{QA_URL}/{site_id}")
        assert browser.is_element_visible_by_css(".qa", wait_time=TIME_TO_WAIT)

        # saving and validating
        expected_text = "This site is just a mess 2"
        browser.find_by_xpath("//textarea").first.fill(expected_text)
        assert browser.is_element_present_by_css(
            "#save_notes_button:not([disabled])", wait_time=TIME_TO_WAIT
        )
        browser.find_by_id("save_notes_button").first.click()

        browser.find_by_id("validate_button").first.click()
        browser.is_element_present_by_css(
            "#validate_button:not([enabled])", wait_time=TIME_TO_WAIT
        )

        assert browser.find_by_text("Heatmaps validated", wait_time=TIME_TO_WAIT).first

        site_info = SiteDBHandler.get_by(id=site_id)
        assert site_info["heatmaps_qa_complete"] is True
        assert site_info["validation_notes"] == expected_text


def test_check_heatmaps(
    browser,
    client_db,
    do_login,
    dashboard_url,
    site_1439_simulated,
):
    """
    Open QA page
    Click on "Check heatmaps switch"
    Several heatmaps appears
    If we select a floor
    A heatmap of the current floor appears
    If we select a unit
    A heatmap of the current unit appears
    If we group by "view"
    Several heatmaps for every simulation view appear
    """
    BUILDINGS_SIM = "buildings"
    SKY_SIM = "sky"
    SINGLE_SIM_MODE = "single"

    INITIAL_SIM_1 = "buildings"
    INITIAL_SIM_2 = "greenery"
    INITIAL_SIM_3 = "isovist"

    site_id = site_1439_simulated["site"]["id"]
    browser.visit(dashboard_url + f"{QA_URL}/{site_id}")
    assert browser.is_element_visible_by_css(".qa", wait_time=TIME_TO_WAIT)

    # Ensure several view heatmaps are show
    assert browser.find_by_xpath(
        f"//*[contains(text(), {INITIAL_SIM_1})]", wait_time=TIME_TO_WAIT
    ).first
    assert browser.find_by_xpath(
        f"//*[contains(text(), {INITIAL_SIM_2})]", wait_time=TIME_TO_WAIT
    ).first
    assert browser.find_by_xpath(
        f"//*[contains(text(), {INITIAL_SIM_3})]", wait_time=TIME_TO_WAIT
    ).first

    # Select the first floor & ensure the heatmap for that floor is shown
    FIRST_FLOOR_ID = "12248"
    browser.find_by_xpath(
        "//*[contains(@class, 'qa-floor-dropdown')]", wait_time=TIME_TO_WAIT
    ).first.click()

    javascript_click_by_data_value(browser=browser, data_value=FIRST_FLOOR_ID)

    heatmap_title = browser.find_by_css(
        ".heatmap-title", wait_time=TIME_TO_WAIT
    ).first.text
    assert heatmap_title == f"Floor 1 - {BUILDINGS_SIM}"

    # Select the first unit & ensure the heatmap for that unit is shown
    FIRST_UNIT_CLIENT_ID = "ABC0101"
    FIRST_UNIT_ID = "61596"
    browser.find_by_xpath(
        "//*[contains(@class, 'qa-unit-dropdown')]", wait_time=TIME_TO_WAIT
    ).first.click()
    javascript_click_by_data_value(browser=browser, data_value=FIRST_UNIT_ID)

    heatmap_title = browser.find_by_css(
        ".heatmap-title", wait_time=TIME_TO_WAIT
    ).first.text
    assert heatmap_title == f"Unit {FIRST_UNIT_CLIENT_ID} - {BUILDINGS_SIM}"

    # Select a single simulation & ensure that simulation is shown
    browser.find_by_xpath(
        f"//input[@type='radio'][@value='{SINGLE_SIM_MODE}']", wait_time=TIME_TO_WAIT
    ).first.click()

    browser.find_by_xpath(
        "//*[contains(@class, 'qa-simulation-name-dropdown')]", wait_time=TIME_TO_WAIT
    ).first.click()

    javascript_click_by_data_value(browser=browser, data_value=SKY_SIM)

    heatmap_title = browser.find_by_css(
        ".heatmap-title", wait_time=TIME_TO_WAIT
    ).first.text
    assert heatmap_title == f"Unit {FIRST_UNIT_CLIENT_ID} - {SKY_SIM}"
