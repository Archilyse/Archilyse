import time
from typing import Dict, List, Tuple

from contexttimer import timer
from selenium.webdriver.common.keys import Keys

from brooks.types import FeatureType
from common_utils.constants import USER_ROLE
from common_utils.logger import logger
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler
from handlers.editor_v2.schema import CURRENT_REACT_ANNOTATION_VERSION, ReactPlannerName
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import make_login
from tests.e2e_browser.utils_editor import (
    clear_input,
    click_in_app_surface_center,
    click_in_global_coordinate,
    move_in_global_coordinate,
)
from tests.utils import add_plan_image_to_gcs, recreate_test_gcp_client_bucket_method


def admin_login(browser, editor_v2_url):
    make_login(
        browser=browser,
        admin_url=editor_v2_url,
        user_type=USER_ROLE.ADMIN.name,
        expected_element_id="home-header",
    )


DEFAULT_WALL_THICKNESS = "20"


def exit_drawing_mode(browser):
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.ESCAPE)


def select_from_catalog(browser, element_name):
    catalog = browser.find_by_id("catalog-toolbar")
    if not catalog:
        browser.find_by_id("catalog-button").first.click()
    browser.find_by_xpath(f"//div/small[text()='{element_name}']").first.click()


def draw_single_wall(browser, line_coords):
    select_from_catalog(browser, "Wall")

    for (x, y) in line_coords:
        click_in_global_coordinate(
            browser=browser, pos_x=x, pos_y=y, surface_id="viewer"
        )


def wait_for_floorplan_img_load(browser):
    assert browser.find_by_css(
        ".floorplan-img-loaded", wait_time=TIME_TO_WAIT * 2
    ).first


def wait_for_floorplan_img_loaded_and_centered(browser):
    assert browser.find_by_css(".floorplan-img-loaded", wait_time=TIME_TO_WAIT).first
    assert browser.find_by_css(".centered", wait_time=TIME_TO_WAIT).first


def set_plan_scale(
    browser,
    coords: List[Tuple[int, int]] = None,
    with_wait=False,
    scale_factor: float = 3,
):
    if not coords:
        coords = [(300, 300), (600, 300)]

    def take_single_measurement():
        for (x, y) in coords:
            click_in_global_coordinate(
                browser=browser, pos_x=x, pos_y=y, surface_id="viewer"
            )
            if with_wait:
                time.sleep(1)

        # Erase the default distance
        area_measure = "distance" if len(coords) == 2 else "area-size"
        browser.type(area_measure, 0)  # To focus on the input
        clear_input(browser)

        # Set new scale and validate
        browser.type(area_measure, scale_factor)
        active_web_element = browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ENTER)

    # Scale tool loaded
    assert browser.find_by_text("Scale mode").first

    for _ in range(2):
        take_single_measurement()
        press_escape(browser=browser)  # So we deselect the drawing tool
        browser.find_by_text("Save measure").first.click()

    # Match snackbar text instead of id to avoid matching the measure success one
    assert browser.find_by_text("Plan scale set", wait_time=TIME_TO_WAIT).first


def set_plan_scale_with_page_specs(browser, paper_format, scale_ratio):
    # Scale tool loaded
    assert browser.find_by_text("Scale mode").first

    browser.select("paperFormat", paper_format)
    browser.type("scaleRatio", scale_ratio)

    browser.find_by_text("Validate scale using format/ratio").first.click()

    assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT).first


def zoom_plan_out(browser):
    # turns on zoom out tool so that if user clicks on plan it zooms out
    # since we don't have any UI control to turn this tool on, we do it via redux actions
    browser.execute_script(
        "ReactPlanner.do([ReactPlanner.viewer2DActions.selectToolZoomOut()])"
    )
    # clicks 10 times to make plan properly visible
    for _ in range(10):
        click_in_app_surface_center(browser, surface_id="viewer")


def press_escape(browser):
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.ESCAPE)


def draw_2_valid_item_in_area(browser):
    select_from_catalog(browser, ReactPlannerName.KITCHEN.value)

    test_coords = [
        (300, 300),  # This one should fail
        (450, 450),  # This one places the kitchen in the corner of the area
        (351, 351),  # This one places the kitchen in the corner of the area
    ]
    for (x, y) in test_coords:
        click_in_global_coordinate(
            browser=browser, pos_x=x, pos_y=y, surface_id="viewer"
        )
    press_escape(browser=browser)


