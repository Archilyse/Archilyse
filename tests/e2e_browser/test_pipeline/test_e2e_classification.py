import pytest

from brooks.classifications import CLASSIFICATIONS
from brooks.types import AreaType
from tests.e2e_browser.utils_editor import make_login, wait_for_preview_img
from tests.e2e_browser.utils_pipeline import editor_click_help_button


@pytest.fixture(autouse=True)
def do_login(browser, login_url):
    make_login(browser, login_url, "ADMIN")


def test_classification_area_types_visible(
    browser,
    recreate_test_gcp_client_bucket,
    site,
    plan,
    add_background_plan_image_to_gcloud,
    classification_url_default_plan,
    make_classified_plans,
):
    make_classified_plans(plan, annotations_plan_id=332)
    add_background_plan_image_to_gcloud(plan_info=plan)
    # We need a controlled window size to click
    browser.visit(classification_url_default_plan)

    wait_for_preview_img(browser)

    # Select "No filter"
    browser.find_by_xpath("//option")[0].click()

    areas_which_should_be_visible = {
        area_type
        for area_type, properties in CLASSIFICATIONS.UNIFIED.value().area_tree.items()
        if not properties["children"]
    }
    areas_which_should_be_visible.remove(AreaType.KITCHEN_DINING)
    area_types_visible = {
        area
        for area in areas_which_should_be_visible
        if not browser.find_by_xpath(
            f"//div[contains(text(), '{area.name}')]"
        ).is_empty()
    }
    assert AreaType.LIGHTWELL in areas_which_should_be_visible
    assert areas_which_should_be_visible == area_types_visible


def test_classification_display_help_modal(
    browser,
    recreate_test_gcp_client_bucket,
    classification_url_default_plan,
    plan,
    add_background_plan_image_to_gcloud,
):
    """
    Given any plan
    Go to the classification window as a non-dev user
    When the classification window opens
    And the user clicks on Help
    Then a modal window displaying key shortcuts will be displayed
    """
    add_background_plan_image_to_gcloud(plan_info=plan)

    browser.visit(classification_url_default_plan)

    wait_for_preview_img(browser)

    editor_click_help_button(browser=browser)

    assert browser.find_by_xpath(
        "//h5[text() = 'Controls and Keyboard Shortcuts']"
    ).first

    help_instructions = browser.find_by_css(
        "help-dialog-classification-component > ul > li"
    )
    assert len(help_instructions) >= 5
