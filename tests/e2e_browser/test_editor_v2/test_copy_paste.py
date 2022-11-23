import pytest
from selenium.webdriver.common.keys import Keys

from handlers.db import PlanDBHandler
from handlers.editor_v2.schema import ReactPlannerName
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    add_opening,
    save_plan_and_success,
    scale_and_annotate_plan,
    select_from_catalog,
    set_plan_scale,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.e2e_browser.utils_editor import (
    click_and_hold_accross_global_coordinates,
    click_in_global_coordinate,
)


class TestCopyPaste:
    @pytest.fixture(autouse=True)
    def do_login(self, browser, editor_v2_url):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)

    @staticmethod
    def test_copy_paste_interaction(
        browser,
        plan_masterplan,
        client_db,
        background_floorplan_image,
        editor_v2_url,
    ):
        """
        When the user is logged
        And enters into copypaste mode
        He/she can create selection rectangle by clicking and holding the mouse
        When the selection is over two walls
        The walls are selected
        Then if the user drags the selection around
        And press ENTER
        The walls are pasted elsewhere and a new area is created
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

            original_lines = browser.find_by_xpath(
                "//*[@data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )
            original_items = browser.find_by_xpath(
                "//*[@data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )
            original_areas = browser.find_by_xpath(
                "//*[@data-prototype='areas']",
                wait_time=TIME_TO_WAIT,
            )
            original_holes = browser.find_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )
            original_nr_of_lines = len(original_lines)
            original_nr_of_items = len(original_items)
            original_nr_of_areas = len(original_areas)
            original_nr_of_holes = len(original_holes)

            # Enter copy paste
            browser.find_by_id("copy-paste-button").first.click()

            click_and_hold_accross_global_coordinates(
                browser=browser,
                start_x=300,
                start_y=300,
                end_x=700,
                end_y=700,
                surface_id="viewer",
            )

            assert browser.find_by_id(
                "copy-paste-selection", wait_time=TIME_TO_WAIT
            ).first.visible

            copied_walls = browser.find_by_xpath(
                "//*[@data-selected='true' and @data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )
            assert len(copied_walls) == 4

            # Drag it to the right
            click_and_hold_accross_global_coordinates(
                browser=browser,
                start_x=450,
                start_y=550,
                end_x=1000,
                end_y=600,
                surface_id="viewer",
                hold_range=100,
            )

            # Paste it
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.CONTROL + "v")

            # If we have pasted successfully there will be twice the number of lines, areas, items & holes
            lines = browser.find_by_xpath(
                "//*[@data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )
            items = browser.find_by_xpath(
                "//*[@data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )
            areas = browser.find_by_xpath(
                "//*[@data-prototype='areas']",
                wait_time=TIME_TO_WAIT,
            )
            holes = browser.find_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )

            assert len(lines) == original_nr_of_lines * 2
            assert len(areas) == original_nr_of_areas * 2
            assert len(items) == original_nr_of_items * 2
            assert len(holes) == original_nr_of_holes * 2
            browser.find_by_id("select-tool-button").first.click()
            save_plan_and_success(browser=browser)

    @staticmethod
    def test_copy_paste_between_plans(
        browser,
        plan_masterplan,
        client_db,
        background_floorplan_image,
        building,
        make_plans,
        editor_v2_url,
    ):
        """
        When the user is logged
        And enters into copypaste mode
        He/she can create selection rectangle by clicking and holding the mouse
        And the selection is automatically copied in the local storage
        If the user opens a new plan and paste the selection there
        The elements from the original plan are copied in the new one
        """
        (plan2,) = make_plans(*(building,))
        PlanDBHandler.update(
            item_pks={"id": plan2["id"]}, new_values={"is_masterplan": True}
        )

        with expand_screen_size(browser=browser):
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

            scale_and_annotate_plan(browser)

            add_opening(browser)
            save_plan_and_success(browser=browser)

            select_from_catalog(browser, ReactPlannerName.KITCHEN.value)
            click_in_global_coordinate(
                browser=browser, pos_x=450, pos_y=550, surface_id="viewer"
            )

            original_items = browser.find_by_xpath(
                "//*[@data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )
            original_areas = browser.find_by_xpath(
                "//*[@data-prototype='areas']",
                wait_time=TIME_TO_WAIT,
            )
            original_lines = browser.find_by_xpath(
                "//*[@data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )
            original_holes = browser.find_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )

            original_nr_of_lines = len(original_lines)
            original_nr_of_items = len(original_items)
            original_nr_of_areas = len(original_areas)
            original_nr_of_holes = len(original_holes)

            # Enter copy paste
            browser.find_by_id("copy-paste-button").first.click()

            click_and_hold_accross_global_coordinates(
                browser=browser,
                start_x=300,
                start_y=300,
                end_x=700,
                end_y=700,
                surface_id="viewer",
            )
            # Open a new plan
            browser.visit(editor_v2_url + f"/{plan2['id']}")
            alert = browser.get_alert()
            assert alert is not None
            alert.accept()

            set_plan_scale(browser)

            # Recreate copypaste from the first plan
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.CONTROL + "v")

            # And paste it
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.CONTROL + "v")

            # Exit copy paste, save (thus ensuring data consistency with BE) & reload
            browser.find_by_id("copy-paste-button").first.click()
            save_plan_and_success(browser=browser)

            browser.reload()

            # There should be the same number of lines, areas & items as in the original plan
            areas = browser.find_by_xpath(
                "//*[@data-prototype='areas']",
                wait_time=TIME_TO_WAIT,
            )
            items = browser.find_by_xpath(
                "//*[@data-prototype='items']",
                wait_time=TIME_TO_WAIT,
            )
            lines = browser.find_by_xpath(
                "//*[@data-prototype='lines']",
                wait_time=TIME_TO_WAIT,
            )

            holes = browser.find_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )
            assert len(areas) == original_nr_of_areas
            assert len(items) == original_nr_of_items
            assert len(lines) == original_nr_of_lines
            assert len(holes) == original_nr_of_holes
