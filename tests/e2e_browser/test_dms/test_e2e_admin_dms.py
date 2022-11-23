from enum import Enum

import pytest
from splinter.exceptions import ElementDoesNotExist

from common_utils.constants import DMS_PERMISSION, USER_ROLE
from handlers.db import SiteDBHandler
from tests.constants import FLAKY_RERUNS, TIME_TO_WAIT
from tests.e2e_browser.utils_admin import assert_tags_interaction, make_login
from tests.utils import get_wait_downloaded_file


class WIDGETS_TABS(Enum):
    MAP = "Map"
    THREE_D = "Environment"
    UNIT = "Unit view"
    HEATMAPS = "Insights"
    ANALYSIS = "Dashboard"


def advance_one_level_down(browser):
    browser.find_by_css(".tbody .tr .name").first.click()  # Clicking on row name


def create_folder(browser, folder_name="my folder"):
    # Click on add folder
    create_folder_button = browser.find_by_xpath(
        "//button[@aria-label='add folder']", wait_time=TIME_TO_WAIT
    )
    create_folder_button.first.click()

    # Fills the input text with the folder name and click on "Accept"
    browser.find_by_id("name").fill(folder_name)
    browser.find_by_text("Accept").first.click()


def _login_and_give_site_permissions(
    browser, dms_url, site_1439_simulated, user_role, permissions
):
    login = make_login(
        browser, dms_url, user_role.name, expected_element_id="admin-header"
    )
    SiteDBHandler.update(
        item_pks={"id": site_1439_simulated["site"]["id"]},
        new_values={"group_id": login["group_id"]},
    )
    if user_role == USER_ROLE.DMS_LIMITED:
        from handlers import DmsPermissionHandler

        DmsPermissionHandler.put_permissions(
            user_id=login["id"],
            data=[
                {
                    "site_id": site_1439_simulated["site"]["id"],
                    "rights": permissions.name,
                }
            ],
            requesting_user=login,
        )


def assert_expected_tabs_opened(
    browser,
    view_drawer: str = None,
    heatmap_drawer: str = None,
    details_drawer: str = None,
):
    if view_drawer:
        assert browser.is_element_present_by_xpath(
            f"//*[contains(@class, 'view-drawer')]//*[contains(@class, 'tab selected')]//*[text()='{view_drawer}']",
            wait_time=TIME_TO_WAIT,
        )
    else:
        assert browser.is_element_not_present_by_xpath(
            "//*[contains(@class, 'view-drawer')]",
            wait_time=TIME_TO_WAIT,
        )

    if heatmap_drawer:
        assert browser.is_element_present_by_xpath(
            f"//*[contains(@class, 'heatmap-drawer')]//*[contains(@class, 'tab selected')]//*[text()='{heatmap_drawer}']",
            wait_time=TIME_TO_WAIT,
        )
    else:
        assert browser.is_element_not_present_by_xpath(
            "//*[contains(@class, 'heatmap-drawer')]",
            wait_time=TIME_TO_WAIT,
        )

    if details_drawer:
        assert browser.is_element_present_by_xpath(
            f"//*[contains(@class, 'details-drawer')]//*[contains(@class, 'tab selected')]//*[text()='{details_drawer}']",
            wait_time=TIME_TO_WAIT,
        )
    else:
        assert browser.is_element_not_present_by_xpath(
            "//*[contains(@class, 'details-drawer')]",
            wait_time=TIME_TO_WAIT,
        )


@pytest.fixture
def admin_login(browser, dms_url):
    make_login(browser, dms_url)


@pytest.mark.usefixtures("splinter_download_dir_autoclean")
class TestDMSAdmin:
    @pytest.fixture(autouse=True)
    def dms_admin_login(self, client_db, browser, dms_url):
        make_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")

    def test_dms_admin_drawers_uncompleted_site(
        self,
        client_db,
        dms_url,
        browser,
        site,
    ):
        """
        When opening the admin URL of a non completed site (simulated + qa)
        If we go to directory view
        There will be only a drawer with the maps
        """
        browser.visit(dms_url + f"/buildings?site_id={site['id']}")

        # Ensure there is a map and no other drawer
        assert browser.is_element_visible_by_xpath(
            "//*[contains(@class, 'map')]", wait_time=TIME_TO_WAIT
        )
        assert browser.is_element_not_present_by_xpath("//div[(@class='view-drawer')]")


