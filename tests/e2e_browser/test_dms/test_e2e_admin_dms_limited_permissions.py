import pytest

from tests.e2e_browser.utils_admin import make_login

# TODO limited permissions e2e


@pytest.mark.usefixtures("splinter_download_dir_autoclean")
class TestDMSAdmin:
    @pytest.fixture(autouse=True)
    def dms_limited_login(self, browser, dms_url):
        make_login(browser, dms_url, "DMS_LIMITED")
