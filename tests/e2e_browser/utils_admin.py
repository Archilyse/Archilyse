import json
import mimetypes
import os
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from selenium.webdriver.common.keys import Keys
from splinter.driver.webdriver import BaseWebDriver

from common_utils.constants import ADMIN_SIM_STATUS, REGION
from common_utils.logger import logger
from handlers.db import UnitDBHandler
from tests.constants import TIME_TO_WAIT, USERS
from tests.utils import create_user_context, retry_stale_element


def make_login(
    browser, admin_url, user_type="ADMIN", expected_element_id="admin-header"
):
    context = create_user_context(USERS[user_type])["user"]
    browser.visit(f"{admin_url}/login")
    browser.fill("user", context["login"])
    browser.fill("password", context["password"])
    browser.find_by_xpath(
        "//button[contains(text(), 'Sign in')]",
        wait_time=TIME_TO_WAIT,
    ).first.click()
    assert browser.is_element_present_by_id(expected_element_id, wait_time=TIME_TO_WAIT)
    return context


def assert_tag_is_visible(browser, tag_name):
    assert browser.is_element_visible_by_xpath(
        f"//span[(text()='{tag_name}')]", wait_time=TIME_TO_WAIT
    )


def assert_tags_interaction(browser, tags):
    # Add tags
    for tag in tags:
        browser.fill("labels", tag)
        active_web_element = browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ENTER)
        time.sleep(1)  # Too fast interaction here may cause one tag not to be saved

    # Ensure they are visible
    for tag in tags:
        assert_tag_is_visible(browser, tag)

    # After reloading, if they are saved successfully, tags will be there
    browser.reload()
    for tag in tags:
        assert_tag_is_visible(browser, tag)

    # Erase all tags and ensure they are gone after the reload
    browser.find_by_css(".autocomplete-input", wait_time=TIME_TO_WAIT).first.click()
    active_web_element = browser.driver.switch_to.active_element
    for _tag in tags:
        active_web_element.send_keys(Keys.BACKSPACE)

    browser.reload()
    assert browser.is_element_not_present_by_css(".tag", wait_time=TIME_TO_WAIT)


@contextmanager
def expand_screen_size(browser, width=2048, height=1152):
    previous_window_size = browser.driver.get_window_size()
    try:
        yield browser.driver.set_window_size(width=width, height=height)
    finally:
        browser.driver.set_window_size(**previous_window_size)


def safe_wait_for_table_and_expand_columns(browser, table_name, expected_rows=0):
    table = browser.find_by_id(table_name, wait_time=TIME_TO_WAIT)
    assert browser.is_element_present_by_css(".ag-header-row", wait_time=TIME_TO_WAIT)
    assert browser.is_element_present_by_css(
        ".ag-body-viewport", wait_time=TIME_TO_WAIT
    )
    if expected_rows > 0:
        rows = table.find_by_xpath(
            "//div[contains(@class, 'ag-center-cols-container')]"
            "/div[contains(@role, 'row') and contains(@class, 'ag-row')]"
        )
        assert expected_rows == len(
            rows
        ), f"expected {expected_rows}, rows in table: {len(rows)}"
    return table


def admin_assert_alert_successful(browser, time_to_wait=TIME_TO_WAIT * 2):
    assert browser.is_element_present_by_id(
        "notification-success", wait_time=time_to_wait
    )


def admin_click_save_and_assert_successful(browser, save_id=None):
    admin_click_save(browser=browser, save_id=save_id)
    admin_assert_alert_successful(browser=browser)


def admin_click_delete_and_assert_successful(browser):
    browser.find_by_xpath(
        "//*[contains(@class, 'delete-button')]", wait_time=TIME_TO_WAIT
    ).first.click()
    browser.find_by_xpath(
        "//*[contains(@class, 'delete-button')]", wait_time=TIME_TO_WAIT
    )[1].click()
    admin_assert_alert_successful(browser=browser)


def reload_and_count_ready_columns(browser):
    browser.reload()
    safe_wait_for_table_and_expand_columns(browser, "sites_table")
    assert browser.is_element_visible_by_css("[col-id='ready']", wait_time=TIME_TO_WAIT)

    not_ready_elems = browser.find_by_css("[col-id='ready'] .cross")
    ready_elems = browser.find_by_css("[col-id='ready'] .check")

    return ready_elems, not_ready_elems


def _get_admin_columns(browser):
    return browser.find_by_css(".ag-center-cols-container > .row")


@retry_stale_element
def _get_admin_column_content(
    browser: BaseWebDriver, column_name: str, row_number: int = 1, as_text: bool = True
):
    criteria = f"//div[@row-id={row_number-1}]/div[@col-id='{column_name}']"
    if as_text:
        return browser.find_by_xpath(criteria).text
    return browser.find_by_xpath(criteria)


