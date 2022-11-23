import pytest

from tests.constants import PERCY_TIME_TO_WAIT, TIME_TO_WAIT, USERS
from tests.percy_tests.utils_percy import take_screenshot
from tests.selenium_utils import expand_competition_category_clicking_arrow
from tests.utils import create_user_context

PERCY_SCREENSHOT_HEIGHT = 1152
PERCY_SCREENSHOT_WIDTH = 2000

CANVAS_SCREENSHOT_HEIGHT = 613
CANVAS_SCREENSHOT_WIDTH = 1920
CANVAS_TESTS_ENABLED = False


@pytest.fixture
def do_login(browser, client_db, dashboard_url):
    context = create_user_context(USERS["COMPETITION_ADMIN"])["user"]

    browser.visit(dashboard_url + "/login")
    browser.fill("user", context["login"])
    browser.fill("password", context["password"])
    browser.find_by_text("Sign in").first.click()
    assert browser.is_element_visible_by_css(".competitions", wait_time=TIME_TO_WAIT)


def test_default_competition_view(
    browser, competition_with_fake_feature_values, dashboard_url, do_login
):
    """
    Takes a screenshot of the default competition
    """
    browser.visit(
        dashboard_url + f"/competition/{competition_with_fake_feature_values['id']}"
    )
    assert browser.is_element_visible_by_css(".competition-tool-table")
    assert browser.is_element_visible_by_xpath("//th[@data-testid='winner']")
    expand_competition_category_clicking_arrow(
        browser=browser, category="Gesamtpunktzahl"
    )
    expand_competition_category_clicking_arrow(
        browser=browser, category="Gesamtbruttomiete / Jahr"
    )

    assert take_screenshot(browser, "test_default_competition")


def test_competition_heatmap_modal(
    browser, competition_with_fake_feature_values, dashboard_url, do_login
):
    """
    Takes a screenshot of modal with a heatmap
    """
    CATEGORY_NAME = "Umgebung – Allgemein"
    SUB_CATEGORY_NAME = "Umgebung – Analysen"
    DATA_FEATURE_NAME = "Analyse Grünraum"

    browser.visit(
        dashboard_url + f"/competition/{competition_with_fake_feature_values['id']}"
    )

    browser.find_by_xpath(
        f"//div[text()='{CATEGORY_NAME}']/following-sibling::div//button"
    ).first.click()
    browser.find_by_xpath(
        f"//div[text()='{SUB_CATEGORY_NAME}']/following-sibling::div//button"
    ).first.click()
    browser.find_by_xpath(
        f'//button[contains(text(), "{DATA_FEATURE_NAME}")]'
    ).first.click()

    assert browser.find_by_css(".common-modal-container").first.visible

    assert take_screenshot(
        browser,
        "test_competition_heatmap_modal",
        wait_time=3 * PERCY_TIME_TO_WAIT,
    )
