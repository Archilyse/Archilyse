import pytest

from tests.constants import PERCY_TIME_TO_WAIT, TIME_TO_WAIT
from tests.percy_tests.utils_percy import dashboard_login, take_screenshot
from tests.utils import retry_intercepted_click


@pytest.fixture
def qa_login(browser, client_db, dashboard_url):
    dashboard_login(browser, client_db, dashboard_url, "ADMIN", ".qa")


def test_qa_view(
    browser,
    dashboard_url,
    recreate_test_gcp_client_bucket,
    splinter_download_dir_autoclean,
    site_1439_simulated,
    triangles_site_1439_3d_building_gcs,
    qa_login,
):
    """
    Open QA, select a building & unit and take a screenshot
    """
    SITE_1439_BUILDING_ID = "2656"
    UNIT_UI_NAME = "ABC0201"

    site_id = site_1439_simulated["site"]["id"]
    # To avoid flakyness, we ask for the dashboard ('blue') bg in qa
    browser.visit(dashboard_url + f"/qa/{site_id}?background=dashboard")

    assert browser.is_element_visible_by_css(".qa", wait_time=TIME_TO_WAIT)

    # Select a building
    click_building_dropdown(browser=browser)
    browser.find_by_xpath(
        f"//li[@data-value='{SITE_1439_BUILDING_ID}']", wait_time=TIME_TO_WAIT
    ).first.click()

    # Select a unit and take screenshot
    click_unit_dropdown(browser=browser)
    browser.find_by_xpath(
        f"//*[text()='{UNIT_UI_NAME}']", wait_time=TIME_TO_WAIT
    ).first.click()

    assert take_screenshot(browser, "test_qa_view", wait_time=3 * PERCY_TIME_TO_WAIT)


@retry_intercepted_click
def click_unit_dropdown(browser):
    browser.find_by_css(".qa-unit-dropdown", wait_time=TIME_TO_WAIT).first.click()


@retry_intercepted_click
def click_building_dropdown(browser):
    browser.find_by_css(".qa-building-dropdown", wait_time=TIME_TO_WAIT).first.click()
