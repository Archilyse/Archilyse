import pytest
from selenium.webdriver.common.keys import Keys

from brooks.constants import GENERIC_HEIGHTS
from brooks.types import SeparatorType
from handlers.db import PlanDBHandler
from tests.constants import FLAKY_RERUNS, TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    add_opening,
    admin_login,
    save_plan_and_success,
    scale_and_annotate_plan,
    set_plan_scale,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
    wait_for_floorplan_img_loaded_and_centered,
)
from tests.e2e_browser.utils_admin import expand_screen_size


def test_editor_v2_site_structure(
    browser,
    editor_v2_url,
    insert_react_planner_data,
    plan,
    site,
    building,
    floor,
    floor2,
    background_floorplan_image,
    client_db,
):
    """
    Given an annotated scaled plan
    Go to the editor2 window
    When the editor window opens
    User see the site structure info
    With client site ID
    And the site name and its id
    And the building info and its id
    And the floors of the plan and the pla nid
    """
    update_plan_with_gcs_image(
        plan_id=insert_react_planner_data["plan_id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{insert_react_planner_data['plan_id']}")

        assert browser.find_by_text("Site structure", wait_time=TIME_TO_WAIT).first
        assert browser.find_by_text(
            f"{site['client_site_id']}", wait_time=TIME_TO_WAIT
        ).first
        assert browser.find_by_text(
            f"{site['name']} - ({site['id']})", wait_time=TIME_TO_WAIT
        ).first
        assert browser.find_by_text(
            f"{building['street']}, {building['housenumber']} - ({building['id']})",
            wait_time=TIME_TO_WAIT,
        ).first
        assert browser.find_by_text(
            f"{floor['floor_number']}, {floor2['floor_number']} - ({plan['id']})",
            wait_time=TIME_TO_WAIT,
        ).first


def test_editor_v2_validation_errors(
    browser, editor_v2_url, plan_masterplan, background_floorplan_image, client_db
):
    """
    When the user draws a plan from scratch
    The validation errors are shown after saving
    If we reload to fetch the plan agian
    The validation errors will be shown
    If the errors are corrected and the plan is saved
    The UI wont show any error
    And we can advance to classification
    If we label the plan wrongly again
    We cannot advance to classification
    """
    update_plan_with_gcs_image(
        plan_id=plan_masterplan["id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    EXPECTED_ERROR = "SPACE_NOT_ACCESSIBLE"
    CIRCLE_ERROR_ID = "error-circle-1"

    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

        wait_for_floorplan_img_load(browser)

        # Scale and save a plan
        scale_and_annotate_plan(browser)

        # An error appears in the panel and in the grid
        assert browser.find_by_text(EXPECTED_ERROR, wait_time=TIME_TO_WAIT)
        assert browser.find_by_id(CIRCLE_ERROR_ID)

        # If we reload, the UI fetch the validated plan and show the errors
        browser.reload()

        assert browser.find_by_text(EXPECTED_ERROR, wait_time=TIME_TO_WAIT)
        assert browser.find_by_id(CIRCLE_ERROR_ID)

        # If we fix the error, they disappear from the UI
        add_opening(browser)
        save_plan_and_success(browser=browser)

        assert browser.is_element_not_present_by_text(
            EXPECTED_ERROR, wait_time=TIME_TO_WAIT
        )
        assert browser.is_element_not_present_by_id(
            CIRCLE_ERROR_ID, wait_time=TIME_TO_WAIT
        )

        # And we can advance to classification
        assert browser.find_by_text("Go to classification", wait_time=TIME_TO_WAIT)


@pytest.mark.flaky(reruns=FLAKY_RERUNS)
def test_save_heights(
    browser,
    plan,
    client_db,
    background_floorplan_image,
    insert_react_planner_data,
    editor_v2_url,
):
    update_plan_with_gcs_image(
        plan_id=plan["id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    button_xpath = (
        "//button[@class = 'primary-button' and text() = 'Save Default heights']"
    )
    with expand_screen_size(browser=browser):
        admin_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{plan['id']}")
        wait_for_floorplan_img_load(browser=browser)
        browser.find_by_xpath(
            "//*[contains(text(), 'Default heights')]", wait_time=TIME_TO_WAIT
        ).first.click()
        wall_height = int(GENERIC_HEIGHTS[SeparatorType.WALL][1] * 100)
        browser.find_by_css(f'input[type="number"][value="{wall_height}"]').first.type(
            ""
        )
        number_of_increases = 5
        for _ in range(number_of_increases):
            browser.driver.switch_to.active_element.send_keys(Keys.UP)

        browser.find_by_xpath(button_xpath).first.click()
        assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT)
        plan = PlanDBHandler.get_by(id=plan["id"])
        assert (
            plan["default_wall_height"] == (wall_height + number_of_increases) / 100.0
        )


def assert_background_properties(
    browser, width, height, expected_position_x, expected_position_y, expected_rotate
):

    floorplan_img = browser.find_by_xpath(
        f"//*[(@id='floorplan-img') and (@width={str(width)}) and  (@height={str(height)})]",
        wait_time=TIME_TO_WAIT,
    ).first

    assert floorplan_img["x"] == str(expected_position_x)
    assert floorplan_img["y"] == str(expected_position_y)

    floorplan_img_group = browser.find_by_id("background-img-group").first
    assert floorplan_img_group["transform"] == f"{expected_rotate}"


def test_modify_background_image(
    browser,
    plan_masterplan,
    client_db,
    background_floorplan_image,
    editor_v2_url,
):
    """
    When loading a plan
    If the user enters rotate/scale background mode
    And modifies the properties of the background
    The background changes
    If he/she saves the changes
    The changes are applied next time the plan is loaded

    """
    update_plan_with_gcs_image(
        plan_id=plan_masterplan["id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    INITIAL_BACKGROUND_WIDTH = 2187
    INITIAL_BACKGROUND_HEIGHT = 1640
    INITIAL_BACKGROUND_X = 0
    INITIAL_BACKGROUND_Y = 0
    INITIAL_BACKGROUND_ROTATE = "rotate(0, 1093.5, 820)"

    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")
        wait_for_floorplan_img_loaded_and_centered(browser=browser)
        set_plan_scale(browser)

        assert_background_properties(
            browser=browser,
            width=INITIAL_BACKGROUND_WIDTH,
            height=INITIAL_BACKGROUND_HEIGHT,
            expected_position_x=INITIAL_BACKGROUND_X,
            expected_position_y=INITIAL_BACKGROUND_Y,
            expected_rotate=INITIAL_BACKGROUND_ROTATE,
        )

        # Enter rotate/scale mode
        browser.find_by_id("rotate-scale-background-button").first.click()

        # Modify background
        NEW_BACKGROUND_SCALE = "0.96"
        NEW_BACKGROUND_X = 30
        NEW_BACKGROUND_Y = 15
        NEW_BACKGROUND_ROTATION = 5

        browser.find_by_name("backgroundScale").first.clear()
        browser.find_by_name("backgroundScale").first.type(NEW_BACKGROUND_SCALE)

        browser.find_by_name("rotation").first.clear()
        browser.find_by_name("rotation").first.type(NEW_BACKGROUND_ROTATION)

        browser.find_by_name("shiftX").first.clear()
        browser.find_by_name("shiftX").first.type(NEW_BACKGROUND_X)

        browser.find_by_name("shiftY").first.clear()
        browser.find_by_name("shiftY").first.type(NEW_BACKGROUND_Y)

        # Background should have the changes
        EXPECTED_BACKGROUND_WIDTH = int(
            INITIAL_BACKGROUND_WIDTH * float(NEW_BACKGROUND_SCALE)
        )
        EXPECTED_BACKGROUND_HEIGHT = int(
            INITIAL_BACKGROUND_HEIGHT * float(NEW_BACKGROUND_SCALE)
        )
        EXPECTED_BACKGROUND_X = 30
        EXPECTED_BACKGROUND_Y = (
            51  # scene.height(1640) - new_background_height(1574) - new_y (15)
        )
        EXPECTED_BACKGROUND_ROTATION_AXIS_X = (
            1079.5  # EXPECTED_BACKGROUND_WIDTH / 2 + EXPECTED_BACKGROUND_X
        )
        EXPECTED_BACKGROUND_ROTATION_AXIS_Y = (
            838  # EXPECTED_BACKGROUND_HEIGHT / 2 + EXPECTED_BACKGROUND_Y
        )
        EXPECTED_BACKGROUND_ROTATE = f"rotate({NEW_BACKGROUND_ROTATION}, {EXPECTED_BACKGROUND_ROTATION_AXIS_X}, {EXPECTED_BACKGROUND_ROTATION_AXIS_Y})"

        assert_background_properties(
            browser=browser,
            width=EXPECTED_BACKGROUND_WIDTH,
            height=EXPECTED_BACKGROUND_HEIGHT,
            expected_position_x=EXPECTED_BACKGROUND_X,
            expected_position_y=EXPECTED_BACKGROUND_Y,
            expected_rotate=EXPECTED_BACKGROUND_ROTATE,
        )

        # Trying to reload or refresh page without saving triggers an alert
        browser.reload()
        alert = browser.get_alert()
        assert alert is not None
        alert.dismiss()

        # Save the changes & reload
        browser.find_by_text("Save").first.click()
        assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT)
        browser.reload()

        # Background should have the saved properties
        wait_for_floorplan_img_loaded_and_centered(browser=browser)
        assert_background_properties(
            browser=browser,
            width=EXPECTED_BACKGROUND_WIDTH,
            height=EXPECTED_BACKGROUND_HEIGHT,
            expected_position_x=EXPECTED_BACKGROUND_X,
            expected_position_y=EXPECTED_BACKGROUND_Y,
            expected_rotate=EXPECTED_BACKGROUND_ROTATE,
        )
