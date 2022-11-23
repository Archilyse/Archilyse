import pytest
from splinter.driver.webdriver import BaseWebDriver

from common_utils.constants import USER_ROLE
from handlers.db import FloorDBHandler, PlanDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import (
    admin_click_delete_and_assert_successful,
    admin_click_save_and_assert_successful,
    expand_screen_size,
    make_login,
)
from tests.e2e_browser.utils_editor import clear_input
from tests.utils import switch_to_opened_tab


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url, user_type=USER_ROLE.TEAMMEMBER.value)


def test_floor_original_plan(floor, plan, admin_url, browser: BaseWebDriver):
    """
    Given a pipeline
    Open its original plan file
    """
    browser.visit(admin_url + f"/floor/plan?plan_id={floor['plan_id']}")
    assert browser.find_by_id("original-plan", wait_time=TIME_TO_WAIT * 2).first


def test_edit_range_of_floors(
    site, building, floor, admin_url, browser, recreate_test_gcp_client_bucket
):
    """
    Given an existing plan
    Edit the floor range with floor numbers 0 and 2
    When the Save button is pressed
    Then 3 new floors are created
    And they have floor_number values 0, 1, 2
    """

    with expand_screen_size(browser=browser):
        browser.visit(admin_url + f"/pipelines?site_id={site['id']}")
        # Expand building and click on the add button to add floors
        browser.find_by_css(".building-name").first.click()
        browser.find_by_css(".edit-floor-button").first.click()

        browser.type("floor_lower_range", "0")
        clear_input(browser)
        browser.type("floor_lower_range", "0")

        browser.type("floor_upper_range", "2")
        clear_input(browser)
        browser.type("floor_upper_range", "2")
        admin_click_save_and_assert_successful(browser=browser)

        plans = PlanDBHandler.find()
        assert len(plans) == 1

        floors = FloorDBHandler.find()
        assert len(floors) == 3
        assert {f["floor_number"] for f in floors} == {0, 1, 2}
        browser.find_by_css(".edit-floor-button").first.click()
        admin_click_delete_and_assert_successful(browser=browser)

        assert not FloorDBHandler.find()


def test_pipelines_masterplan_workflow(
    site,
    plan,
    building,
    floor,
    make_plans,
    admin_url,
    valid_image,
    browser: BaseWebDriver,
    recreate_test_gcp_client_bucket,
):
    """
    Given two pipelines with no master plans
    There is no link to access to pipeline
    If a masterplan is selected
    There are links to access the pipeline
    If we access the masterplan link, we need to scale it
    If we access the regular plan link, we need to import annotations
    """
    (plan_2,) = make_plans(building)

    with expand_screen_size(browser=browser):
        browser.visit(admin_url + f"/pipelines?site_id={site['id']}")
        # Expand building and click on the add button to add floors
        browser.find_by_css(".building-name").first.click()

        # No links initially
        pipeline_links = browser.links.find_by_text("Go to pipeline")
        assert len(pipeline_links) == 0

        # Mark the first plan as masterplan
        browser.find_by_xpath(
            "//input[@type='radio']", wait_time=TIME_TO_WAIT
        ).first.click()

        # There should be links to the editor
        pipeline_links = browser.links.find_by_text("Go to pipeline")
        assert len(pipeline_links) > 0

        # Go to the plan marked as "master plan"
        browser.find_by_text("Go to pipeline").first.click()

        switch_to_opened_tab(browser)

        # Editor asks to scale
        assert browser.find_by_text(
            "New plan, please set the scale by drawing a line or an area",
            wait_time=TIME_TO_WAIT,
        ).first

        # Close and go back to Admin UI
        browser.windows.current.close()

        # Go to the regular plan
        browser.find_by_text("Go to pipeline")[1].click()

        switch_to_opened_tab(browser)

        # Editor asks to import
        assert browser.find_by_text(
            "Please import annotations to start", wait_time=TIME_TO_WAIT
        ).first
