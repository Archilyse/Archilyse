import pytest
import requests

from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import make_login
from tests.utils import wait_for_url


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url, "ADMIN")


def test_admin_panel_public_statics_served(admin_url, browser):
    browser.visit(admin_url)
    images = browser.find_by_xpath("//img")

    assert all(requests.get(image["src"]).ok for image in images)


def test_admin_saved_route(admin_url, browser):
    """
    When user go to a site first time and log in
    We will redirect him to a initial page
    If he goes to somewhere
    We will save that route in localStorage
    If user close a page and open a new one with root route (/)
    We will restore saved route and navigate user to it
    If user close a page and open a new one with some specific route
    We will open that route
    """

    clients_url = f"{admin_url}/clients"
    sites_url = f"{admin_url}/sites"
    users_url = f"{admin_url}/users"

    # Initial page for admin is /clients
    wait_for_url(browser, clients_url)

    # Go to sites page
    browser.visit(sites_url)

    # Open a new page with root route
    browser.visit(admin_url)

    # We have to be on closed page
    wait_for_url(browser, sites_url)

    # Open a new page with users route
    browser.visit(users_url)

    # We have to be on users page
    wait_for_url(browser, users_url)


def test_admin_saved_search(admin_url, browser):
    """
    When the user enters a search filter
    And then leaves the page and come back
    The UI remembers the filter entered
    """

    SEARCH_FILTER = "papaya"

    browser.visit(f"{admin_url}/sites")

    # Enters a filter
    browser.fill("search-input", SEARCH_FILTER)

    # If we reload, the filter is there
    browser.reload()
    assert browser.find_by_xpath(
        f"//input[@value='{SEARCH_FILTER}']", wait_time=TIME_TO_WAIT
    ).first
