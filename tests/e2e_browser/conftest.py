import contextlib

import pytest
from selenium.common.exceptions import WebDriverException

from tests.constants import BROWSER_NAME, SPLINTER_SCREENSHOTS_DIRECTORY
from tests.utils import (
    browser_console_logs_to_logger,
    clear_redis,
    get_splinter_driver_kwargs,
    recreate_db,
)

pytest_plugins = (
    "tests.db_fixtures",
    "tests.constant_fixtures",
    "tests.annotations_fixtures",
    "tests.file_fixtures",
    "tests.helper_fixtures",
    "tests.mocks_fixtures",
    "tests.e2e_fixtures",
)


@pytest.fixture(scope="session")
def splinter_webdriver():
    """Override splinter webdriver name."""
    return BROWSER_NAME


@pytest.fixture(scope="session")
def splinter_driver_kwargs(splinter_webdriver, splinter_file_download_dir):
    return get_splinter_driver_kwargs(
        splinter_file_download_dir=splinter_file_download_dir,
        splinter_webdriver=splinter_webdriver,
    )


@pytest.fixture(scope="session")
def splinter_screenshot_dir():
    return SPLINTER_SCREENSHOTS_DIRECTORY


@pytest.fixture(autouse=True)
def setup_db():
    recreate_db()
    clear_redis()


@pytest.fixture(autouse=True)
def clear_cookies_and_storage(browser):
    yield "teardown"
    browser.driver.delete_all_cookies()
    # To clear for good the disk cache so overwritten url ids are not cached
    browser.driver.command_executor._commands["SEND_COMMAND"] = (
        "POST",
        "/session/$sessionId/chromium/send_command",
    )
    browser.driver.execute(
        "SEND_COMMAND", dict(cmd="Network.clearBrowserCache", params={})
    )
    with contextlib.suppress(WebDriverException):
        browser.execute_script("window.localStorage.clear()")
        browser.execute_script("window.sessionStorage.clear()")


@pytest.fixture(autouse=True)
def log_browser_console_logs(request, browser):
    browser_console_logs_to_logger(browser=browser)
