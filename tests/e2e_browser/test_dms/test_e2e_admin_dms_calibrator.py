import pytest

from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import make_login


@pytest.mark.usefixtures("splinter_download_dir_autoclean")
class TestDMSAdmin:
    @pytest.fixture(autouse=True)
    def dms_login(self, client_db, browser, dms_url):
        make_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")

    def test_dms_admin_analysis_chart_interaction(
        self,
        browser,
        dms_url,
        site_1439_simulated,
        dms_login,
    ):
        """
        When opening a site page
        There will be a Pie Chart showing distribution for the buildings
        If we hover over a building
        The pie chart will show the distribution for that building
        """
        EXPECTED_DEFAULT_M2 = "1423.8m2"

        browser.visit(
            dms_url + f"/buildings?site_id={site_1439_simulated['site']['id']}"
        )

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Ensure a default chart shows for the current buildings
        assert browser.is_element_present_by_xpath(
            f"//div[(@class='analysis')]//*[contains(text(), '{EXPECTED_DEFAULT_M2}')]",
            wait_time=TIME_TO_WAIT,
        )

        # Select a building and ensure its analysis chart is loaded
        building_1_street = site_1439_simulated["building"][0]["street"]

        building_1_folder = browser.find_by_xpath(
            "//div[(@class='folder')]",
            wait_time=TIME_TO_WAIT,
        ).first
        building_1_folder.mouse_over()
        assert browser.find_by_xpath(
            f"//div[(@class='analysis')]//*[contains(text(), '{building_1_street}')]",
            wait_time=TIME_TO_WAIT,
        ).first
        # De-select the building to ensure the default chart
        browser.find_by_xpath(
            "//a[(@class='breadcrumb-link')]"
        ).first.mouse_over()  # Explicitly mouse over outside of the grid to avoid an accidental hover over other item
        assert browser.find_by_xpath(
            f"//div[(@class='analysis')]//*[contains(text(), '{EXPECTED_DEFAULT_M2}')]",
            wait_time=TIME_TO_WAIT,
        ).first