def _get_admin_row_content_by_row_id(browser: BaseWebDriver, row_id: int):
    rows = _get_admin_columns(browser)
    for row in rows:
        if row.find_by_css("[col-id='id']").first.text == str(row_id):
            return row


def admin_click_save(browser, save_id=None):
    if save_id:
        buttons = browser.find_by_id(save_id, wait_time=TIME_TO_WAIT)
    else:
        buttons = browser.find_by_xpath(
            "//button[@type='submit']", wait_time=TIME_TO_WAIT
        )

    assert len(buttons) == 1
    buttons.first.click()


def click_edit_button(browser):
    """Expanding the screen so that Edit button is clickable"""
    browser.links.find_by_text("Edit").click()


def navigate_to_child_and_create(browser, child_text, expected_table):
    navigate_to_child(browser=browser, child_text=child_text)
    safe_wait_for_table_and_expand_columns(browser, expected_table)
    browser.find_by_css(".add-icon", wait_time=TIME_TO_WAIT).first.click()
    assert browser.is_element_present_by_xpath("//form", wait_time=TIME_TO_WAIT)


def navigate_to_parent(browser, parent_text):
    browser.click_link_by_partial_href(parent_text)
    browser.reload()


@retry_stale_element
def navigate_to_child(browser, child_text):
    browser.click_link_by_partial_href(child_text)


def get_uploaded_file_name(file_fixture):
    return os.path.basename(file_fixture)


def upload_file(browser, file_fixture):
    browser.fill("upload-file", file_fixture.as_posix())
    assert admin_assert_alert_successful

    snackbar_close_buttons = browser.find_by_xpath(
        "//*[contains(@title, 'Close')]", wait_time=TIME_TO_WAIT
    )

    # Close snackbars as some of them can contain the filename
    for close_button in snackbar_close_buttons:
        close_button.click()

    # Now the only text with the filename is the file itself
    filename = get_uploaded_file_name(file_fixture)
    return browser.find_by_text(filename, wait_time=TIME_TO_WAIT).first


@pytest.mark.local_ui_tests
def test_import_dxf(
    building, dxf_sample_compliant, celery_eager, recreate_test_gcp_client_bucket, qa_db
):
    from handlers import PlanHandler
    from handlers.db import FloorDBHandler, SiteDBHandler

    def create_plan(file_content, floor_number: int):
        new_plan_info = PlanHandler.add(
            plan_content=file_content,
            plan_mime_type=mimetypes.types_map[".dxf"],
            site_id=building["site_id"],
            building_id=building["id"],
        )
        SiteDBHandler.update(
            item_pks={"id": building["site_id"]}, new_values={"qa_id": qa_db["id"]}
        )

        FloorDBHandler.add(
            building_id=building["id"],
            plan_id=new_plan_info["id"],
            floor_number=floor_number,
        )
        logger.info(
            f"Created DXF annotations in plan {new_plan_info['id']}."
            f" Check http://localhost:9000/v2/editor/{new_plan_info['id']}"
        )

    create_plan(dxf_sample_compliant, floor_number=0)
    for i, file_name in enumerate(Path("tests/fixtures/dxf/").glob("*.dxf")):
        with open(file_name, "rb") as f:
            logger.info(
                f"Generating dxf annotations and image of file {file_name.as_posix()}"
            )
            create_plan(file_content=f.read(), floor_number=i + 1)


