import time

import pytest

from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import assert_tags_interaction, make_login


class TestDMSAdminFolder:
    @pytest.fixture(autouse=True)
    def dms_admin_login(self, client_db, browser, dms_url):
        make_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")

    @staticmethod
    def find_folder(browser, folder_name):
        return browser.find_by_xpath(
            f"//div[contains(@class,'folder') and .//*[contains(text(), '{folder_name}')]]",
            wait_time=TIME_TO_WAIT,
        ).first

    def create_folder(self, browser, folder_name="my folder"):
        # Click on add folder
        create_folder_button = browser.find_by_xpath(
            "//button[@aria-label='add folder']", wait_time=TIME_TO_WAIT
        )
        create_folder_button.first.click()

        # Fills the input text with the folder name and click on "Accept"
        browser.find_by_id("name").fill(folder_name)
        browser.find_by_text("Accept").first.click()
        # We close the notification, allowing also renders to finish
        self.close_notification(browser=browser)

    @staticmethod
    def close_notification(browser):
        browser.find_by_xpath("//button[@title = 'Close']").first.click()

    @classmethod
    def check_notification_and_close(
        cls, browser, expected_text, max_time=TIME_TO_WAIT
    ):
        timenow = time.time()
        text = ""
        while time.time() - timenow < max_time:
            text = browser.find_by_xpath(
                "//div[@role = 'alert']", wait_time=TIME_TO_WAIT
            ).first.text
            if expected_text == text:
                break

        assert text == expected_text
        cls.close_notification(browser)

    def test_dms_admin_create_folder(self, client_db, dms_url, browser):
        """
        Given I'm in the sites screen
        When I create a new folder
        Then it appears in the list
        """

        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        self.create_folder(browser)

        # Asserts if the folder has been created
        new_folder_row = browser.find_by_text("my folder", wait_time=TIME_TO_WAIT)

        assert new_folder_row.first

    def test_dms_admin_rename_folder(self, client_db, dms_url, browser):
        """
        Given I'm in the sites screen
        When I create a new folder
        And I rename it
        Then it appears in the list with the new name
        """

        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        self.create_folder(browser)

        # Display context menu
        browser.find_by_text("my folder", wait_time=TIME_TO_WAIT).first.right_click()

        # Open the rename folder dialog by clicking on "Rename"
        browser.find_by_xpath(
            "//li[contains(text(),'Rename')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Fills the input text with the new folder name and clicks on "Accept"
        browser.find_by_id("name").fill("my renamed folder")
        browser.find_by_text("Accept").first.click()

        # Asserts if the folder has been renamed
        renamed_folder_row = browser.find_by_text(
            "my renamed folder", wait_time=TIME_TO_WAIT
        )
        assert renamed_folder_row.first

    def test_dms_admin_create_subfolder(self, client_db, dms_url, browser):
        """
        Given I'm in the sites screen
        And I've created a new folder
        And I enter to the new folder
        When I create a new sub folder
        Then it appears in the list
        """

        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        self.create_folder(browser)
        # Clicks on the new created folder
        browser.find_by_text("my folder", wait_time=TIME_TO_WAIT).first.click()

        self.create_folder(browser, "my subfolder")

        # Asserts if the sub folder has been created
        new_folder_row = browser.find_by_text("my subfolder", wait_time=TIME_TO_WAIT)
        assert new_folder_row.first

    def test_dms_admin_restore_deleted_folder(self, client_db, dms_url, browser):
        """
        Given I have removed a folder
        When I restore it
        Then it appears in the list again
        """
        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        self.create_folder(browser)

        # Display context menu
        browser.find_by_text("my folder", wait_time=TIME_TO_WAIT).first.right_click()

        # Clicks on delete
        browser.find_by_xpath(
            "//li[contains(text(),'Delete')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Clicks on trash button to go to trash view
        browser.find_by_xpath(
            "//span[contains(text(),'Trash')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Asserts if the folder has been moved to trash
        folder = browser.find_by_text("my folder", wait_time=TIME_TO_WAIT)
        assert folder.first

        # Display context menu
        browser.find_by_text("my folder", wait_time=TIME_TO_WAIT).first.right_click()

        # Clicks on Restore
        browser.find_by_xpath(
            "//li[contains(text(),'Restore')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # # We go back to the folder
        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        # Asserts if the folder has been restored from trash
        folder = browser.find_by_text("my folder", wait_time=TIME_TO_WAIT)
        assert folder.first

    def test_dms_admin_tag_folder(
        self, site_with_full_slam_results_success, client_db, dms_url, browser, dms_file
    ):
        """
        When opening the admin
        We upload a file and switch to table view
        If we add some tags
        The tags will be visible
        If we reload the page
        The tags will be there
        If we erase a tag
        That tag will not be there
        """
        browser.visit(
            dms_url + f"/buildings?site_id={site_with_full_slam_results_success['id']}"
        )

        TAG_1 = "papaya"
        TAG_2 = "aguacate"

        self.create_folder(browser)

        assert_tags_interaction(browser, [TAG_1, TAG_2])

    def test_dms_admin_move_folder(
        self, dms_url, browser, building, dms_folder, dms_subfolder
    ):
        """
        When opening the DMS
        If we cut a folder
        And paste it in another place
        The folder is moved
        If we access inside the folder
        Its contents have been copied recursively
        """

        browser.visit(dms_url + f"/buildings?site_id={dms_folder['site_id']}")

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Cut the folder
        browser.find_by_text(
            dms_folder["name"], wait_time=TIME_TO_WAIT
        ).first.right_click()
        browser.find_by_text("Cut", wait_time=TIME_TO_WAIT).first.click()

        # Go to a building
        building_name = f"{building['street']}, {building['housenumber']}"
        browser.find_by_text(building_name, wait_time=TIME_TO_WAIT).first.click()

        # Paste and ensure is there after reloading
        browser.find_by_xpath("//button[@aria-label='paste']").first.click()
        assert self.find_folder(browser, dms_folder["name"])

        browser.reload()

        assert self.find_folder(browser, dms_folder["name"])

        # If the user goes inside the moved folder, its contents (subfolders, files) have also been moved
        folder = self.find_folder(browser, dms_folder["name"])
        folder.click()

        # Assert subfolder is there and then click on it (this order of actions is necessary to avoid stale element errors)
        subfolder = self.find_folder(browser, dms_subfolder["name"])
        subfolder.click()

        assert browser.is_element_visible_by_xpath(
            "//div[contains(@class, 'file')]", wait_time=TIME_TO_WAIT
        )

    def test_dms_admin_move_folder_into_folder(self, dms_url, browser, dms_folder):
        """
        When opening the DMS
        If we cut a folder
        And paste it in another folder
        The folder is moved
        """

        browser.visit(dms_url + f"/buildings?site_id={dms_folder['site_id']}")

        # Switch to grid view to find elements easier
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Create a folder
        FOLDER_NAME = "super_folder"
        self.create_folder(browser=browser, folder_name=FOLDER_NAME)

        # Cut one of the folders
        browser.find_by_text(
            dms_folder["name"], wait_time=TIME_TO_WAIT
        ).first.right_click()
        browser.find_by_text("Cut", wait_time=TIME_TO_WAIT).first.click()

        self.check_notification_and_close(
            browser=browser,
            expected_text=f"{dms_folder['name']} copied in the clipboard",
        )
        # Go to the other one
        browser.find_by_text(FOLDER_NAME, wait_time=TIME_TO_WAIT).first.click()

        # Paste and ensure is there after reloading
        browser.find_by_xpath("//button[@aria-label='paste']").first.click()
        self.check_notification_and_close(
            browser=browser,
            expected_text=f"{dms_folder['name']} successfully moved",
        )
        assert self.find_folder(browser, folder_name=dms_folder["name"])

        browser.reload()

        assert self.find_folder(browser, folder_name=dms_folder["name"])
