from pathlib import Path

import pytest

from tests.constants import BROWSER_NAME
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
        splinter_webdriver=splinter_webdriver,
        splinter_file_download_dir=splinter_file_download_dir,
    )


@pytest.fixture(scope="session")
def splinter_screenshot_dir():
    return Path().cwd().joinpath("tests/splinter_images/")


@pytest.fixture(autouse=True)
def setup_db():
    recreate_db()
    clear_redis()


@pytest.fixture(autouse=True)
def log_browser_console_logs(request, browser):
    browser_console_logs_to_logger(browser=browser)


@pytest.fixture(scope="session")
def splinter_session_scoped_browser():
    return False
