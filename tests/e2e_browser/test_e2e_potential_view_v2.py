from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import make_login


def admin_login(browser, potential_view_v2_url):
    make_login(
        browser, potential_view_v2_url, expected_element_id="potential-view-home"
    )


def test_potential_view_v2_not_available_for_non_authorized(
    browser, potential_view_v2_url
):
    """
    Non-authorized user can not access Potential View UI
    """
    browser.visit(potential_view_v2_url)

    assert browser.is_element_not_present_by_xpath(
        "//h2[text()='Potential Simulations']", wait_time=TIME_TO_WAIT
    )

    assert browser.is_element_visible_by_xpath(
        "//*[text()='Sign in']", wait_time=TIME_TO_WAIT
    )


def test_potential_view_v2_available_for_authorized(browser, potential_view_v2_url):
    """
    Authorized user can access Potential View UI
    """
    admin_login(browser, potential_view_v2_url)

    assert browser.is_element_visible_by_xpath(
        "//h2[text()='Potential Simulations']", wait_time=TIME_TO_WAIT
    )


def test_potential_view_displays_success_simulations(
    browser, potential_view_v2_url, two_potential_simulations_success_and_failed
):
    admin_login(browser, potential_view_v2_url)
    assert (
        len(browser.find_by_xpath("//span[contains(@class, 'simulation-status')]")) == 1
    )


def check_spinner_loads_and_disappears(browser):
    assert browser.is_element_present_by_css(
        "button .loading-indicator", wait_time=TIME_TO_WAIT
    )

    # wait until spinner disappears
    assert browser.is_element_not_present_by_css(
        "button .loading-indicator", wait_time=TIME_TO_WAIT
    )
