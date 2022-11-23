import urllib.parse

import pytest
from selenium.webdriver.common.keys import Keys

from common_utils.constants import ADMIN_SIM_STATUS, DMS_PERMISSION
from handlers.db import SiteDBHandler, UserDBHandler
from tasks.mail_tasks import get_sendgrid_mail_configured, send_email_task
from tasks.utils.constants import EmailTypes
from tests.celery_utils import get_flower_all_tasks_metadata, wait_for_celery_tasks
from tests.constants import FLAKY_RERUNS, TIME_TO_WAIT, USERS
from tests.e2e_browser.utils_admin import (
    _get_admin_column_content,
    admin_click_save_and_assert_successful,
    make_login,
    safe_wait_for_table_and_expand_columns,
)
from tests.e2e_browser.utils_editor import clear_input
from tests.utils import create_user_context

NEW_USER_LOGIN = "dashboard_user"
NEW_USER_PASSWORD = "aDf1324!"
NEW_USER_EMAIL = "salpicado@salpicando.com"


def do_login(browser, url, user_type="ADMIN"):
    return make_login(browser, url, user_type)


def wait_for_form(browser):
    assert browser.find_by_xpath(
        "//div[contains(@class, 'field')]", wait_time=TIME_TO_WAIT
    ).first


def fill_new_user_form(browser, client_db, role):
    client_dropdown = browser.find_by_xpath(
        "//*[contains(@class, 'form-select-client_id')]", wait_time=TIME_TO_WAIT
    ).first
    client_dropdown.click()
    browser.find_by_xpath(
        f"//div[(text()='{client_db['name']}')]", wait_time=TIME_TO_WAIT
    ).first.click()

    group_dropdown = browser.find_by_xpath(
        "//*[contains(@class, 'form-select-group_id')]", wait_time=TIME_TO_WAIT
    ).first
    group_dropdown.click()
    browser.find_by_xpath(
        "//div[(text()='Archilyse')]", wait_time=TIME_TO_WAIT
    ).first.click()

    browser.fill("name", "New dashboard user")
    browser.fill("login", f"{NEW_USER_LOGIN}")
    browser.fill("password", f"{NEW_USER_PASSWORD}")
    browser.fill("email", f"{NEW_USER_EMAIL}")
    browser.find_by_xpath(
        "//*[contains(@class, 'form-select-roles')]", wait_time=TIME_TO_WAIT
    ).first.click()
    for available_role in browser.find_by_css("#menu-roles ul > li"):
        if available_role.text == role:
            available_role.type(Keys.ENTER)
            available_role.type(Keys.ESCAPE)  # To close dropdown with multiple options
            break
    admin_click_save_and_assert_successful(browser=browser)


def find_link_in_mail_and_visit_it(browser, dms_url, user_id):
    mail = get_sendgrid_mail_configured(
        user_id=user_id, email_type=EmailTypes.ACTIVATION_EMAIL
    ).get()
    encoded_html = urllib.parse.quote(mail["content"][0]["value"])
    browser.driver.get("data:text/html," + encoded_html)
    redirection_link = browser.links.find_by_partial_href(
        f"{dms_url}/password/reset"
    ).first
    browser.visit(redirection_link["href"])


def click_submit_and_get_error(browser):
    browser.find_by_xpath(
        "//button[@type='submit']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_visible_by_xpath(
        "//p[contains(@class, 'Mui-error')]", wait_time=TIME_TO_WAIT
    )


def test_admin_see_users_table(client_db, admin_url, browser):
    """
    When log in as an admin
    And visiting the users section
    We see a table with one row
    And the row belongs to the only user in the DB
    """
    context = do_login(browser, admin_url)
    browser.visit(admin_url + "/users")
    safe_wait_for_table_and_expand_columns(browser, "users_table", expected_rows=1)
    login = _get_admin_column_content(
        browser=browser, column_name="login", row_number=1, as_text=True
    )
    assert _get_admin_column_content(
        browser=browser, column_name="last_login", row_number=1, as_text=True
    )
    assert _get_admin_column_content(
        browser=browser, column_name="email_validated", row_number=1, as_text=True
    )
    assert context["login"] == login


