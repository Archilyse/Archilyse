import pytest

from brooks.types import AreaType
from handlers import PlanLayoutHandler
from handlers.db import AreaDBHandler, ReactPlannerProjectsDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    add_opening,
    assert_latest_version,
    draw_single_wall,
    press_escape,
    save_plan_and_success,
    scale_and_annotate_plan,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.e2e_browser.utils_editor import assert_plan_is_finished_in_db, make_login
from tests.e2e_utils import SlamUIClient
from tests.utils import switch_to_opened_tab, wait_for_url


def test_editor_v2_exit_without_saving_changes(
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
    If the user makes a change
    And tries to exit
    And alert appears
    If then it saves changes
    It can advance to classification
    If it makes another change
    It cannot advance as changes are not saved
    """
    update_plan_with_gcs_image(
        plan_id=insert_react_planner_data["plan_id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{insert_react_planner_data['plan_id']}")

        # Make a change
        line_coords = [(300, 300), (600, 300)]
        draw_single_wall(browser, line_coords)

        # Trying to exit without saving triggers an alert
        browser.reload()
        alert = browser.get_alert()
        assert alert is not None
        alert.dismiss()  # Do not exit

        # Exit drawing mode to be able to click on Save
        press_escape(browser=browser)

        # If we save changes, we can go to classification
        save_plan_and_success(browser=browser)
        assert browser.find_by_xpath(
            "//button[text()='Go to classification' and not(@disabled)]"
        ).first

        # Making a change without saving disables the go to classification button
        line_coords = [(300, 300), (600, 300)]
        draw_single_wall(browser, line_coords)
        press_escape(browser=browser)

        assert browser.find_by_xpath(
            "//button[text()='Go to classification' and @disabled]"
        ).first

        # We save again to avoid the alert
        save_plan_and_success(browser=browser)
        assert browser.find_by_xpath(
            "//button[text()='Go to classification' and not(@disabled)]"
        ).first


def test_editor_v2_finish_labelling(
    browser, editor_v2_url, plan_masterplan, background_floorplan_image, client_db
):
    """
    Given an unannotated, scaled plan
    When the editor V2 window opens
    Then the user sees the floorplan image without annotations on top of it

    When user annotates it such that there are no blocking violations
    And saves the plan
    Then the annotations of the plan are saved
    And task to generate 1 brooks area has been started
    And the plan is marked as 'finished' in the database
    And the plan has the scale factor set.

    And the user can continue to classification step in old pipeline
    If the user tries to rescale the plan in the old pipeline
    An error appears
    """
    OLD_PIPELINE_CLASSIFICATION_URL = "/classification"
    update_plan_with_gcs_image(
        plan_id=plan_masterplan["id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )

    assert len(ReactPlannerProjectsDBHandler.find()) == 0

    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

        wait_for_floorplan_img_load(browser)

        scale_and_annotate_plan(browser)

        add_opening(browser)
        save_plan_and_success(browser=browser)
        assert_latest_version(plan_id=plan_masterplan["id"])

        assert len(ReactPlannerProjectsDBHandler.find()) == 1
        assert len(AreaDBHandler.find(plan_id=plan_masterplan["id"])) == 1
        # Make sure the area plot in the FE matches what we have in the BE
        area_size = list(
            PlanLayoutHandler(plan_id=plan_masterplan["id"])
            .get_layout(scaled=True)
            .areas
        )[0].footprint.area

        # Depends on how the CI draws, the expected value may change
        assert area_size == pytest.approx(7.82, abs=10**-2)
        assert_plan_is_finished_in_db(plan_id=plan_masterplan["id"])

        # User can click on a button to go to classification
        browser.find_by_text(
            "Go to classification", wait_time=TIME_TO_WAIT
        ).first.click()

        switch_to_opened_tab(browser)

        # Assert we are in classification
        wait_for_url(browser, OLD_PIPELINE_CLASSIFICATION_URL)


@pytest.fixture
def dummy_area(plan):
    AreaDBHandler.add(
        plan_id=plan["id"],
        coord_x=1.23,
        coord_y=-4.56,
        area_type=AreaType.OIL_TANK.name,
        scaled_polygon="",
    )


def test_editor_scaling_navigation_tab_redirects_to_editor_v2(
    browser,
    dummy_area,
    plan_classified_scaled,
    recreate_test_gcp_client_bucket,
    add_background_plan_image_to_gcloud,
    login_url,
):
    """
    Given a team member user attending the classification screen
    When the 'Scaling' tab in the navbar is clicked
    Then the user is redirected to the new editor page.
    """
    make_login(browser, login_url, "ADMIN")
    add_background_plan_image_to_gcloud(plan_info=plan_classified_scaled)

    classification_url = SlamUIClient._classification_url_plan(
        plan_id=plan_classified_scaled["id"]
    )
    browser.visit(classification_url)
    browser.find_by_text("Editor").first.click()
    browser.driver.switch_to.window(browser.driver.window_handles[-1])
    assert "v2/editor/" in browser.url