@pytest.mark.local_ui_tests
def test_local_pipeline_ui(
    client_db,
    site_coordinates,
    building,
    make_buildings,
    oecc_group,
    archilyse_group,
    login,
    make_plans,
    make_floor,
    qa_db,
    recreate_test_gcp_client_bucket,
    add_background_plan_image_to_gcloud,
    fixtures_path,
    georef_plan_values,
    react_planner_fixtures_path,
):
    from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler, SiteDBHandler

    create_user_context(USERS["ADMIN"])
    planner_site = SiteDBHandler.add(
        client_id=client_db["id"],
        client_site_id="Site with react planner data",
        full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
        name="Site with react planner data",
        region="Switzerland",
        group_id=oecc_group["id"],
        georef_region=REGION.CH.name,
        **site_coordinates,
        qa_id=qa_db["id"],
    )
    (react_building,) = make_buildings(*[planner_site])
    (fe_fixtures_building,) = make_buildings(
        planner_site, street_name="frontend_fixtures"
    )
    load_all_react_planner_fixture_annotations(
        annotation_paths=[
            react_planner_fixtures_path.joinpath(name)
            for name in (
                "mockScene.json",
                "mockSimpleScene.json",
                "mockSceneWithPotentialOrphanOpenings.json",
                "mockAnnotationsResponse.json",
            )
        ],
        make_plans=make_plans,
        make_floor=make_floor,
        building=react_building,
    )
    load_all_react_planner_fixture_annotations(
        annotation_paths=fixtures_path.joinpath("annotations").glob("*.json"),
        make_plans=make_plans,
        make_floor=make_floor,
        building=fe_fixtures_building,
    )
    plan_ids_w_image = (332, 6951)
    # Upload once a background image and share the link with all the other plans
    plans_by_id = {x["id"]: x for x in PlanDBHandler.find()}
    plan_updated = add_background_plan_image_to_gcloud(plan_info=plans_by_id[574])
    plans_w_common_image = [
        v for k, v in plans_by_id.items() if k not in plan_ids_w_image
    ]

    projects = ReactPlannerProjectsDBHandler.find()
    projects_by_plan_id = {
        project["plan_id"]: {
            "image_width": project["data"].get("width", 20000),
            "image_height": project["data"].get("height", 10000),
        }
        for project in projects
    }

    PlanDBHandler.bulk_update(
        image_gcs_link={
            x["id"]: plan_updated["image_gcs_link"] for x in plans_w_common_image
        },
        image_mime_type={
            x["id"]: plan_updated["image_mime_type"] for x in plans_w_common_image
        },
        image_width={
            x["id"]: projects_by_plan_id[x["id"]]["image_width"]
            for x in plans_w_common_image
        },
        image_height={
            x["id"]: projects_by_plan_id[x["id"]]["image_height"]
            for x in plans_w_common_image
        },
    )

    # Add the real image of plans 332 and 6951 to have examples where we can match annotations
    # with the image
    for plan_id in plan_ids_w_image:
        with fixtures_path.joinpath(f"images/image_plan_{plan_id}.jpg").open("rb") as f:
            add_background_plan_image_to_gcloud(
                plan_info=plans_by_id[plan_id], image_content=f.read()
            )
            PlanDBHandler.update(
                item_pks={"id": plan_id},
                new_values={
                    "georef_scale": georef_plan_values[plan_id]["georef_scale"]
                },
            )


@pytest.mark.local_ui_tests
def test_local_dashboard_dms_ui(
    client_db,
    site_coordinates,
    oecc_group,
    archilyse_group,
    upwork_group,
    login,
    qa_db,
    recreate_test_gcp_client_bucket,
    recreate_test_gcp_bucket,
    competition_with_fake_feature_values,
    add_site_1439_floorplan_to_unit,
    add_site_1439_floorplan_to_floor,
    site_1439_simulated,
    triangles_site_1439_3d_building_gcs_2,
    add_background_plan_image_to_gcloud,
):
    create_user_context(USERS["ADMIN"])

    UNIT_UI_CLIENT_ID = "ABC0101"
    add_site_1439_floorplan_to_unit(client_id=UNIT_UI_CLIENT_ID)
    FLOOR_ID = 12249
    add_site_1439_floorplan_to_floor(floor_id=FLOOR_ID)
    units_ids = list(UnitDBHandler.find_ids())
    UnitDBHandler.bulk_update(
        ph_final_gross_rent_adj_factor={u_id: 0.03 for u_id in units_ids},
        ph_final_gross_rent_annual_m2={u_id: 100 for u_id in units_ids},
        ph_final_sale_price_m2={u_id: 500 for u_id in units_ids},
        ph_final_sale_price_adj_factor={u_id: 0.02 for u_id in units_ids},
    )


def load_all_react_planner_fixture_annotations(
    annotation_paths, make_plans, make_floor, building
):
    from handlers.db import PlanDBHandler
    from handlers.editor_v2 import ReactPlannerHandler

    for i, annotation_file in enumerate(sorted(annotation_paths)):
        (new_plan,) = make_plans(building)
        if "plan_" in annotation_file.name:
            plan_id = int(annotation_file.stem.split("_")[-1])
            new_plan = PlanDBHandler.update(
                item_pks={"id": new_plan["id"]}, new_values={"id": plan_id}
            )

        make_floor(building=building, plan=new_plan, floornumber=i)
        with annotation_file.open() as f:
            logger.debug(f"plan id: {new_plan['id']} - {annotation_file}")
            plan_data = json.load(f)
            if "mockAnnotationsResponse" in annotation_file.name:
                plan_data = plan_data["data"]
            ReactPlannerHandler().store_plan_data(
                plan_id=new_plan["id"],
                plan_data=plan_data,
                validated=False,
            )
