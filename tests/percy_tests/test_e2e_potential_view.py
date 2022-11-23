import pytest
from selenium.webdriver.common.keys import Keys

from tests.constants import PERCY_TIME_TO_WAIT, TIME_TO_WAIT, USERS
from tests.percy_tests.utils_percy import take_screenshot
from tests.utils import create_user_context


@pytest.fixture
def do_login(browser, client_db, potential_view_v2_url):
    context = create_user_context(USERS["ADMIN"])["user"]

    browser.visit(potential_view_v2_url + "/login")
    browser.fill("user", context["login"])
    browser.fill("password", context["password"])

    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.ENTER)

    assert browser.is_element_visible_by_css(".home-container", wait_time=TIME_TO_WAIT)


def test_potential_view_home_screen(
    browser, potential_view_simulations_list, potential_view_v2_url, do_login
):
    """
    Takes a screenshot of the home screen
    """

    # wait until simulation cards are loaded
    assert browser.is_element_visible_by_css(
        ".simulation-info-card", wait_time=TIME_TO_WAIT
    )

    assert take_screenshot(browser, "test_home_screen")


def test_potential_heatmaps_over_map(
    browser, potential_view_simulations_list, potential_view_v2_url, do_login
):
    """
    Takes a screenshot of the detailed view of simulation
    """
    # wait until simulation cards are loaded
    assert browser.is_element_visible_by_css(
        ".simulation-info-card", wait_time=TIME_TO_WAIT
    )

    browser.find_by_text("View result").first.click()

    assert browser.is_element_visible_by_css(
        ".heatmap-canvas-container", wait_time=TIME_TO_WAIT
    )

    assert take_screenshot(
        browser,
        "test_simulation_result_map_buildings",
        wait_time=2 * PERCY_TIME_TO_WAIT,
    )
