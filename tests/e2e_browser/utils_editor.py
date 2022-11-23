import time

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from handlers.db import PlanDBHandler
from tests.constants import SLAM_AUTH_COOKIE_NAME, TIME_TO_WAIT, USERS
from tests.db_fixtures import create_user_context
from tests.utils import TestRetryException


def assert_plan_is_finished_in_db(plan_id):
    plan_data = PlanDBHandler.get_by(id=plan_id)
    assert plan_data["annotation_finished"] is True


def assert_basic_elements_are_visible_in_page(browser):
    assert browser.is_element_present_by_id("save_button")
    assert browser.is_element_present_by_id("help_button")
    assert browser.is_element_present_by_id("copyright")


def click_in_global_coordinate(browser, pos_x, pos_y, surface_id="base_app_surface"):
    action = ActionChains(browser.driver)
    base_app_surface = browser.driver.find_element_by_id(surface_id)

    action.move_to_element_with_offset(base_app_surface, pos_x, pos_y)
    action.click()
    action.perform()


def move_in_global_coordinate(browser, pos_x, pos_y, surface_id="base_app_surface"):
    action = ActionChains(browser.driver)
    base_app_surface = browser.driver.find_element_by_id(surface_id)

    action.move_to_element_with_offset(base_app_surface, pos_x, pos_y)
    action.perform()


def click_and_hold_accross_global_coordinates(
    browser,
    start_x,
    start_y,
    end_x,
    end_y,
    surface_id="base_app_surface",
    hold_range=None,
):
    action = ActionChains(browser.driver)
    base_app_surface = browser.driver.find_element_by_id(surface_id)

    action.move_to_element_with_offset(base_app_surface, start_x, start_y)
    action.click_and_hold()

    if hold_range:
        for x in range(start_x, end_x, hold_range):
            action.move_to_element_with_offset(base_app_surface, x, end_y)
    else:
        action.move_to_element_with_offset(base_app_surface, end_x, end_y)

    action.release()
    action.perform()


def click_in_app_surface_center(browser, surface_id="base_app_surface"):
    action = ActionChains(browser.driver)
    base_app_surface = browser.driver.find_element_by_id(surface_id)

    size = base_app_surface.size
    action.move_to_element_with_offset(
        base_app_surface, size.get("width") / 2, size.get("height") / 2
    )
    action.click()
    action.perform()


def assert_error_is_visible_in_page(browser):
    assert browser.is_element_present_by_id("errorMessage")


def click_save_button(browser):
    assert browser.is_element_present_by_css(
        "#save_button:not([disabled])", wait_time=TIME_TO_WAIT
    )
    browser.find_by_id("save_button").first.click()


def click_save_and_wait_till_saved(browser):
    click_save_button(browser)
    WebDriverWait(browser.driver, TIME_TO_WAIT).until(
        expected_conditions.text_to_be_present_in_element(
            (By.ID, "save_button"), "Saved"
        )
    )


def wait_for_preview_img(browser):
    browser.is_element_present_by_id("preview_img", wait_time=TIME_TO_WAIT)


def assert_snack_bar_successful(browser, msg_to_check="saved successfully"):
    assert browser.is_element_present_by_xpath("//simple-snack-bar/span")
    for _ in range(5):
        snack_bar_text = browser.find_by_xpath("//simple-snack-bar/span").first.text
        if snack_bar_text:
            assert msg_to_check in snack_bar_text, snack_bar_text
            return True
    assert (
        msg_to_check in browser.find_by_xpath("//simple-snack-bar/span").first.text
    ), browser.find_by_xpath("//simple-snack-bar/span").first.text


@retry(
    retry=retry_if_exception_type(TestRetryException),
    stop=stop_after_attempt(5),
    wait=wait_fixed(wait=0.1),
    reraise=True,
)
def assert_snack_bar_error(browser, error_message: str, close_snackbar: bool):
    if not browser.is_element_present_by_xpath("//simple-snack-bar/span"):
        raise TestRetryException("Could not find a snackbar after multiple retries")
    snack_bar_text = browser.find_by_xpath("//simple-snack-bar/span").first.text
    assert error_message == snack_bar_text, snack_bar_text

    if close_snackbar:
        browser.find_by_xpath("//simple-snack-bar/div").first.click()


def wait_for_auth_cookie(browser, times=20):
    if not browser.driver.get_cookie(SLAM_AUTH_COOKIE_NAME):
        if times > 0:
            time.sleep(0.2)
            return wait_for_auth_cookie(browser=browser, times=times - 1)
        else:
            raise Exception("Couldn't find the slam-auth cookie after 4 seconds")


def make_login(browser, url, user_type="ADMIN"):
    context = create_user_context(USERS[user_type])["user"]
    browser.driver.delete_cookie(SLAM_AUTH_COOKIE_NAME)
    browser.visit(url)
    browser.find_by_id("userInput").first.fill(context["login"])
    browser.find_by_id("passwordInput").first.fill(context["password"])
    browser.find_by_id("saveButton").first.click()
    wait_for_auth_cookie(browser=browser)
    # TODO: This browser.find_by_xpath("//button[contains(@class, 'mat-button')]").first.click()
    #  should be possible here but somehow the snackbar doesn't belong to the document?
    return context


def accept_snack_bar_message(browser):
    browser.find_by_xpath(
        "//span[contains(@class, 'mat-button-wrapper')]", wait_time=TIME_TO_WAIT
    ).first.click()


def clear_input(browser):
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.CONTROL + "a")
    active_web_element.send_keys(Keys.DELETE)


def log_out(browser):
    browser.find_by_xpath(
        "//button[contains(@class, 'btn btn-link logOut')]"
    ).first.click()
