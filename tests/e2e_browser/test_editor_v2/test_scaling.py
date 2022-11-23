import pytest

from handlers.editor_v2 import ReactPlannerHandler
from tests.constants import FLAKY_RERUNS, TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    assert_image_loaded,
    assert_latest_version,
    set_plan_scale,
    set_plan_scale_with_page_specs,
    team_member_login,
    update_plan_with_gcs_image,
)
from tests.e2e_browser.utils_admin import expand_screen_size


class TestScaling:
    @staticmethod
    def test_editor_v2_scale_plan_with_line_n_check_version(
        browser, editor_v2_url, plan_masterplan, background_floorplan_image, client_db
    ):
        """
        Given an unannotated plan masterplan
        Go to the editor2 window
        When the editor window opens
        The scale item is shown and the user draws a line
        When the user adjusts the real distance and validates
        The plan is scaled
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")
            # A snackbars telling us to scale the plan appears
            assert browser.find_by_id("notification-info", wait_time=TIME_TO_WAIT)

            set_plan_scale(browser)

            # Ensure plan has been updated in the DB
            updated_plan = ReactPlannerHandler().get_by_migrated(
                plan_id=plan_masterplan["id"]
            )
            assert updated_plan["data"]["scale"] is not None
            assert_latest_version(plan_id=plan_masterplan["id"])
            assert_image_loaded(browser=browser)

    @staticmethod
    @pytest.mark.flaky(reruns=FLAKY_RERUNS)
    def test_editor_v2_scale_plan_with_polygon_n_check_version(
        browser, editor_v2_url, plan_masterplan, background_floorplan_image, client_db
    ):
        """
        Given an unannotated plan masterplan
        Go to the editor2 window
        When the editor window opens
        The scale item is shown and the user draws a polygon
        When the user adjusts the real distance and validates
        The plan is scaled
        If we scale with the same shape over and over
        It has the same area size as it uses the current scale
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")
            # A snackbars telling us to scale the plan appears
            assert browser.find_by_id("notification-info", wait_time=TIME_TO_WAIT)

            polygon_coords = [
                (300, 300),
                (600, 300),
                (600, 600),
                (300, 600),
                (300, 300),
            ]
            # Scale tool loaded
            assert browser.find_by_text("Scale mode").first

            set_plan_scale(browser=browser, coords=polygon_coords, scale_factor=25)
            # Ensure plan has been updated in the DB
            updated_plan = ReactPlannerHandler().get_by_migrated(
                plan_id=plan_masterplan["id"]
            )
            assert updated_plan["data"]["scale"] is not None
            assert_latest_version(plan_id=plan_masterplan["id"])
            assert_image_loaded(browser=browser)

    @staticmethod
    def test_editor_v2_scale_plan_with_page_specs(
        browser, editor_v2_url, plan_masterplan, background_floorplan_image, client_db
    ):
        """
        Given an unannotated plan masterplan
        Go to the editor2 window
        When the editor window opens
        The scale item is shown
        If the user enters page format and scale ratio and validates
        The plan is scaled
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")
            # A snackbars telling us to scale the plan appears
            assert browser.find_by_id("notification-info", wait_time=TIME_TO_WAIT)

            set_plan_scale_with_page_specs(
                browser=browser, paper_format="A0", scale_ratio=5
            )

            # Ensure plan has been updated in the DB
            updated_plan = ReactPlannerHandler().get_by_migrated(
                plan_id=plan_masterplan["id"]
            )
            assert updated_plan["data"]["scale"] is not None
            assert_latest_version(plan_id=plan_masterplan["id"])
            assert_image_loaded(browser=browser)
