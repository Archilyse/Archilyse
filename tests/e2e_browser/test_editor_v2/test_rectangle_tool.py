import pytest
from selenium.webdriver.common.keys import Keys

from handlers.editor_v2.schema import ReactPlannerName
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    add_opening,
    save_plan_and_success,
    scale_and_annotate_plan,
    select_from_catalog,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.e2e_browser.utils_editor import (
    click_and_hold_accross_global_coordinates,
    click_in_global_coordinate,
)


class TestRectangleSelectToolSelection:
    @pytest.fixture(autouse=True)
    def do_login(self, browser, editor_v2_url):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)

    @staticmethod
    def test_rectangle_tool_interaction(
        browser,
        plan_masterplan,
        client_db,
        background_floorplan_image,
        editor_v2_url,
    ):
        """
        When the user is logged
        And enters into rectangle-tool mode,
        He/she can create selection rectangle by clicking and holding the mouse.
        When the selection is over two walls
        The walls are selected.
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

            wait_for_floorplan_img_load(browser=browser)
            scale_and_annotate_plan(browser)

            add_opening(browser)
            save_plan_and_success(browser=browser)

            select_from_catalog(browser, ReactPlannerName.KITCHEN.value)
            click_in_global_coordinate(
                browser=browser, pos_x=450, pos_y=550, surface_id="viewer"
            )

            # Enter rectangle select tool mode
            browser.find_by_id("rectangle-select-tool-button").first.click()

            click_and_hold_accross_global_coordinates(
                browser=browser,
                start_x=300,
                start_y=300,
                end_x=700,
                end_y=700,
                surface_id="viewer",
            )

            selected_walls = browser.find_by_xpath(
                "//*[@data-selected='true' and @data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )

            selected_holes = browser.find_by_xpath(
                "//*[@data-selected='true' and @data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )

            selected_items = browser.find_by_xpath(
                "//*[@data-selected='true' and @data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )

            assert len(selected_walls) == 4
            assert len(selected_holes) == 1
            assert len(selected_items) == 1

            # Delete selected annotations
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.DELETE)
            browser.find_by_id("select-tool-button").first.click()
            save_plan_and_success(browser=browser)

            assert browser.is_element_not_present_by_xpath(
                "//*[@data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )

            assert browser.is_element_not_present_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )

            assert browser.is_element_not_present_by_xpath(
                "//*[@data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )
