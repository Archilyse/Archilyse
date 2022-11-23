from time import sleep

import pytest

from handlers.db import PlanDBHandler, SiteDBHandler
from tests.constants import PERCY_TIME_TO_WAIT, TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    admin_login,
    select_from_catalog,
    set_plan_scale,
)
from tests.e2e_browser.utils_editor import (
    assert_basic_elements_are_visible_in_page,
    click_in_global_coordinate,
    make_login,
    wait_for_preview_img,
)
from tests.e2e_browser.utils_pipeline import (
    STATUS_NAVIGATION_AVAILABLE,
    STATUS_NAVIGATION_COMPLETED,
    STATUS_NAVIGATION_DISABLED,
    assert_linking_is_visible_in_page,
    assert_site_navigation_is_visible_in_page,
)
from tests.e2e_utils import SlamUIClient
from tests.percy_tests.utils_percy import take_screenshot


@pytest.fixture(autouse=True)
def do_login(browser, login_url):
    make_login(browser, login_url, user_type="ADMIN")


@pytest.fixture
def plan_georeferenced_streetless_area(plans_ready_for_georeferencing):
    site_lon = 8.058831854979383
    site_lat = 46.590042426785764
    SiteDBHandler.update(
        item_pks={"id": plans_ready_for_georeferencing[0]["site_id"]},
        new_values=dict(lon=site_lon, lat=site_lat),
    )
    PlanDBHandler.update(
        item_pks=dict(id=plans_ready_for_georeferencing[1]["id"]),
        new_values=dict(
            georef_x=site_lon + 0.0001,  # 10 meters aprox
            georef_y=site_lat + 0.0001,  # 10 meters aprox
        ),
    )
    return plans_ready_for_georeferencing


def test_georeference_screenshot(
    recreate_test_gcp_bucket, browser, login, plan_georeferenced_streetless_area
):
    """
    Go to the georeference window as a non-dev user
    We take an screenshot
    """
    browser.visit(
        SlamUIClient._georeference_url_plan(
            plan_id=plan_georeferenced_streetless_area[0]["id"]
        )
    )

    assert browser.is_element_visible_by_xpath(
        "//div[contains(@class, 'ol-scale-line-inner')]", wait_time=TIME_TO_WAIT
    )
    sleep(10)
    assert take_screenshot(
        browser,
        "test_pipeline_georeference_view",
        wait_time=2 * PERCY_TIME_TO_WAIT,
    )


def test_linking_screenshot(
    browser,
    recreate_test_gcp_client_bucket,
    linking_url_default_plan,
    plan,
    add_background_plan_image_to_gcloud,
):
    """
    Go to the linking window as a non-dev user
    When the linking window opens we check that the basic elements are displayed
    We take an screenshot
    """
    add_background_plan_image_to_gcloud(plan_info=plan)
    browser.visit(linking_url_default_plan)

    wait_for_preview_img(browser)

    assert_linking_is_visible_in_page(browser=browser)
    assert_basic_elements_are_visible_in_page(browser=browser)

    assert_site_navigation_is_visible_in_page(
        browser=browser,
        status_editor=STATUS_NAVIGATION_COMPLETED,
        status_classification=STATUS_NAVIGATION_COMPLETED,
        status_splitting=STATUS_NAVIGATION_COMPLETED,
        status_georeference=STATUS_NAVIGATION_COMPLETED,
        status_linking=STATUS_NAVIGATION_COMPLETED,
    )

    assert take_screenshot(
        browser, "test_pipeline_linking_view", wait_time=2 * PERCY_TIME_TO_WAIT
    )


