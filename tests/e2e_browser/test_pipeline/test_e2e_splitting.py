from collections import Counter

import pytest

from brooks.models.violation import ViolationType
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler, UnitDBHandler
from handlers.plan_utils import create_areas_for_plan
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_editor import (
    accept_snack_bar_message,
    assert_basic_elements_are_visible_in_page,
    assert_error_is_visible_in_page,
    click_in_global_coordinate,
    click_save_and_wait_till_saved,
    click_save_button,
    log_out,
    make_login,
    wait_for_preview_img,
)
from tests.e2e_browser.utils_pipeline import assert_help_modal_is_visible
from tests.e2e_utils import SlamUIClient


@pytest.fixture(autouse=True)
def do_login(browser, login_url):
    make_login(browser, login_url)


def test_splitting_window_appears_with_an_error(browser, splitting_url_wrong_plan):
    """
    Go to the splitting window as a non-dev user and a plan_id that doesn't exist
    When the splitting window opens we check that the users gets an error
    """
    browser.visit(splitting_url_wrong_plan)

    assert_error_is_visible_in_page(browser=browser)
    assert_basic_elements_are_visible_in_page(browser=browser)
    assert_help_modal_is_visible(
        browser=browser, number_of_li=3, number_of_instructions=9
    )


def test_splitting_unit_happy_path_ok(
    browser,
    recreate_test_gcp_client_bucket,
    floor,
    splitting_url_default_plan,
    add_background_plan_image_to_gcloud,
):
    """
    Go to the splitting window as a non-dev user
    When the splitting window opens we check that the basic elements are displayed
    And we click on the available area to assign it to unit 1
    And we click save
    Then we have a unit in the DB
    """
    PlanDBHandler.update(
        item_pks=dict(id=floor["plan_id"]),
        new_values=dict(georef_scale=0.0001),
    )
    add_background_plan_image_to_gcloud(
        plan_info=PlanDBHandler.get_by(id=floor["plan_id"])
    )

    browser.visit(splitting_url_default_plan)
    wait_for_preview_img(browser)
    # By default the first unit is selected
    browser.find_by_xpath(
        "//div[contains(@class, 'featureType selected')]"
    ).find_by_xpath("span[contains(text(), 'Unit 1')]").click()

    # Unit 1 is saved
    assert browser.is_element_visible_by_xpath(
        "//div[contains(@class, 'apartmentColor') and contains(@class, 'saved')]",
        wait_time=TIME_TO_WAIT,
    )

    click_in_global_coordinate(browser, 1000, 550)
    assert browser.find_by_xpath(
        "//div[contains(@class, 'element HNF')]", wait_time=TIME_TO_WAIT
    ).first

    # Unit 1 is modified
    assert browser.is_element_visible_by_xpath(
        "//div[contains(@class, 'apartmentColor') and contains(@class, 'modified')]",
        wait_time=TIME_TO_WAIT,
    )

    click_save_and_wait_till_saved(browser=browser)
    browser.find_by_xpath(
        "//button[contains(@class, 'mat-focus-indicator')]", wait_time=TIME_TO_WAIT
    ).first.click()
    assert len(UnitDBHandler.find()) == 1

    # Unit 1 is saved
    assert browser.is_element_visible_by_xpath(
        "//div[contains(@class, 'apartmentColor') and contains(@class, 'saved')]",
        wait_time=TIME_TO_WAIT,
    )

    browser.fill("1_typeName", "custom type name")
    # Click outside of input to apply a changes
    browser.find_by_xpath(
        "//div[contains(@class, 'featureType selected')]"
    ).find_by_xpath("span[contains(text(), 'Unit 1')]").click()
    assert browser.is_element_visible_by_xpath(
        "//div[contains(@class, 'apartmentColor') and contains(@class, 'modified')]",
        wait_time=TIME_TO_WAIT,
    )

    click_save_and_wait_till_saved(browser=browser)
    browser.find_by_xpath(
        "//button[contains(@class, 'mat-focus-indicator')]", wait_time=TIME_TO_WAIT
    ).first.click()
    modified_unit = UnitDBHandler.find()[0]
    assert modified_unit["unit_type"] == "custom type name"


def test_feedback_brooks_model(
    browser,
    recreate_test_gcp_client_bucket,
    react_planner_background_image_full_plan,
    plan,
    add_background_plan_image_to_gcloud,
):
    """
    When accessing the splitting site for a plan that contains an annotation error
    We can see there is 1 brooks error displayed
    When clicking on an area
    And saving
    Then More errors appear as not all the right areas are selected
    """
    ReactPlannerProjectsDBHandler.add(
        plan_id=plan["id"],
        data=react_planner_background_image_full_plan,
    )
    add_background_plan_image_to_gcloud(plan_info=plan)

    create_areas_for_plan(plan_id=plan["id"])
    browser.visit(SlamUIClient._splitting_url_plan(plan_id=plan["id"]))
    brooks_errors = browser.find_by_xpath(
        "//div[contains(@class, 'brooksType')]", wait_time=TIME_TO_WAIT
    )

    assert Counter([x.text.split(")")[-1].strip().rstrip() for x in brooks_errors]) == {
        ViolationType.OPENING_OVERLAPS_ANOTHER_OPENING.name: 4,
    }
    click_in_global_coordinate(browser, 1000, 650)
    click_save_button(browser=browser)
    accept_snack_bar_message(browser=browser)
    errors = {
        error.text.split(")")[1].strip()
        for error in browser.find_by_xpath(
            "//div[contains(@class, 'brooksType')]", wait_time=TIME_TO_WAIT
        )
    }
    assert errors == {
        ViolationType.CONNECTED_SPACES_MISSING.name,
        ViolationType.AREA_NOT_DEFINED.name,
    }
    log_out(browser=browser)


def test_plan_without_units(
    browser,
    recreate_test_gcp_client_bucket,
    plan_classified_scaled_georeferenced,
    add_background_plan_image_to_gcloud,
):
    """
    When accessing the unit splitting page of a plan that contains an annotation error
    Then the user can see there is plan brooks displayed
    If user selects that the plan has no unit
    Then brooks model is not displayed
    And the plan data is updated
    """
    add_background_plan_image_to_gcloud(plan_info=plan_classified_scaled_georeferenced)

    browser.visit(
        SlamUIClient._splitting_url_plan(
            plan_id=plan_classified_scaled_georeferenced["id"]
        )
    )

    wait_for_preview_img(browser)

    assert plan_classified_scaled_georeferenced["without_units"] is False
    # Floorplan & Brooks are shown
    assert browser.find_by_id("floorplan").first

    browser.find_by_xpath(
        "//*[contains(text(), 'Plan without units')]/input", wait_time=TIME_TO_WAIT
    ).first.click()

    # Floorplan & Brooks are not displayed
    assert browser.is_element_not_present_by_id("floorplan", wait_time=TIME_TO_WAIT)

    # Assert plan is updated
    updated_plan = PlanDBHandler.get_by(id=plan_classified_scaled_georeferenced["id"])
    assert updated_plan["without_units"] is True
