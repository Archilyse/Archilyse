import os
import time
from distutils.util import strtobool

import pytest
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from shapely.geometry import Point

from brooks.util.projections import project_geometry
from common_utils.constants import REGION
from handlers import PlanLayoutHandler
from handlers.db import PlanDBHandler, SiteDBHandler
from tests.constants import FLAKY_RERUNS, TIME_TO_WAIT
from tests.e2e_browser.utils_editor import (
    assert_basic_elements_are_visible_in_page,
    assert_error_is_visible_in_page,
    assert_snack_bar_successful,
    make_login,
)
from tests.e2e_browser.utils_pipeline import (
    STATUS_NAVIGATION_AVAILABLE,
    STATUS_NAVIGATION_COMPLETED,
    STATUS_NAVIGATION_DISABLED,
    assert_georeference_is_visible_in_page,
    assert_site_navigation_is_visible_in_page,
    editor_click_help_button,
    wait_for_browser_condition,
)


@pytest.fixture(autouse=True)
def do_login(browser, login_url):
    make_login(browser, login_url)


def test_georeference_window_appears_with_an_error(
    browser, georeference_url_wrong_plan
):
    """
    Go to the georeference window as a non-dev user and a plan_id that doesn't exist
    When the georeference window opens we check that the users gets an error
    """
    browser.visit(georeference_url_wrong_plan)

    assert_error_is_visible_in_page(browser=browser)


def test_georeference_window_appears_and_help_modal_works(
    browser, plans_ready_for_georeferencing
):
    """
    Go to the georeference window as a non-dev user
    When the georeference window opens we check that the basic elements are displayed
    """
    from tests.e2e_utils import SlamUIClient

    browser.visit(
        SlamUIClient._georeference_url_plan(
            plan_id=plans_ready_for_georeferencing[0]["id"]
        )
    )

    assert_georeference_is_visible_in_page(browser=browser)
    assert_basic_elements_are_visible_in_page(browser=browser)

    assert_site_navigation_is_visible_in_page(
        browser=browser,
        status_editor=STATUS_NAVIGATION_COMPLETED,
        status_classification=STATUS_NAVIGATION_COMPLETED,
        status_georeference=STATUS_NAVIGATION_AVAILABLE,
        status_splitting=STATUS_NAVIGATION_DISABLED,
        status_linking=STATUS_NAVIGATION_DISABLED,
    )

    editor_click_help_button(browser=browser)

    assert browser.find_by_xpath(
        "//h5[text() = 'Controls and Keyboard Shortcuts']"
    ).first

    help_instructions = browser.find_by_css(
        "help-dialog-georeference-component > ul > li"
    )
    assert len(help_instructions) >= 5


@pytest.fixture
def expected_new_rotation():
    if strtobool(os.environ["BROWSER_HEADLESS"]):
        return 227.4690
    else:
        return 244.65038


@pytest.fixture
def expected_distance_after_translation():
    # The distance of 4 meter is approximate, it makes sense but it seems to change depending
    # on the size of the screen.
    if strtobool(os.environ["BROWSER_HEADLESS"]):
        return 2.46535
    else:
        return 3.055774


