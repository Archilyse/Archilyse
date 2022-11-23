import time

from tests.constants import TIME_TO_WAIT

STATUS_NAVIGATION_DISABLED = "disabled"
STATUS_NAVIGATION_AVAILABLE = "available"
STATUS_NAVIGATION_COMPLETED = "completed"


def assert_classification_is_visible_in_page(browser):
    assert browser.is_element_present_by_id("classification_app")


def assert_linking_is_visible_in_page(browser):
    assert browser.is_element_present_by_id("linking_app")


def assert_quality_is_visible_in_page(browser):
    assert browser.is_element_present_by_id("quality_app")


def assert_scaling_is_visible_in_page(browser):
    assert browser.is_element_present_by_id("scaling_app")


def assert_georeference_is_visible_in_page(browser):
    assert browser.is_element_present_by_id("georeference_app")


def editor_click_help_button(browser):
    browser.find_by_id("help_button", wait_time=TIME_TO_WAIT).first.click()
    assert browser.is_element_present_by_id("helpDialog", wait_time=TIME_TO_WAIT)


def assert_help_modal_is_visible(browser, number_of_li, number_of_instructions):
    editor_click_help_button(browser=browser)
    items_in_help = {
        len(instructions.find_by_xpath("li"))
        for instructions in browser.find_by_xpath(
            "//ul[contains(@class, 'instructions')]"
        )
    }
    assert items_in_help == {number_of_li, number_of_instructions}


def assert_site_navigation_is_visible_in_page(
    browser,
    status_editor,
    status_classification,
    status_splitting,
    status_georeference,
    status_linking,
):
    assert browser.is_element_present_by_id(
        "navigationContainer", wait_time=TIME_TO_WAIT
    )

    assert browser.is_element_visible_by_xpath(
        "//li[contains(@class, 'nav-item-editor')] // a[contains(@class, '"
        + status_editor
        + "')]",
        wait_time=TIME_TO_WAIT,
    )
    assert browser.is_element_visible_by_xpath(
        "//li[contains(@class, 'nav-item-classification')] // a[contains(@class, '"
        + status_classification
        + "')]",
        wait_time=TIME_TO_WAIT,
    )
    assert browser.is_element_visible_by_xpath(
        "//li[contains(@class, 'nav-item-splitting')] // a[contains(@class, '"
        + status_splitting
        + "')]",
        wait_time=TIME_TO_WAIT,
    )
    assert browser.is_element_visible_by_xpath(
        "//li[contains(@class, 'nav-item-georeference')] // a[contains(@class, '"
        + status_georeference
        + "')]",
        wait_time=TIME_TO_WAIT,
    )
    assert browser.is_element_visible_by_xpath(
        "//li[contains(@class, 'nav-item-linking')] // a[contains(@class, '"
        + status_linking
        + "')]",
        wait_time=TIME_TO_WAIT,
    )


def wait_for_browser_condition(browser, condition, wait_time=TIME_TO_WAIT):
    if not browser.execute_script(condition):
        if wait_time > 0:
            time.sleep(1.0)
            return wait_for_browser_condition(
                browser=browser, condition=condition, wait_time=wait_time - 1.0
            )

        raise AssertionError(f"browser condition `{condition}` never fulfilled.")
