import pytest
from splinter.driver.webdriver import BaseWebDriver

from handlers.db import SiteDBHandler
from tests.celery_utils import wait_for_celery_tasks
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import (
    _get_admin_column_content,
    _get_admin_columns,
    admin_click_save_and_assert_successful,
    click_edit_button,
    make_login,
    navigate_to_child,
    navigate_to_child_and_create,
    navigate_to_parent,
    safe_wait_for_table_and_expand_columns,
)
from tests.e2e_browser.utils_editor import clear_input

MISSING_PARENT_INFO_ERROR = "Missing parent info while trying to create an entity"


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url)


def test_admin_create_edit_site_autofills_related_entity_field(
    admin_url,
    browser: BaseWebDriver,
    make_clients,
    make_buildings,
    site_coordinates,
):
    """
    Given many clients
    when clicking on sites for specific client
    and clicking on create site
    and the site is created
    then there is one site for the specified client

    when clicking on edit site
    and the site is edited
    then there is one site for the specified client
    and site is edited
    """
    *_, client = make_clients(3)

    browser.visit(admin_url + "/clients")
    safe_wait_for_table_and_expand_columns(browser, "clients_table", expected_rows=3)
    navigate_to_child_and_create(
        browser,
        child_text=f"sites?client_id={client['id']}",
        expected_table="sites_table",
    )

    browser.fill("name", "test_site")
    browser.fill("region", "1")
    browser.fill("priority", "10")
    browser.fill("lat", str(site_coordinates["lat"]))
    browser.fill("lon", str(site_coordinates["lon"]))

    admin_click_save_and_assert_successful(browser=browser)
    wait_for_celery_tasks(num_tasks_expected=1)

    sites = SiteDBHandler.get_all_by_client(client_id=client["id"])
    assert len(sites) == 1

    browser.visit(admin_url + f"/sites?client_id={client['id']}")  # Go back
    safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=1)

    click_edit_button(browser=browser)
    assert browser.find_by_xpath("//form", wait_time=TIME_TO_WAIT).first
    browser.type("region", "2")
    clear_input(browser)
    browser.fill("region", "2")

    admin_click_save_and_assert_successful(browser=browser)

    wait_for_celery_tasks(num_tasks_expected=1)

    sites = SiteDBHandler.get_all_by_client(client_id=client["id"])
    assert len(sites) == 1
    assert sites[0]["region"] == "2"


def test_admin_cant_create_site_without_parent_info(
    admin_url, browser: BaseWebDriver, client_db, site_coordinates
):
    """
    User can not create a site without client id info
    """
    browser.visit(admin_url + "/site/new?client_id=")
    assert browser.find_by_text(MISSING_PARENT_INFO_ERROR)


def test_admin_client_link_sites(
    make_clients, make_sites, admin_url, browser: BaseWebDriver
):
    """
    Given 2 clients
    and 2 site for client1
    and 1 site for client2
    when visiting clients endpoint
    and clicking on sites link for client1
    then in the page there are only 2 sites
    when clicking on parent link for first site
    then first row belongs to client1
    """
    client1, client2 = make_clients(2)
    site1, _, _ = make_sites(client1, client1, client2)

    browser.visit(admin_url + "/clients")

    safe_wait_for_table_and_expand_columns(browser, "clients_table", expected_rows=2)
    navigate_to_child(browser, f"/sites?client_id={client1['id']}")

    safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=2)
    sites_entries = _get_admin_columns(browser=browser)
    assert len(sites_entries) == 2

    navigate_to_parent(browser, "/clients")
    safe_wait_for_table_and_expand_columns(browser, "clients_table", expected_rows=2)
    client_entries = _get_admin_columns(browser=browser)
    assert len(client_entries) == 2
    for value in ["id", "name"]:
        assert _get_admin_column_content(browser, value) == str(client1[value])


def test_admin_site_link_buildings(
    make_clients, make_sites, make_buildings, admin_url, browser: BaseWebDriver
):
    """
    Given 1 client
    and 2 sites for client1
    and 2 buildings for site1
    and 1 building for site2
    when visiting sites endpoint
    and clicking on buildings for site1
    then in the page there are only 2 buildings
    """

    # Create data
    (client1,) = make_clients(1)
    site1_1, site1_2 = make_sites(client1, client1)
    building_1, _, _ = make_buildings(site1_1, site1_1, site1_2)

    browser.visit(admin_url + f"/sites?client_id={client1['id']}")
    navigate_to_child(browser, f"/pipelines?site_id={site1_1['id']}")

    building_entries = browser.find_by_xpath(
        "//td[contains(text(), 'Building:')]",
        wait_time=TIME_TO_WAIT,
    )

    assert len(building_entries) == 2
