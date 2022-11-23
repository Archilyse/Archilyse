from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size


class TestAccessControl:
    @staticmethod
    def test_editor_v2_no_access_without_login(browser, editor_v2_url):
        """
        If the user tries to access editor without login,
        it should be redirected to the login page
        """
        browser.visit(editor_v2_url + "/1")
        assert browser.find_by_text("Sign in", wait_time=TIME_TO_WAIT)

    @staticmethod
    def test_editor_v2_logout(
        browser,
        editor_v2_url,
        plan_classified_scaled,
        background_floorplan_image,
        client_db,
    ):
        """
        Given an editor canvas
        And a logged in Editor user navigating to id
        When the user clicks on the Logout button
        Then the user is redirected to the Login screen
        And after logging in again
        Then the user is redirected to the same plan id that they were attending
        """
        update_plan_with_gcs_image(
            plan_id=plan_classified_scaled["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_classified_scaled['id']}")

            browser.find_by_id("logout-button").first.click()

            assert browser.url.endswith(editor_v2_url + "/login")

            browser.fill("user", "admin")
            browser.fill("password", "admin")
            browser.find_by_xpath(
                "//button[contains(text(), 'Sign in')]",
                wait_time=TIME_TO_WAIT,
            ).first.click()

            wait_for_floorplan_img_load(browser)
            assert browser.url.endswith(
                editor_v2_url + f"/{plan_classified_scaled['id']}"
            )
