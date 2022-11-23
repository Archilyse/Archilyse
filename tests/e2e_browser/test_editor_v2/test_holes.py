from selenium.webdriver.common.keys import Keys

from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import ReactPlannerData
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    add_opening,
    save_plan_and_success,
    scale_and_annotate_plan,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size


def test_add_holes_interaction(
    browser,
    plan_masterplan,
    client_db,
    background_floorplan_image,
    editor_v2_url,
):
    """
    An opening is added to a wall
    The size
    """
    update_plan_with_gcs_image(
        plan_id=plan_masterplan["id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

        wait_for_floorplan_img_load(browser=browser)
        scale_and_annotate_plan(browser=browser)
        add_opening(browser=browser)

        decrease_size_opening_form_click(browser=browser)
        decrease_size_opening_shortcuts(browser=browser)

        lower_edge = 55
        upper_edge = 150
        change_lower_and_upper_edges(
            browser=browser, lower_edge=lower_edge, upper_edge=upper_edge
        )
        save_plan_and_success(browser=browser)

        data = ReactPlannerHandler().get_by_migrated(plan_id=plan_masterplan["id"])
        schema = ReactPlannerData(**data["data"])
        opening = list(schema.holes_by_id.values())[0]

        # Check the form to change individual heights works
        assert opening.properties.heights.lower_edge == lower_edge
        assert opening.properties.heights.upper_edge == upper_edge

        # Check the change of the length of the opening works via the form and the shortcuts
        default_door_length = 80
        step_value = 5
        assert opening.properties.length.value == default_door_length - step_value * 2


def change_lower_and_upper_edges(browser, lower_edge: int, upper_edge: int):
    browser.find_by_css("input[name='lower_edge']").first.clear()
    browser.find_by_css("input[name='lower_edge']").first.type(f"{lower_edge}")

    browser.find_by_css("input[name='upper_edge']").first.clear()
    browser.find_by_css("input[name='upper_edge']").first.type(f"{upper_edge}")
    browser.find_by_id("save-heights-button").first.click()
    assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT)


def select_opening(browser):
    browser.find_by_css("g[data-prototype='holes'] > g > polygon").click()


def decrease_size_opening_form_click(browser):
    # click the door to select it
    select_opening(browser=browser)

    # change the width of the entrance door
    browser.find_by_xpath("//table[@class='PropertyLengthMeasure']//input").click()
    browser.find_by_id("decr-length", wait_time=TIME_TO_WAIT).first.click()


def decrease_size_opening_shortcuts(browser):
    # click the door to select it
    select_opening(browser=browser)

    # change the width of the entrance door
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys([Keys.CONTROL, Keys.LEFT])
