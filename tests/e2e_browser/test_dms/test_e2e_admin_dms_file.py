import pytest
from selenium.webdriver.common.keys import Keys

from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import (
    admin_assert_alert_successful,
    assert_tag_is_visible,
    assert_tags_interaction,
    expand_screen_size,
    get_uploaded_file_name,
    make_login,
    upload_file,
)
from tests.utils import get_wait_downloaded_file


class TestDMSAdminFiles:
    @pytest.fixture(autouse=True)
    def dms_admin_login(self, client_db, browser, dms_url):
        make_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")

    def test_dms_admin_upload_and_delete_file(
        self,
        dms_url,
        client_db,
        browser,
        site_with_full_slam_results_success,
        recreate_test_gcp_client_bucket,
        valid_image,
        pdf_floor_plan,
        building,
    ):
        """
        When opening the admin
        If we go to a site and upload a file
        The file will be there
        If we go to a building and upload a file
        The file will be there
        If we delete the file
        The file won't be there
        """
        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Go to a site
        browser.find_by_xpath(
            "//div[(@class='folder')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Upload file in sites
        upload_file(browser, valid_image)

        # Go to a building
        browser.find_by_xpath(
            "//div[(@class='folder')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Upload a file in buildings
        uploaded_file = upload_file(browser, pdf_floor_plan)

        # Display context menu
        uploaded_file.right_click()
        assert browser.find_by_xpath(
            "//*[contains(@class,'context-menu')]", wait_time=TIME_TO_WAIT
        ).first

        # Delete the file by clicking on context menu and confirming
        browser.find_by_xpath(
            "//*[contains(text(),'Delete')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert admin_assert_alert_successful

        file_uploaded_name = get_uploaded_file_name(pdf_floor_plan)
        assert browser.is_element_not_present_by_text(
            f"{file_uploaded_name}", wait_time=TIME_TO_WAIT
        )

    def test_dms_admin_download_file(
        self,
        dms_url,
        browser,
        dms_file,
        splinter_download_dir_autoclean,
        splinter_file_download_dir,
    ):
        """
        When opening the admin
        If we go to a site and upload a file
        The file will be there
        If we open context menu
        And click download
        We download a uploaded file
        """
        browser.visit(dms_url + f"/buildings?site_id={dms_file['site_id']}")

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Display context menu
        browser.find_by_xpath(
            "//div[(@class='file')]", wait_time=TIME_TO_WAIT
        ).right_click()

        assert browser.is_element_visible_by_xpath(
            "//*[contains(@class,'context-menu')]", wait_time=TIME_TO_WAIT
        )

        # Find download button
        download_button = browser.find_by_xpath(
            "//*[contains(text(),'Download')]", wait_time=TIME_TO_WAIT
        ).first

        # Download the file
        download_button.click()
        file = get_wait_downloaded_file(splinter_download_dir_autoclean)
        assert file is not None

    def test_dms_admin_tag_file(
        self,
        dms_url,
        browser,
        dms_file,
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
        browser.visit(dms_url + f"/buildings?site_id={dms_file['site_id']}")

        TAG_1 = "salpica"
        TAG_2 = "payaso"

        assert_tags_interaction(browser, [TAG_1, TAG_2])

    @pytest.mark.freeze_time("2020-08-04")
    def test_dms_admin_show_file_details(
        self,
        dms_url,
        browser,
        dms_file,
        splinter_download_dir_autoclean,
        splinter_file_download_dir,
    ):
        """
        When opening the admin
        If we click on a file
        A drawer with its details will be opened
        If download the file from there
        The file is downloaded
        If we change the tags from there
        The tags are updated
        If we delete the file from the drawer
        The file is deleted
        """
        TAG_1 = "salpica"
        TAG_2 = "carota"
        RANDOM_COMMENT_TEXT = "lorem ipsum salpica"

        browser.visit(dms_url + f"/buildings?site_id={dms_file['site_id']}")

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        browser.find_by_xpath(
            "//div[(@class='file')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert browser.find_by_xpath(
            "//div[(@class='details-tab')]", wait_time=TIME_TO_WAIT
        ).first

        # Download file
        download_button = browser.find_by_xpath(
            "//button[text()='Download']", wait_time=TIME_TO_WAIT
        ).first

        download_button.click()
        file = get_wait_downloaded_file(splinter_download_dir_autoclean)
        assert file is not None

        # Change tags using the drawer and ensure they are saved
        browser.fill("labels", TAG_1)
        active_web_element = browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ENTER)

        browser.fill("labels", TAG_2)
        active_web_element = browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ENTER)

        assert_tag_is_visible(browser, TAG_1)
        assert_tag_is_visible(browser, TAG_2)

        with expand_screen_size(browser=browser):
            # Add some comments
            browser.find_by_xpath(
                "//*[contains(text(),'Comments')]", wait_time=TIME_TO_WAIT
            ).first.click()

            assert browser.find_by_xpath(
                "//div[@class='comments']", wait_time=TIME_TO_WAIT
            ).first

            # Add a comment and press enter

            browser.fill("add-comment", RANDOM_COMMENT_TEXT)
            active_web_element = browser.driver.switch_to.active_element
            active_web_element.send_keys(Keys.ENTER)

            # Ensure the comment is there
            comments = browser.find_by_xpath(
                "//div[@class='comment']", wait_time=TIME_TO_WAIT
            )
            assert len(comments) == 1

        browser.find_by_xpath(
            "//div[text()='Details']", wait_time=TIME_TO_WAIT
        ).first.click()

        # Delete file
        browser.find_by_xpath(
            "//button[contains(@class,'details-delete-button')]",
            wait_time=TIME_TO_WAIT,
        ).first.click()

        assert admin_assert_alert_successful

        assert browser.is_element_not_present_by_text(
            f"{dms_file['name']}", wait_time=TIME_TO_WAIT
        )

    def test_dms_admin_open_file_details(self, dms_url, browser, dms_file):
        """
        When opening the admin
        If we click on a file
        A drawer with its details will be opened
        """
        browser.visit(dms_url + f"/buildings?site_id={dms_file['site_id']}")

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # click on a file and ensure drawer is open
        browser.find_by_xpath(
            "//div[(@class='file')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert browser.find_by_xpath(
            "//div[(@class='details-tab')]", wait_time=TIME_TO_WAIT
        ).first

    def test_dms_admin_trash(
        self,
        dms_url,
        client_db,
        browser,
        site_with_full_slam_results_success,
        recreate_test_gcp_client_bucket,
        valid_image,
        pdf_floor_plan,
        building,
    ):
        """
        When opening the admin
        If we go to a site and upload a file
        The file will be there
        If we open context menu
        And click delete
        We move file to the trash
        If we go to a trash page
        We will see the deleted file
        If we restore a file
        The file will be returned to site
        """
        browser.visit(
            dms_url
            + f"/sites?client_id={site_with_full_slam_results_success['client_id']}"
        )

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Go to a folder
        browser.find_by_xpath(
            "//div[(@class='folder')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Upload files
        upload_file(browser, valid_image)

        upload_file(browser, pdf_floor_plan)

        image_file_name = get_uploaded_file_name(valid_image)
        pdf_file_name = get_uploaded_file_name(pdf_floor_plan)

        browser.find_by_text(image_file_name).first.right_click()

        browser.find_by_xpath(
            "//*[contains(text(),'Delete')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert admin_assert_alert_successful

        assert browser.is_element_not_present_by_text(
            f"{image_file_name}", wait_time=TIME_TO_WAIT
        )

        browser.find_by_text(pdf_file_name).first.right_click()

        browser.find_by_xpath(
            "//*[contains(text(),'Delete')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert admin_assert_alert_successful

        assert browser.is_element_not_present_by_text(
            f"{pdf_file_name}", wait_time=TIME_TO_WAIT
        )

        browser.visit(dms_url + f"/trash?client_id={client_db['id']}")

        assert browser.find_by_xpath(
            f"//div[contains(@class, 'file') and  contains(.//div, '{image_file_name}')]",
            wait_time=TIME_TO_WAIT,
        ).first

        assert browser.find_by_xpath(
            f"//div[contains(@class, 'file') and  contains(.//div, '{pdf_file_name}')]",
            wait_time=TIME_TO_WAIT,
        ).first

        # Restore image file from trash
        browser.find_by_text(image_file_name).first.right_click()

        browser.find_by_xpath(
            "//*[contains(text(),'Restore')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert browser.is_element_not_present_by_text(
            f"{image_file_name}", wait_time=TIME_TO_WAIT
        )

        # Delete pdf file from trash
        browser.find_by_text(pdf_file_name).first.right_click()

        browser.find_by_xpath(
            "//*[contains(text(),'Delete permanently')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert browser.is_element_not_present_by_text(
            f"{pdf_file_name}", wait_time=TIME_TO_WAIT
        )

        # Go back to folder where files should have been restored
        browser.visit(dms_url + f"/sites?client_id={client_db['id']}")

        browser.find_by_xpath(
            "//div[(@class='folder')]", wait_time=TIME_TO_WAIT
        ).first.click()

        assert browser.find_by_xpath(
            f"//div[contains(@class, 'file') and  contains(.//div, '{image_file_name}')]",
            wait_time=TIME_TO_WAIT,
        ).first

    def test_dms_admin_move_file(self, dms_url, browser, building, dms_file):
        """
        When opening the DMS
        If we cut a file
        And paste it in another place
        The file is moved
        """
        browser.visit(dms_url + f"/buildings?site_id={dms_file['site_id']}")

        # Switch to grid view
        browser.find_by_xpath(
            "//*[contains(@class,'toggle-view-switch')]", wait_time=TIME_TO_WAIT
        ).first.click()

        # Cut the file
        browser.find_by_xpath(
            "//div[contains(@class, 'file')]", wait_time=TIME_TO_WAIT
        ).first.right_click()
        browser.find_by_text("Cut", wait_time=TIME_TO_WAIT).first.click()

        # Go to a building
        building_name = f"{building['street']}, {building['housenumber']}"
        browser.find_by_text(building_name, wait_time=TIME_TO_WAIT).first.click()

        # Paste and ensure is there after reloading
        browser.find_by_xpath("//button[@aria-label='paste']").first.click()
        assert browser.is_element_visible_by_xpath(
            "//div[contains(@class, 'file')]", wait_time=TIME_TO_WAIT
        )

        browser.reload()

        assert browser.is_element_visible_by_xpath(
            "//div[contains(@class, 'file')]", wait_time=TIME_TO_WAIT
        )
