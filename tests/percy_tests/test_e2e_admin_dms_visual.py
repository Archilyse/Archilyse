import pendulum
import pytest

from handlers.db import FileDBHandler, UnitDBHandler
from tests.constants import PERCY_TIME_TO_WAIT, TIME_TO_WAIT
from tests.e2e_browser.utils_admin import expand_screen_size, make_login, upload_file
from tests.percy_tests.utils_percy import take_screenshot

PERCY_CSS = (
    """
        #root {
          height: 1152px;
        }
        /* As percy disables the animation to position the drawer, we have to position it ourselves */
        .widget-drawer {
            position: relative;
            right: 0;
        }
    """,
)


def advance_one_level_down(browser):
    browser.find_by_css(".tbody .tr .name").first.click()  # Clicking on row name


@pytest.fixture
def admin_login(browser, dms_url):
    make_login(browser, dms_url)


@pytest.fixture
def dms_login(browser, dms_url):
    make_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")


def wait_for_pie_chart(browser):
    EXPECTED_SITE_1439_UNITS_TEXT = "units"
    assert browser.find_by_xpath(
        f"//*[contains(text(),'{EXPECTED_SITE_1439_UNITS_TEXT}')]",
        wait_time=TIME_TO_WAIT,
    ).first


def assert_tag_is_visible(browser, tag_name):
    assert browser.is_element_visible_by_xpath(
        f"//span[(text()='{tag_name}')]", wait_time=TIME_TO_WAIT
    )


@pytest.mark.freeze_time("2020-08-04")
def test_dms_sites_table_view(
    client_db, site_1439_simulated, dms_url, dms_login, browser
):
    """
    Takes a screenshot of the sites in table view as a DMS user
    """
    with expand_screen_size(browser=browser):
        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")
        wait_for_pie_chart(browser)

        assert take_screenshot(
            browser,
            "test_dms_sites_table_view",
            percy_css=PERCY_CSS,
        )


@pytest.mark.freeze_time("2020-08-04")
def test_dms_sites_grid_view(
    client_db, site_1439_simulated, dms_url, dms_login, browser
):
    """
    Takes a screenshot of the sites in grid view as a DMS suer
    """
    with expand_screen_size(browser=browser):
        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        wait_for_pie_chart(browser)
        assert take_screenshot(
            browser,
            "test_dms_sites_grid_view",
            percy_css=PERCY_CSS,
        )


@pytest.mark.freeze_time("2020-08-04")
def test_dms_units_grid_view(
    client_db,
    dms_url,
    admin_login,
    valid_image,
    recreate_test_gcp_bucket,
    recreate_test_gcp_client_bucket,
    site_1439_simulated,
    triangles_site_1439_3d_building_gcs,
    browser,
    add_site_1439_floorplan_to_unit,
    populate_unit_ph_price,
):
    """
    Takes a screenshot of the units in table view and grid view with the two drawers open
    Upload a file and then takes screenshot of its details view
    """
    UNIT_UI_CLIENT_ID = "ABC0101"
    add_site_1439_floorplan_to_unit(client_id=UNIT_UI_CLIENT_ID)

    with expand_screen_size(browser=browser):
        building_with_3d_fixtures = 2659

        # Units table view
        browser.visit(dms_url + f"/floors?building_id={building_with_3d_fixtures}")
        advance_one_level_down(browser)

        assert take_screenshot(
            browser,
            "test_dms_units_table_view",
            percy_css=PERCY_CSS,
            wait_time=2 * PERCY_TIME_TO_WAIT,
        )

        # Units grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # To avoid flakyness we disable the map
        browser.find_by_text("Map").first.click()

        assert take_screenshot(
            browser,
            "test_dms_units_view_with_widgets",
            wait_time=2 * PERCY_TIME_TO_WAIT,
            percy_css=PERCY_CSS,
        )

        uploaded_file = upload_file(browser, valid_image)
        FileDBHandler.update(
            item_pks={"id": FileDBHandler.find()[0]["id"]},
            new_values={
                "created": pendulum.datetime(2020, 8, 4, 0, 0).to_datetime_string()
            },
        )
        assert uploaded_file.visible
        uploaded_file.click()

        assert take_screenshot(
            browser,
            "test_dms_units_view_with_widgets_details",
            wait_time=2 * PERCY_TIME_TO_WAIT,
            percy_css=PERCY_CSS,
        )

        # Rooms view checks, the site_1439 fixtures are so slow that we are adding it into this test as well
        unit_id = UnitDBHandler.get_by(client_id=UNIT_UI_CLIENT_ID)["id"]
        browser.visit(dms_url + f"/rooms?unit_id={unit_id}")

        # Rooms view
        assert browser.find_by_text("Environment", wait_time=TIME_TO_WAIT).first

        assert take_screenshot(
            browser,
            "test_dms_rooms_view",
            percy_css=PERCY_CSS,
            wait_time=2 * PERCY_TIME_TO_WAIT,
        )
