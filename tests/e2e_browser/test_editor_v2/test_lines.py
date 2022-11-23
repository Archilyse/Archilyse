from selenium.webdriver.common.keys import Keys

from handlers.db import AreaDBHandler
from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import ReactPlannerName
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    DEFAULT_WALL_THICKNESS,
    draw_single_wall,
    save_plan_and_success,
    select_from_catalog,
    set_plan_scale,
    team_member_login,
    update_plan_with_gcs_image,
)
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.e2e_browser.utils_editor import (
    click_in_global_coordinate,
    move_in_global_coordinate,
)


class TestLineInteraction:
    @staticmethod
    def test_editor_v2_split_area(
        browser,
        editor_v2_url,
        plan,
        background_floorplan_image,
        client_db,
        insert_react_planner_data,
    ):
        """
        Given an annotated scaled plan
        Go to the editor2 window
        When the editor window opens
        User sees floorplan with annotations
        When the user selects the area splitter item
        And splits one area in two and save
        We have one area more in the db
        """
        update_plan_with_gcs_image(
            plan_id=insert_react_planner_data["plan_id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        plan_id = insert_react_planner_data["plan_id"]
        original_plan = ReactPlannerHandler().get_by_migrated(plan_id=plan_id)
        areas = original_plan["data"]["layers"]["layer-1"]["areas"]
        original_number_of_areas = len(areas)

        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_id}")

            assert browser.find_by_css(".centered", wait_time=TIME_TO_WAIT).first
            # Open catalog and pick 'Area splitter' element
            browser.find_by_id("catalog-button").first.click()
            browser.find_by_text(ReactPlannerName.AREA_SPLITTER.value).first.click()

            # Split one area in two
            click_in_global_coordinate(
                browser=browser, pos_x=740, pos_y=650, surface_id="viewer"
            )
            click_in_global_coordinate(
                browser=browser, pos_x=930, pos_y=650, surface_id="viewer"
            )

            # Exit drawing mode and save
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.ESCAPE)

            save_plan_and_success(browser=browser)
            # Asserts that we have one area more
            updated_plan = ReactPlannerHandler().get_by_migrated(plan_id=plan_id)
            updated_areas = updated_plan["data"]["layers"]["layer-1"]["areas"]
            new_number_of_areas = len(updated_areas)

            assert (original_number_of_areas + 1) == new_number_of_areas
            assert len(AreaDBHandler.find(plan_id=plan_id)) == new_number_of_areas

    @staticmethod
    def test_editor_v2_wall_thickness_interaction(
        browser,
        editor_v2_url,
        plan_masterplan,
        background_floorplan_image,
        client_db,
    ):
        """
        When the user draw a wall
        It can increase its thickness pressing '+'
        If the user draws a new wall
        The increased thickness is used
        And it can decrease thickness using '-'
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")
            set_plan_scale(browser)

            # Draw a single wall with default thickness
            line_coords = [(300, 300), (600, 300)]
            draw_single_wall(browser, line_coords)

            assert (
                browser.find_by_id("width", wait_time=TIME_TO_WAIT).value
                == f"{DEFAULT_WALL_THICKNESS}"
            )

            # Increase thickness
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.ADD)
            assert browser.find_by_id("width", wait_time=TIME_TO_WAIT).value == "21"

            # Draw a new wall that should use previous thickness
            active_web_element.send_keys(Keys.ESCAPE)
            line_coords = [(350, 350), (650, 350)]
            draw_single_wall(browser, line_coords)
            assert browser.find_by_id("width", wait_time=TIME_TO_WAIT).value == "21"

            # Decrease thickness
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.SUBTRACT)
            active_web_element.send_keys(Keys.SUBTRACT)
            assert browser.find_by_id("width", wait_time=TIME_TO_WAIT).value == "19"

            # Ensure saving updated walls is fine (so contract between FE - BE in line properties is respected)
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.ESCAPE)
            save_plan_and_success(browser=browser)

    @staticmethod
    def test_editor_v2_reference_line_change(
        browser,
        editor_v2_url,
        plan_masterplan,
        background_floorplan_image,
        client_db,
    ):
        """
        When the user draws the same wall twice with different reference lines (pressing f)
        Then both walls final positions are not the same and create a bigger rectangle
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")
            set_plan_scale(browser)

            y_pixel = 300
            x_initial = 300
            x_final = 400
            for i in range(2):
                select_from_catalog(browser, "Wall")
                click_in_global_coordinate(
                    browser=browser, pos_x=x_initial, pos_y=y_pixel, surface_id="viewer"
                )
                # To be able to change the reference line we have to start drawing the wall, so we move the cursor
                move_in_global_coordinate(
                    browser=browser, pos_x=x_final, pos_y=y_pixel, surface_id="viewer"
                )

                # the reference line is saved and the next walls are always using the same one, so we will press it only
                # the 2nd time
                if i == 1:
                    active_web_element = browser.driver.switch_to.active_element
                    active_web_element.send_keys("f")

                click_in_global_coordinate(
                    browser=browser, pos_x=x_final, pos_y=y_pixel, surface_id="viewer"
                )
                active_web_element = browser.driver.switch_to.active_element
                active_web_element.send_keys(Keys.ESCAPE)

            save_plan_and_success(browser=browser)
            # Asserts that we have one area more
            updated_plan = ReactPlannerHandler().get_by_migrated(
                plan_id=plan_masterplan["id"]
            )
            reference_lines = {
                line["properties"]["referenceLine"]
                for line in updated_plan["data"]["layers"]["layer-1"]["lines"].values()
            }
            assert reference_lines == {"OUTSIDE_FACE", "INSIDE_FACE"}