def draw_all_items_in_area(browser):
    for feature in FeatureType:
        if feature == FeatureType.NOT_DEFINED:
            continue
        select_from_catalog(browser, getattr(ReactPlannerName, feature.name).value)

        click_in_global_coordinate(
            browser=browser, pos_x=500, pos_y=450, surface_id="viewer"
        )
        press_escape(browser=browser)


def extend_size_of_items(browser):
    for item in browser.find_by_xpath("//*[@data-prototype='items']"):
        item.click()
        # The app needs time to react to the click and for the form to appear at the right
        time.sleep(0.3)
        for _ in range(10):
            browser.find_by_id("incr-width", wait_time=TIME_TO_WAIT).click()
            browser.find_by_id("incr-length", wait_time=TIME_TO_WAIT).click()
        press_escape(browser=browser)


def scale_and_annotate_plan(browser):
    rectangle_coords = [
        (300, 300),
        (600, 300),
        (600, 600),
        (300, 600),
        (300, 300),
    ]

    set_plan_scale(browser)
    # Open catalog and pick 'Wall' element
    select_from_catalog(browser, ReactPlannerName.WALL.value)

    # Draw rectangle on the plan
    for (x, y) in rectangle_coords:
        click_in_global_coordinate(
            browser=browser, pos_x=x, pos_y=y, surface_id="viewer"
        )

    # Exit drawing mode
    press_escape(browser=browser)

    browser.find_by_id("save-scene-button").first.click()

    # The plan will be saved with one error (the enclosed walls have no holes) and a warning will appear
    assert browser.find_by_id("notification-warning", wait_time=TIME_TO_WAIT)


def save_plan_and_success(browser):
    browser.find_by_id("save-scene-button").first.click()
    assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT)


def save_and_warning(browser):
    browser.find_by_id("save-scene-button").first.click()
    assert browser.find_by_id("notification-warning", wait_time=TIME_TO_WAIT)


def add_opening(
    browser,
    coordinates=(305, 450),
    opening_type: ReactPlannerName = ReactPlannerName.ENTRANCE_DOOR,
):
    door_x, door_y = coordinates

    select_from_catalog(browser, opening_type.value)

    move_in_global_coordinate(
        browser=browser, pos_x=door_x, pos_y=door_y, surface_id="viewer"
    )

    click_in_global_coordinate(
        browser=browser, pos_x=door_x, pos_y=door_y, surface_id="viewer"
    )

    exit_drawing_mode(browser=browser)


def team_member_login(browser, editor_v2_url):
    make_login(
        browser=browser,
        admin_url=editor_v2_url,
        user_type=USER_ROLE.TEAMMEMBER.name,
        expected_element_id="home-header",
    )


def plan_with_module_background_image(client_id: int, image_content: bytes) -> Dict:
    """Generally client id is always 1 so the cache kind of works correctly"""
    recreate_test_gcp_client_bucket_method(client_id=client_id)

    return add_plan_image_to_gcs(
        client_id=client_id,
        image_content=image_content,
    )


@timer(logger=logger)
def update_plan_with_gcs_image(plan_id: int, client_id: int, image_content: bytes):
    cached_plan = plan_with_module_background_image(
        client_id=client_id, image_content=image_content
    )
    return PlanDBHandler.update(
        item_pks={"id": plan_id},
        new_values=dict(
            image_width=cached_plan["image_width"],
            image_height=cached_plan["image_height"],
            image_gcs_link=cached_plan["image_gcs_link"],
            image_mime_type=cached_plan["image_mime_type"],
            image_hash=cached_plan["image_hash"],
        ),
    )


def assert_image_loaded(browser):
    assert browser.find_by_css(".floorplan-img-loaded", wait_time=TIME_TO_WAIT).first


def assert_latest_version(plan_id: int):
    updated_plan = ReactPlannerProjectsDBHandler.get_by(plan_id=plan_id)
    assert updated_plan["data"]["version"] == CURRENT_REACT_ANNOTATION_VERSION
