import pytest
from selenium.webdriver.common.keys import Keys

from handlers.db import FloorDBHandler, PlanDBHandler, ReactPlannerProjectsDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    draw_single_wall,
    save_and_warning,
    team_member_login,
)
from tests.e2e_browser.utils_admin import expand_screen_size


@pytest.fixture(autouse=True)
def do_login(browser, editor_v2_url):
    team_member_login(browser=browser, editor_v2_url=editor_v2_url)


def test_import_annotations(
    browser,
    client_db,
    background_floorplan_image,
    building,
    plan_masterplan,
    make_plans,
    editor_v2_url,
    annotations_plan_247,
):
    """
    When the user is logged
    And enters in a non masterplan
    It will enter into import annotations mode by default
    Then it can import annotions from the masterplan successfully
    """
    (plan_b,) = make_plans(building)
    for i, plan in enumerate([plan_masterplan, plan_b]):
        FloorDBHandler.add(
            building_id=building["id"], plan_id=plan["id"], floor_number=i
        )

    ReactPlannerProjectsDBHandler.add(
        plan_id=plan_masterplan["id"], data=annotations_plan_247
    )
    PlanDBHandler.update(
        item_pks={"id": plan_masterplan["id"]},
        new_values={"annotation_finished": True},
    )

    with expand_screen_size(browser=browser):
        browser.visit(editor_v2_url + f"/{plan_b['id']}")

        # A notification appears and we enter into "Import Annotations" mode
        assert browser.is_element_present_by_id("notification-info")
        assert browser.find_by_text("Import Annotations", wait_time=TIME_TO_WAIT).first

        # Select dropdown
        browser.find_by_id("select-import-floor").click()
        browser.find_by_xpath("//option[text()='Floor 0']").first.click()
        browser.find_by_xpath(
            "//button[text()='Import Annotation']", wait_time=TIME_TO_WAIT
        ).first.click()
        assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT)

        num_of_items = len(
            browser.find_by_xpath(
                "//*[@data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )
        )
        num_of_areas = len(
            browser.find_by_xpath(
                "//*[@data-prototype='areas']",
                wait_time=TIME_TO_WAIT,
            )
        )
        num_of_lines = len(
            browser.find_by_xpath(
                "//*[@data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )
        )
        num_of_holes = len(
            browser.find_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )
        )
        assert {
            "items": num_of_items,
            "holes": num_of_holes,
            "lines": num_of_lines,
            "areas": num_of_areas,
        } == {
            "items": 31,
            "holes": 53,
            "lines": 154,
            "areas": 31,
        }

        # We should be able to draw and save after importing
        line_coords = [(300, 300), (600, 300)]
        draw_single_wall(browser, line_coords)

        active_web_element = browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ESCAPE)
        save_and_warning(browser=browser)
