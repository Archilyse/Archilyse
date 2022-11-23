import pytest
from selenium.webdriver.common.keys import Keys

from handlers.editor_v2.schema import ReactPlannerName, ReactPlannerType
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    add_opening,
    save_and_warning,
    save_plan_and_success,
    scale_and_annotate_plan,
    select_from_catalog,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.e2e_browser.utils_editor import click_in_global_coordinate
from tests.utils import do_while_pressing


class TestChangeAnnotationType:
    @pytest.fixture(autouse=True)
    def do_login(self, browser, editor_v2_url):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)

    @staticmethod
    def test_change_annotation_type(
        browser,
        plan_masterplan,
        client_db,
        background_floorplan_image,
        editor_v2_url,
    ):
        """
        When the user is logged
        And selects an annotation (line, hole or item),
        He/She can change its type from the catalog
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

            add_opening(browser=browser, coordinates=(305, 450))
            add_opening(
                browser=browser,
                coordinates=(450, 305),
                opening_type=ReactPlannerName.WINDOW,
            )
            save_plan_and_success(browser=browser)

            # Add two kitchens
            select_from_catalog(browser, ReactPlannerName.KITCHEN.value)
            click_in_global_coordinate(
                browser=browser, pos_x=450, pos_y=550, surface_id="viewer"
            )
            click_in_global_coordinate(
                browser=browser, pos_x=450, pos_y=450, surface_id="viewer"
            )

            # =========== Change an item =========
            # Enter select tool mode
            browser.find_by_id("select-tool-button").first.click()

            # Select the first kitchen (item)
            click_in_global_coordinate(
                browser=browser, pos_x=450, pos_y=550, surface_id="viewer"
            )
            # Select the second kitchen (item)
            with do_while_pressing(browser, Keys.CONTROL):
                click_in_global_coordinate(
                    browser=browser, pos_x=450, pos_y=450, surface_id="viewer"
                )

            # Change the kitchens to showers
            select_from_catalog(browser, ReactPlannerName.SHOWER.value)

            shower_items = browser.find_by_xpath(
                f"//*[@data-testid='item-{ReactPlannerType.SHOWER.value}']",
                wait_time=TIME_TO_WAIT,
            )
            assert len(shower_items) == 2

            # =========== Change two holes =========
            # Enter select tool mode
            browser.find_by_id("select-tool-button").first.click()

            # Select the door (hole)
            click_in_global_coordinate(
                browser=browser, pos_x=305, pos_y=450, surface_id="viewer"
            )
            # Select the window (hole)
            with do_while_pressing(browser, Keys.CONTROL):
                click_in_global_coordinate(
                    browser=browser, pos_x=450, pos_y=305, surface_id="viewer"
                )

            # Change the door and the window to a sliding door
            select_from_catalog(browser, ReactPlannerName.SLIDING_DOOR.value)

            sliding_doors_holes = browser.find_by_xpath(
                f"//*[@data-element-type='{ReactPlannerType.SLIDING_DOOR.value}']",
                wait_time=TIME_TO_WAIT,
            )
            assert len(sliding_doors_holes) == 2

            # =========== Change two lines =========
            # Enter select tool mode
            browser.find_by_id("select-tool-button").first.click()

            # Select a wall (line) with a door (hole)
            click_in_global_coordinate(
                browser=browser, pos_x=300, pos_y=580, surface_id="viewer"
            )
            # Select a wall (line) with a window (hole)
            with do_while_pressing(browser, Keys.CONTROL):
                click_in_global_coordinate(
                    browser=browser, pos_x=320, pos_y=300, surface_id="viewer"
                )

            # Change the walls to a railing
            select_from_catalog(browser, ReactPlannerName.RAILING.value)

            railing_lines = browser.find_by_xpath(
                f"//*[@data-element-type='{ReactPlannerType.RAILING.value}']",
                wait_time=TIME_TO_WAIT,
            )
            assert len(railing_lines) == 2
            assert browser.is_element_not_present_by_xpath(
                "//*[@data-prototype='holes']",
                wait_time=TIME_TO_WAIT,
            )

            save_and_warning(browser=browser)