class TestReactPlanVisualization:
    def close_unsaved_changes_alert(self, browser):
        alert = browser.get_alert()
        alert.accept()

    def draw_rectangle(self, browser, reference_line="Center"):
        DEFAULT_REFERENCE_LINE = "Center"
        rectangle_coords = [
            (300, 300),
            (600, 300),
            (600, 600),
            (300, 600),
            (300, 300),
        ]
        # Draw rectangle using outside reference line
        select_from_catalog(browser, "Wall")

        # Change the reference line after drawing the first wall
        (x, y) = rectangle_coords[0]
        click_in_global_coordinate(
            browser=browser, pos_x=x, pos_y=y, surface_id="viewer"
        )
        browser.find_by_text(
            DEFAULT_REFERENCE_LINE, wait_time=TIME_TO_WAIT
        ).first.click()
        browser.find_by_text(reference_line, wait_time=TIME_TO_WAIT).first.click()

        for (x, y) in rectangle_coords[1:]:
            click_in_global_coordinate(
                browser=browser, pos_x=x, pos_y=y, surface_id="viewer"
            )

    def test_classification_screenshot_react_data(
        self,
        browser,
        recreate_test_gcp_client_bucket,
        plan_annotated,
        floor,
        add_background_plan_image_to_gcloud,
        react_planner_background_image_one_unit,
        editor_v2_url,
    ):
        add_background_plan_image_to_gcloud(plan_info=plan_annotated)
        admin_login(browser, editor_v2_url)

        browser.visit(
            SlamUIClient._classification_url_plan(plan_id=plan_annotated["id"])
        )
        assert_site_navigation_is_visible_in_page(
            browser=browser,
            status_editor=STATUS_NAVIGATION_COMPLETED,
            status_classification=STATUS_NAVIGATION_AVAILABLE,
            status_splitting=STATUS_NAVIGATION_DISABLED,
            status_georeference=STATUS_NAVIGATION_DISABLED,
            status_linking=STATUS_NAVIGATION_DISABLED,
        )
        assert take_screenshot(
            browser,
            "test_pipeline_classification_react_view",
        )

    def test_editor_validation_error_positions_correct_react(
        self,
        browser,
        recreate_test_gcp_client_bucket,
        plan,
        floor,
        add_background_plan_image_to_gcloud,
        react_planner_floorplan_annotation_w_errors,
        editor_v2_url,
    ):
        from handlers.editor_v2 import ReactPlannerHandler

        add_background_plan_image_to_gcloud(plan_info=plan)

        react_planner_floorplan_annotation_w_errors[
            "scale"
        ] = 1.4  # To make the impact of the scale factor visible we increase it
        ReactPlannerHandler().store_plan_data(
            plan_id=plan["id"],
            plan_data=react_planner_floorplan_annotation_w_errors,
            validated=True,
        )
        admin_login(browser, editor_v2_url)

        browser.visit(editor_v2_url + f"/{plan['id']}")

        assert take_screenshot(
            browser,
            "test_editor_validation_error_positions_correct_react",
        )

    def test_reference_lines_editor_react(
        self,
        browser,
        recreate_test_gcp_client_bucket,
        plan_masterplan,
        floor,
        add_background_plan_image_to_gcloud,
        react_planner_floorplan_annotation_w_errors,
        editor_v2_url,
    ):
        add_background_plan_image_to_gcloud(plan_info=plan_masterplan)

        admin_login(browser, editor_v2_url)

        browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

        set_plan_scale(browser, with_wait=True)

        self.draw_rectangle(browser, reference_line="Center")

        assert take_screenshot(
            browser,
            "test_reference_lines_editor_react_center_line",
        )

        browser.reload()
        self.close_unsaved_changes_alert(browser)

        self.draw_rectangle(browser, reference_line="Outside face")
        assert take_screenshot(
            browser,
            "test_reference_lines_editor_react_outside_line",
        )

        browser.reload()
        self.close_unsaved_changes_alert(browser)

        self.draw_rectangle(browser, reference_line="Inside face")
        assert take_screenshot(
            browser,
            "test_reference_lines_editor_react_inside_line",
        )
        # Reload and dismiss the alert one more time so next tests are not affected
        browser.reload()
        self.close_unsaved_changes_alert(browser)

    def test_splitting_brooks_on_top_of_image(
        self,
        browser,
        celery_eager,
        add_background_plan_image_to_gcloud,
        recreate_test_gcp_client_bucket,
        make_react_annotation_fully_pipelined,
        react_planner_background_image_one_unit,
        editor_v2_url,
    ):
        react_plan_fully_pipelined = make_react_annotation_fully_pipelined(
            react_planner_background_image_one_unit
        )
        add_background_plan_image_to_gcloud(
            plan_info=react_plan_fully_pipelined["plan"]
        )
        admin_login(browser, editor_v2_url)
        browser.visit(
            SlamUIClient._splitting_url_plan(
                plan_id=react_plan_fully_pipelined["plan"]["id"]
            )
        )

        assert take_screenshot(
            browser,
            "test_splitting_brooks_on_top_of_image_react",
        )

    def test_linking_brooks_on_top_of_image(
        self,
        browser,
        celery_eager,
        add_background_plan_image_to_gcloud,
        recreate_test_gcp_client_bucket,
        react_planner_background_image_one_unit,
        make_react_annotation_fully_pipelined,
        editor_v2_url,
    ):
        react_plan_fully_pipelined = make_react_annotation_fully_pipelined(
            react_planner_background_image_one_unit
        )
        add_background_plan_image_to_gcloud(
            plan_info=react_plan_fully_pipelined["plan"]
        )
        admin_login(browser, editor_v2_url)
        browser.visit(
            SlamUIClient._linking_url_plan(
                plan_id=react_plan_fully_pipelined["plan"]["id"]
            )
        )

        assert take_screenshot(
            browser,
            "test_linking_brooks_on_top_of_image_react",
        )