def test_admin_create_user(client_db, admin_url, dms_url, browser):
    """
    When log in as an admin
    And visiting the users section
    We see a table with one row
    If we click on the "create button"
    We see a form to create an user
    If we fill the form and save and create a user for dms
    An user is created
    And we can log with it in the dashboard
    """
    do_login(browser, admin_url)
    browser.visit(admin_url + "/users")
    safe_wait_for_table_and_expand_columns(browser, "users_table", expected_rows=1)
    # Go to the create form
    browser.find_by_xpath(
        "//div[contains(@class, 'add-icon')]", wait_time=TIME_TO_WAIT
    ).first.click()

    wait_for_form(browser)

    fill_new_user_form(browser, client_db, role="ARCHILYSE_ONE_ADMIN")

    browser.visit(admin_url + "/users")
    safe_wait_for_table_and_expand_columns(browser, "users_table", expected_rows=2)

    # Log as this user in the dms
    browser.visit(dms_url + "/login")
    browser.fill("user", NEW_USER_LOGIN)
    browser.fill("password", NEW_USER_PASSWORD)
    browser.find_by_xpath(
        "//button[contains(text(), 'Sign in')]",  # xpath as the text is rendered with line breaks/blank chars
        wait_time=TIME_TO_WAIT,
    ).first.click()
    assert browser.is_element_visible_by_css(".dms-navbar", wait_time=TIME_TO_WAIT)


def test_admin_update_user(client_db, admin_url, browser):
    """
    When log in as an admin
    And visiting the users section
    If we edit a user and change its name
    The name is changed
    """
    context = do_login(browser, admin_url)
    browser.visit(admin_url + "/users")
    safe_wait_for_table_and_expand_columns(browser, "users_table", expected_rows=1)

    # Read current user name
    user_name = _get_admin_column_content(
        browser=browser, column_name="name", row_number=1, as_text=True
    )
    assert user_name == context["name"]

    # Edit user
    browser.find_by_xpath("//a[(text()='Edit')]", wait_time=TIME_TO_WAIT).first.click()

    wait_for_form(browser)
    browser.fill("name", "carota")
    clear_input(browser)
    browser.fill("name", "carota")
    admin_click_save_and_assert_successful(browser=browser)

    # Ensure name has changed
    browser.visit(admin_url + "/users")
    safe_wait_for_table_and_expand_columns(browser, "users_table", expected_rows=1)
    user_name = _get_admin_column_content(
        browser=browser, column_name="name", row_number=1, as_text=True
    )
    assert user_name == "carota"


def test_admin_delete_user(client_db, admin_url, browser):
    """
    When log in as an admin
    And visiting the users section with two users
    If we delete one
    The user is deleted
    """
    context = do_login(browser, admin_url)
    uploader_user = create_user_context(USERS["TEAMMEMBER"])["user"]

    # Delete user
    browser.visit(admin_url + "/users")
    browser.links.find_by_partial_href(f"/admin/user/{uploader_user['id']}").click()
    wait_for_form(browser)

    browser.find_by_xpath(
        "//div[contains(@class, 'delete-button')]",
        wait_time=TIME_TO_WAIT,
    ).first.click()
    # Confirm deletion
    browser.find_by_xpath(
        "//*[contains(@class, 'delete-button button-confirm')]",
        wait_time=TIME_TO_WAIT,
    ).first.click()
    browser.visit(admin_url + "/users")
    safe_wait_for_table_and_expand_columns(browser, "users_table", expected_rows=1)
    user_name = _get_admin_column_content(
        browser=browser, column_name="name", row_number=1, as_text=True
    )
    assert user_name == context["name"]