@pytest.mark.flaky(reruns=FLAKY_RERUNS)
@pytest.mark.parametrize(
    "user_role,permissions",
    [
        (USER_ROLE.ADMIN, None),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.WRITE),
    ],
)
def test_dms_admin_tag_entity(
    client_db, dms_url, site_1439_simulated, browser, user_role, permissions
):
    """
    When opening the dms
    We upload a file and switch to table view
    If we add some tags
    The tags will be visible
    If we reload the page
    The tags will be there
    If we erase a tag
    That tag will not be there
    """
    _login_and_give_site_permissions(
        browser=browser,
        dms_url=dms_url,
        site_1439_simulated=site_1439_simulated,
        user_role=user_role,
        permissions=permissions,
    )

    browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

    TAG_1 = "fund:1"
    TAG_2 = "fund:2"

    # Sites
    assert_tags_interaction(browser, [TAG_1, TAG_2])

    # Buildings
    advance_one_level_down(browser)
    assert_tags_interaction(
        browser, ["marvelous_building", "regular_middle_class_building"]
    )

    # Floors
    advance_one_level_down(browser)
    assert_tags_interaction(browser, ["wonderful_floor", "just_another_floor"])

    # Unit
    advance_one_level_down(browser)
    assert_tags_interaction(browser, ["super_unit", "boring_unit"])

    # Rooms
    advance_one_level_down(browser)
    assert_tags_interaction(browser, ["misterious_room", "escape_room"])


@pytest.mark.usefixtures("splinter_download_dir_autoclean")
@pytest.mark.parametrize(
    "user_role,permissions",
    [
        (USER_ROLE.ADMIN, None),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.WRITE),
    ],
)
def test_dms_navigate_hierarchy(
    client_db, dms_url, site_1439_simulated, browser, user_role, permissions
):
    """
    When opening the dms as a dms admin
    I can navigate through every entity
    Create a folder
    And navigate to i
    """
    _login_and_give_site_permissions(
        browser=browser,
        dms_url=dms_url,
        site_1439_simulated=site_1439_simulated,
        user_role=user_role,
        permissions=permissions,
    )
    browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

    site = site_1439_simulated["site"]["name"]
    building = f"{site_1439_simulated['building'][0]['street']}, {site_1439_simulated['building'][0]['housenumber']}"
    floor_number = site_1439_simulated["floors"][0]["floor_number"]
    area = site_1439_simulated["areas"][0]["area_type"].lower().capitalize()

    # Sites
    assert browser.find_by_text(site, wait_time=TIME_TO_WAIT).first
    assert_expected_tabs_opened(
        browser=browser,
        view_drawer=WIDGETS_TABS.MAP.value,
        details_drawer=WIDGETS_TABS.ANALYSIS.value,
    )

    # Buildings
    advance_one_level_down(browser)
    assert browser.find_by_text(building, wait_time=TIME_TO_WAIT).first
    assert_expected_tabs_opened(
        browser=browser,
        view_drawer=WIDGETS_TABS.MAP.value,
        details_drawer=WIDGETS_TABS.ANALYSIS.value,
    )

    # Floors
    advance_one_level_down(browser)
    assert browser.find_by_text(f"Floor {floor_number}", wait_time=TIME_TO_WAIT).first
    assert_expected_tabs_opened(
        browser=browser,
        view_drawer=WIDGETS_TABS.THREE_D.value,
        details_drawer=WIDGETS_TABS.ANALYSIS.value,
    )

    # Units
    advance_one_level_down(browser)
    assert browser.find_by_xpath(
        "//*[contains(text(), 'ABC')]",
        wait_time=TIME_TO_WAIT,
    ).first

    assert_expected_tabs_opened(
        browser=browser,
        view_drawer=WIDGETS_TABS.THREE_D.value,
        heatmap_drawer=WIDGETS_TABS.HEATMAPS.value,
        details_drawer=WIDGETS_TABS.ANALYSIS.value,
    )

    # Rooms
    advance_one_level_down(browser)

    assert_expected_tabs_opened(
        browser=browser,
        view_drawer=WIDGETS_TABS.THREE_D.value,
        heatmap_drawer=WIDGETS_TABS.HEATMAPS.value,
        details_drawer=WIDGETS_TABS.ANALYSIS.value,
    )

    # https://stackoverflow.com/a/3655588
    assert browser.find_by_xpath(
        f"//*[text()[contains(., '{area}')]]",
        wait_time=TIME_TO_WAIT,
    ).first

    # Room
    advance_one_level_down(browser)
    EMPTY_MESSAGE = "Empty Folder"
    assert browser.find_by_text(EMPTY_MESSAGE, wait_time=TIME_TO_WAIT).first
    assert_expected_tabs_opened(browser=browser)

    # Custom folder inside room
    create_folder(browser, "test_folder")
    EMPTY_FOLDER_MESSAGE = "This folder is empty, upload a file or create a folder"
    if permissions == DMS_PERMISSION.READ:
        with pytest.raises(ElementDoesNotExist):
            browser.find_by_text("test_folder", wait_time=TIME_TO_WAIT).first.click()
    else:
        browser.find_by_text("test_folder", wait_time=TIME_TO_WAIT).first.click()
        assert browser.find_by_text(EMPTY_FOLDER_MESSAGE, wait_time=TIME_TO_WAIT).first


