from selenium.webdriver.common.keys import Keys

from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.test_editor_v2.utils import (
    team_member_login,
    update_plan_with_gcs_image,
    zoom_plan_out,
)
from tests.e2e_browser.utils_admin import expand_screen_size
from tests.utils import do_while_pressing


def test_editor_v2_hide_annotations_by_pressing_space(
    browser,
    editor_v2_url,
    insert_react_planner_data,
    background_floorplan_image,
    client_db,
):
    """
    Given an annotated scaled plan
    Go to the editor2 window
    When the editor window opens
    User sees floorplan with annotations
    When user presses and holds space bar
    Annotations of the plan become invisible
    When user stops pressing
    Annotations of the plan become visible again
    """
    update_plan_with_gcs_image(
        plan_id=insert_react_planner_data["plan_id"],
        client_id=client_db["id"],
        image_content=background_floorplan_image,
    )
    with expand_screen_size(browser=browser):
        team_member_login(browser=browser, editor_v2_url=editor_v2_url)
        browser.visit(editor_v2_url + f"/{insert_react_planner_data['plan_id']}")

        zoom_plan_out(browser)

        assert browser.is_element_present_by_css("polygon", wait_time=TIME_TO_WAIT)

        with do_while_pressing(browser, Keys.SPACE):
            assert browser.is_element_not_present_by_css(
                "polygon", wait_time=TIME_TO_WAIT
            )

        assert browser.is_element_present_by_css("polygon", wait_time=TIME_TO_WAIT)