@pytest.mark.flaky(reruns=FLAKY_RERUNS)
def test_georeference_display_already_georeferenced_layouts(
    recreate_test_gcp_bucket,
    browser,
    login,
    plans_ready_for_georeferencing,
    expected_distance_after_translation,
    expected_new_rotation,
    upload_building_surroundings_to_google_cloud,
    fixtures_path,
):
    from tests.e2e_utils import SlamUIClient

    upload_building_surroundings_to_google_cloud(
        filepath=fixtures_path.joinpath("georeferencing/2614896.8_1268188.6.json"),
        site_id=plans_ready_for_georeferencing[0]["site_id"],
    )

    browser.visit(
        SlamUIClient._georeference_url_plan(
            plan_id=plans_ready_for_georeferencing[0]["id"]
        )
    )

    assert browser.is_element_visible_by_xpath(
        "//div[contains(@class, 'ol-scale-line-inner')]", wait_time=TIME_TO_WAIT
    )
    assert browser.execute_script("return globalSource.getFeatures().length") == 1
    assert browser.execute_script("return decorationSource.getFeatures().length") == 26

    wait_for_browser_condition(
        browser,
        "return decorationFloorsSource.getFeatures().length > 0",
        wait_time=TIME_TO_WAIT * 3,
    )
    assert (
        browser.execute_script("return decorationFloorsSource.getFeatures().length")
        == 1
    )
    assert_site_navigation_is_visible_in_page(
        browser=browser,
        status_editor=STATUS_NAVIGATION_COMPLETED,
        status_classification=STATUS_NAVIGATION_COMPLETED,
        status_georeference=STATUS_NAVIGATION_AVAILABLE,
        status_splitting=STATUS_NAVIGATION_DISABLED,
        status_linking=STATUS_NAVIGATION_DISABLED,
    )
    # Move the plan some pixels and check the result is correct in BE
    action = ActionChains(browser.driver)
    action.drag_and_drop_by_offset(
        browser.find_by_xpath("//div[@class = 'ol-viewport']").first._element, 100, 100
    ).perform()
    browser.find_by_id("save_button").first.click()
    assert_snack_bar_successful(
        browser=browser, msg_to_check="Georeferenced saved successfully"
    )
    plan_translated = PlanDBHandler.get_by(id=plans_ready_for_georeferencing[0]["id"])
    site = SiteDBHandler.get_by(id=plans_ready_for_georeferencing[0]["site_id"])
    # We are shifting the footprint to the right and down, so longitude is increasing and latitude decreasing
    assert plan_translated["georef_x"] > site["lon"]
    assert plan_translated["georef_y"] < site["lat"]
    plan_projected = project_geometry(
        geometry=Point(plan_translated["georef_x"], plan_translated["georef_y"]),
        crs_from=REGION.LAT_LON,
        crs_to=REGION.CH,
    )
    site_projected = project_geometry(
        geometry=Point(site["lon"], site["lat"]),
        crs_from=REGION.LAT_LON,
        crs_to=REGION.CH,
    )
    assert site_projected.distance(plan_projected) == pytest.approx(
        expected_distance_after_translation, abs=10**-4
    )

    # We also check the rotation mode is correctly understood in the BE
    action = ActionChains(browser.driver)
    action.key_down(Keys.CONTROL)
    action.drag_and_drop_by_offset(
        browser.find_by_xpath("//div[@class = 'ol-viewport']").first._element, 100, 100
    )
    action.key_up(Keys.CONTROL)
    action.perform()
    browser.find_by_id("save_button").first.click()
    assert_snack_bar_successful(
        browser=browser, msg_to_check="Georeferenced saved successfully"
    )
    # FE doesn't seem to be really waiting for the BE response to launch the snackbar so DB is not sync here
    time.sleep(1.0)
    plan_after_rotation = PlanDBHandler.get_by(
        id=plans_ready_for_georeferencing[0]["id"]
    )
    assert plan_after_rotation["georef_x"] == plan_translated["georef_x"]
    assert plan_after_rotation["georef_y"] == plan_translated["georef_y"]
    # When executed locally the angle is 235.827
    assert plan_after_rotation["georef_rot_angle"] == pytest.approx(
        expected_new_rotation, abs=10**-2
    )

    # Finally we check the footprint is correctly represented in the right coordinates
    layout_footprint = (
        PlanLayoutHandler(
            plan_id=plan_after_rotation["id"],
            plan_info=plan_after_rotation,
            site_info=site,
        )
        .get_layout(scaled=True, georeferenced=True)
        .footprint
    )
    footprint_lat_lon = project_geometry(
        geometry=layout_footprint,
        crs_from=REGION.CH,
        crs_to=REGION.LAT_LON,
    )
    # checked that visually matches the georeferencing UI against OSM based data like:
    # https://www.mapquest.com/latlng/47.56429534606357,7.636794665284124?zoom=0
    # https://www.mapquest.com/latlng/47.5641171403755,7.636441377818699?zoom=0
    assert footprint_lat_lon.bounds == pytest.approx(
        (
            7.636441377818699,
            47.5641171403755,
            7.636794665284124,
            47.56429534606357,
        ),
        abs=10**-3,
    )