@pytest.mark.parametrize(
    "user_role,permissions",
    [
        (USER_ROLE.ADMIN, None),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.WRITE),
    ],
)
def test_dms_heatmap_modal_dialog(
    client_db,
    dms_url,
    site_1439_simulated,
    browser,
    user_role,
    permissions,
    splinter_download_dir_autoclean,
):
    """
    When open DMS
    I navigate to Units level
    I can see heatmap widget
    I can open the modal dialog to see more detailed view
    Then I close it and go to Rooms level
    I can do the same as previously
    """
    _login_and_give_site_permissions(
        browser=browser,
        dms_url=dms_url,
        site_1439_simulated=site_1439_simulated,
        user_role=user_role,
        permissions=permissions,
    )

    expected_dropdowns = ["Insights", "Building", "Floor", "Unit"]

    floor_id = site_1439_simulated["floors"][0]["id"]
    browser.visit(dms_url + f"/units?floor_id={floor_id}")

    assert browser.is_element_present_by_xpath(
        "//*[contains(@class, 'heatmap-drawer')]",
        wait_time=TIME_TO_WAIT,
    )

    browser.find_by_xpath(
        "//*[@data-testid='open-heatmap-modal']", wait_time=TIME_TO_WAIT
    ).first.click()

    assert browser.is_element_visible_by_css(
        ".heatmap-modal-container", wait_time=TIME_TO_WAIT
    )
    for label in expected_dropdowns:
        assert browser.is_element_visible_by_xpath(
            f"//*[@class='dropdowns-container']//*[text()='{label}']",
            wait_time=TIME_TO_WAIT,
        )

    browser.find_by_text("Close").first.click()

    # Rooms
    advance_one_level_down(browser)

    assert browser.is_element_present_by_xpath(
        "//*[contains(@class, 'heatmap-drawer')]",
        wait_time=TIME_TO_WAIT,
    )

    browser.find_by_xpath(
        "//*[@data-testid='open-heatmap-modal']", wait_time=TIME_TO_WAIT
    ).first.click()

    assert browser.is_element_visible_by_css(
        ".heatmap-modal-container", wait_time=TIME_TO_WAIT
    )
    for label in expected_dropdowns:
        assert browser.is_element_visible_by_xpath(
            f"//*[@class='dropdowns-container']//*[text()='{label}']",
            wait_time=TIME_TO_WAIT,
        )

    # Find download button
    download_button = browser.find_by_xpath(
        "//*[contains(text(),'Download PNG')][not(@disabled)]", wait_time=TIME_TO_WAIT
    ).first

    # Download the file
    download_button.click()
    file = get_wait_downloaded_file(splinter_download_dir_autoclean)
    assert file is not None


@pytest.mark.freeze_time("2020-08-04")
def test_dms_initial_view_as_admin(client_db, dms_url, admin_login, browser):
    """
    Check the clients are loaded when accessing as admin
    """
    browser.visit(dms_url + "/clients")
    assert browser.find_by_text(client_db["name"]).first