def test_admin_activate_user_password(
    client_db,
    admin_url,
    dms_url,
    browser,
):
    """
    Log in as admin
    Then visit the new user form and create a new user
    Visit generated link from sent mail
    There should be a Activate Password page
    Fill the form and send
    The password should be activated
    """
    new_activated_pswrd = "Pay4s0s!"

    do_login(browser, admin_url)
    browser.visit(admin_url + "/users")
    # Go to the create form
    browser.find_by_xpath(
        "//div[contains(@class, 'add-icon')]", wait_time=TIME_TO_WAIT
    ).first.click()

    wait_for_form(browser)
    fill_new_user_form(browser, client_db, role="ARCHILYSE_ONE_ADMIN")

    user = UserDBHandler.get_by(login=NEW_USER_LOGIN)
    find_link_in_mail_and_visit_it(browser, dms_url, user_id=user["id"])

    # Incorrectly fill the form
    browser.fill("password", new_activated_pswrd)
    browser.fill("repeated_password", "123")
    click_submit_and_get_error(browser)

    # Correctly fill the form
    clear_input(browser)
    browser.fill("repeated_password", new_activated_pswrd)
    admin_click_save_and_assert_successful(browser)

    browser.find_by_css(".MuiAlert-message a").first.click()

    wait_for_celery_tasks(num_tasks_expected=1)
    # regression TECH-1936
    tasks_metadata = get_flower_all_tasks_metadata()
    last_task = tasks_metadata[-1]
    assert send_email_task.__name__ in last_task["name"]
    assert eval(last_task["kwargs"]) == {
        "user_id": user["id"],
        "email_type": EmailTypes.ACTIVATION_EMAIL.name,
    }

    # Introduce the new password to login
    browser.fill("user", NEW_USER_LOGIN)
    browser.fill("password", new_activated_pswrd)

    browser.find_by_xpath(
        "//button[@type='submit']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.find_by_id("admin-header", wait_time=TIME_TO_WAIT).first


def test_dms_forgot_user_password(client_db, dms_url, browser):
    """
    Given a DMS user
    When going to the 'Forgot password' page
        and providing the email address & hit send
        and navigating to the email link
    Then the user should be redirected to the reset user password page.
        and after providing a pair of identical password strings
    Then the password should be updated on the user account.
    """
    uploader_user = create_user_context(USERS["DMS_LIMITED"])["user"]
    NEW_PASSWORD = "bDf1324!"

    browser.visit(dms_url + "/password/forgot")
    browser.fill("email", uploader_user["email"])
    admin_click_save_and_assert_successful(browser)

    wait_for_celery_tasks(num_tasks_expected=1)
    find_link_in_mail_and_visit_it(browser, dms_url, user_id=uploader_user["id"])

    browser.fill("password", NEW_PASSWORD)
    browser.fill("repeated_password", NEW_PASSWORD)
    admin_click_save_and_assert_successful(browser)

    browser.visit(f"{dms_url}/login")
    browser.fill("user", uploader_user["login"])
    browser.fill("password", NEW_PASSWORD)
    admin_click_save_and_assert_successful(browser)

    tasks_metadata = get_flower_all_tasks_metadata()
    last_task = tasks_metadata[-1]
    assert send_email_task.__name__ in last_task["name"]
    assert eval(last_task["kwargs"]) == {
        "user_id": uploader_user["id"],
        "email_type": EmailTypes.PASSWORD_RESET.name,
    }


def test_dms_reload_site(client_db, dms_url, browser):
    """
    Given a DMS user
    When going to the 'user profile' page
        and reloading the page
    Then the user should still be able to see the left sidebar
    """
    # 1. Visit user page
    do_login(browser, dms_url)
    browser.visit(dms_url + "/profile")

    # 2. Reload
    browser.reload()

    # 3. Assert that the sidebar is there
    assert browser.find_by_css(".left-sidebar-container").first


def test_dms_update_user_profile(client_db, dms_url, browser):
    """
    Given a DMS user
    On logging into the DMS
    The user should be able to navigate to the 'Profile' page
        by clicking on the settings link in the left sidebar
    Then the user should be able to update his/her email and password
        by clicking on the 'Edit profile' button
    """
    new_email = "payso@mail.com"
    new_pswrd = "aDf1324!"

    logged_user = do_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")

    # Find user's profile link in the sidebar and click on it
    browser.find_by_xpath(
        "//a[contains(@href, '/profile')]", wait_time=TIME_TO_WAIT
    ).first.click()

    # Find the 'Edit profile' button and click on it
    browser.find_by_xpath(
        "//button[@aria-label='edit profile']", wait_time=TIME_TO_WAIT
    ).first.click()

    assert browser.is_element_visible_by_css(
        ".user-profile-container", wait_time=TIME_TO_WAIT
    )

    # Check email validation
    edit_email = browser.find_by_id("edit_profile_email")
    edit_email.fill(f"{logged_user['email']}123")
    browser.find_by_xpath(
        "//button[@id='save_profile']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_visible_by_xpath(
        "//p[contains(@class, 'Mui-error')]", wait_time=TIME_TO_WAIT
    )
    clear_input(browser)
    edit_email.fill(new_email)

    # Not visible until the password has a value
    repeated_pasword = browser.find_by_xpath(
        "//input[contains(@name, 'repeated_password')]", wait_time=TIME_TO_WAIT / 2
    )
    assert len(repeated_pasword) == 0

    # Check password validation
    edit_password = browser.find_by_id("edit_profile_password")
    edit_password.fill(new_pswrd)
    browser.find_by_xpath(
        "//button[@id='save_profile']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_visible_by_xpath(
        "//p[contains(@class, 'Mui-error')]", wait_time=TIME_TO_WAIT
    )

    # If we can fill in a repeated password that means it has appeared (not visible by default)
    browser.fill("repeated_password", "123")
    browser.find_by_xpath(
        "//button[@id='save_profile']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_visible_by_xpath(
        "//p[contains(@class, 'Mui-error')]", wait_time=TIME_TO_WAIT
    )

    clear_input(browser)
    browser.fill("repeated_password", new_pswrd)
    admin_click_save_and_assert_successful(browser, save_id="save_profile")

    # Close the 'Edit profile' drawer and click on it
    cancel_button = browser.find_by_xpath(
        "//button[@class='close-button']", wait_time=TIME_TO_WAIT
    )
    cancel_button.first.click()

    # Find log out link and click on it
    browser.find_by_xpath(
        "//span[contains(text(), 'logout')]", wait_time=TIME_TO_WAIT
    ).first.click()

    browser.fill("user", logged_user["login"])
    browser.fill("password", new_pswrd)
    browser.find_by_xpath(
        "//button[@type='submit']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_present_by_id("admin-header", wait_time=TIME_TO_WAIT)


def add_permission(browser, permission, site_name):
    browser.fill("labels", site_name)
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.ENTER)
    browser.find_by_text(site_name).click()
    browser.find_by_id("permissions-dropdown").click()
    browser.find_by_text(permission).click()
    browser.find_by_text("Save").click()


@pytest.mark.flaky(reruns=FLAKY_RERUNS)
def test_dms_admin_update_permissions(
    client_db,
    dms_url,
    make_sites,
    dms_limited_user,
    site_with_full_slam_results_success,
    browser,
):
    """
    Given a DMS admin
    On entering their profile
    If they adds permissions to another user & site
    The permissions are shown & saved successfully
    """
    extra_site = make_sites(client_db)[0]
    SiteDBHandler.update(
        item_pks=dict(id=extra_site["id"]),
        new_values={
            "full_slam_results": ADMIN_SIM_STATUS.SUCCESS,
            "heatmaps_qa_complete": True,
        },
    )
    do_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")
    # Find user's login in the sidebar and click on it
    browser.find_by_xpath(
        "//a[contains(@href, '/profile')]", wait_time=TIME_TO_WAIT
    ).first.click()

    browser.find_by_text("Add permission").first.click()
    # Add read permission
    add_permission(browser, "Read", site_with_full_slam_results_success["name"])

    # Add edit permission
    add_permission(browser, "Edit", extra_site["name"])

    expected_read_permission = f"read:{site_with_full_slam_results_success['name']}"
    expected_edit_permission = f"edit:{extra_site['name']}"

    assert browser.find_by_text(expected_read_permission).first.visible
    assert browser.find_by_text(expected_edit_permission).first.visible

    browser.reload()

    browser.find_by_text(expected_read_permission).first.scroll_to()
    assert browser.find_by_text(expected_read_permission).first.visible
    assert browser.find_by_text(expected_edit_permission).first.visible


@pytest.mark.parametrize(
    "permission", [DMS_PERMISSION.WRITE_ALL.name, DMS_PERMISSION.READ_ALL.name]
)
def test_admin_update_permissions_all(
    client_db,
    dms_url,
    dms_limited_user,
    site_with_full_slam_results_success,
    browser,
    permission,
):
    """
    Given a DMS admin
    On entering their profile
    If they add permissions Read all or write all
    The permissions are shown & saved successfully
    """

    do_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")

    # Find user's login in the navbar and click on it
    browser.find_by_xpath(
        "//a[contains(@href, '/profile')]", wait_time=TIME_TO_WAIT
    ).first.click()

    browser.find_by_text("Add permission").first.click()

    add_permission(
        browser,
        "Read all" if permission == "READ_ALL" else "Edit all",
        site_with_full_slam_results_success["name"],
    )

    expected_permission_display = (
        "READ ALL" if permission == "READ_ALL" else "WRITE ALL"
    )

    assert browser.find_by_text(expected_permission_display).first.visible

    browser.reload()

    assert browser.find_by_text(expected_permission_display).first.visible


def test_dms_admin_create_user(
    client_db,
    dms_url,
    dms_limited_user,
    site_with_full_slam_results_success,
    browser,
):

    do_login(browser, dms_url, "ARCHILYSE_ONE_ADMIN")
    browser.find_by_xpath(
        "//a[contains(@href, '/profile')]", wait_time=TIME_TO_WAIT
    ).first.click()

    # Find the 'Create user' button and click on it
    browser.find_by_xpath(
        "//button[@aria-label='create user']", wait_time=TIME_TO_WAIT
    ).first.click()

    # Check for email validation and password matching,
    # initially fill form with an invalid email and mismatching passwords
    browser.fill_form(
        form_id="create-user-form",
        field_values={
            "name": "Test DMS User",
            "login": "test_dms_user",
            "email": "test_dms.com",
            "password": "aaaAAA123#",
            "repeated_password": "aaaAAA123",
        },
    )
    # Select "Admin" role
    browser.find_by_css(".create-user-container .form-select-roles").first.click()
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.click()

    browser.find_by_xpath(
        "//button[@id='save-dms-user']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_visible_by_xpath(
        "//p[contains(@class, 'Mui-error')]", wait_time=TIME_TO_WAIT
    )

    # Enter a valid email address
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.CONTROL, "a")
    active_web_element.send_keys(Keys.DELETE)
    browser.find_by_id("create_user_email").fill("test@dms.com")

    # This returns an error because the passwords aren't matching
    browser.find_by_xpath(
        "//button[@id='save-dms-user']", wait_time=TIME_TO_WAIT
    ).first.click()
    assert browser.is_element_visible_by_xpath(
        "//p[contains(@class, 'Mui-error')]", wait_time=TIME_TO_WAIT
    )

    # Enter a matching password
    active_web_element = browser.driver.switch_to.active_element
    active_web_element.send_keys(Keys.CONTROL, "a")
    active_web_element.send_keys(Keys.DELETE)
    browser.find_by_id("create_user_repeated_password").fill("aaaAAA123#")

    # The form should now be submitted succesfully
    admin_click_save_and_assert_successful(browser, save_id="save-dms-user")
    wait_for_celery_tasks(num_tasks_expected=1)

    assert UserDBHandler.get_by(name="Test DMS User")
