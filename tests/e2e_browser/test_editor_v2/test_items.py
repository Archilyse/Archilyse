import pytest

from handlers import PlanLayoutHandler
from tests.e2e_browser.test_editor_v2.utils import (
    draw_2_valid_item_in_area,
    draw_all_items_in_area,
    extend_size_of_items,
    save_and_warning,
    save_plan_and_success,
    scale_and_annotate_plan,
    team_member_login,
    update_plan_with_gcs_image,
    wait_for_floorplan_img_load,
)
from tests.e2e_browser.utils_admin import expand_screen_size


class TestItemsInteraction:
    @staticmethod
    def test_item_interaction(
        browser,
        plan_masterplan,
        client_db,
        background_floorplan_image,
        editor_v2_url,
    ):
        """
        - An item is placed outside of the area, and invalid position so the item is not created
        - An item is placed in the corner of the area
        - An item is placed in the center of the area
        - All the items are increased 10cm in each direction from the default 60cm using the right hand side form
        - The item in the corner can only grow 1cm approximately because it close to the walls
        - The item in the center grows to 70cm each side
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

            wait_for_floorplan_img_load(browser=browser)
            scale_and_annotate_plan(browser=browser)
            draw_2_valid_item_in_area(browser=browser)
            extend_size_of_items(browser=browser)
            save_and_warning(browser=browser)

        layout = PlanLayoutHandler(plan_id=plan_masterplan["id"]).get_layout(
            scaled=True
        )
        features_sizes = sorted([feature.footprint.area for feature in layout.features])
        assert features_sizes[-1] == pytest.approx(0.7**2, abs=10**-2)
        # It can be flaky to assume the item is placed always at the same distance from the wall
        # But the point is to assert it didn't grow as much as the other item
        assert features_sizes[0] == pytest.approx(0.61**2, abs=0.1)

    @staticmethod
    def test_add_all_items_catalog(
        browser,
        plan_masterplan,
        client_db,
        background_floorplan_image,
        editor_v2_url,
    ):
        """
        All items can be added and are recognized by the backend
        """
        update_plan_with_gcs_image(
            plan_id=plan_masterplan["id"],
            client_id=client_db["id"],
            image_content=background_floorplan_image,
        )
        with expand_screen_size(browser=browser):
            team_member_login(browser=browser, editor_v2_url=editor_v2_url)
            browser.visit(editor_v2_url + f"/{plan_masterplan['id']}")

            wait_for_floorplan_img_load(browser=browser)
            scale_and_annotate_plan(browser=browser)

            draw_all_items_in_area(browser=browser)
            save_plan_and_success(browser=browser)
