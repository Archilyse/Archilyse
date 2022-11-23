import pytest
from splinter.driver.webdriver import BaseWebDriver

from common_utils.constants import USER_ROLE
from handlers.db import ClientDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import (
    _get_admin_columns,
    admin_click_save_and_assert_successful,
    make_login,
    safe_wait_for_table_and_expand_columns,
)


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url)


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN.name, USER_ROLE.TEAMLEADER.name])
def test_add_client(admin_url, browser, user_role):
    make_login(browser, admin_url, user_role)
    new_client_name = "NewClient"
    browser.visit(admin_url + "/client/new")
    browser.fill(name="name", value=new_client_name)
    admin_click_save_and_assert_successful(browser)
    assert ClientDBHandler.get_by(name=new_client_name)


def test_admin_panel_can_view_one_client(client_db, admin_url, browser):
    browser.visit(admin_url + "/clients")
    safe_wait_for_table_and_expand_columns(browser, "clients_table", expected_rows=1)
    rows = _get_admin_columns(browser)
    first_client_entry = rows.first
    assert first_client_entry is not None
    client_name = browser.find_by_css(".client-name").text
    assert client_name == client_db["name"]


def test_admin_panel_can_edit_pricing(client_db, admin_url, browser: BaseWebDriver):
    browser.visit(admin_url + "/clients")
    safe_wait_for_table_and_expand_columns(browser, "clients_table", expected_rows=1)
    rows = _get_admin_columns(browser)
    client_entry = rows.first

    client = ClientDBHandler.get_by(id=client_db["id"])
    assert client["option_dxf"]
    assert client["option_pdf"]
    assert client["option_ifc"]
    assert client["option_analysis"]
    client_entry.find_by_css(
        ".option_full_package-true", wait_time=TIME_TO_WAIT
    ).click()
    assert browser.is_element_present_by_css(
        ".option_full_package-false", wait_time=TIME_TO_WAIT
    )
    client = ClientDBHandler.get_by(id=client_db["id"])
    assert not client["option_dxf"]
    assert not client["option_pdf"]
    assert not client["option_ifc"]
    assert not client["option_analysis"]

    # check the other way around
    browser.visit(admin_url + "/clients")
    safe_wait_for_table_and_expand_columns(browser, "clients_table", expected_rows=1)
    rows = _get_admin_columns(browser)
    client_entry = rows.first
    client_entry.find_by_css(
        ".option_full_package-false", wait_time=TIME_TO_WAIT
    ).click()
    assert browser.is_element_present_by_css(
        ".option_full_package-true", wait_time=TIME_TO_WAIT
    )
    client = ClientDBHandler.get_by(id=client_db["id"])
    assert client["option_dxf"]
    assert client["option_pdf"]
    assert client["option_ifc"]
    assert client["option_analysis"]
