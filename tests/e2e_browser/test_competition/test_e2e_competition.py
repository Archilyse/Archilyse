import pytest
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

from common_utils.competition_constants import CompetitionFeatures
from handlers.db import SiteDBHandler
from handlers.db.competition.competition_handler import CompetitionDBHandler
from tests.constants import TIME_TO_WAIT, USERS
from tests.db_fixtures import create_user_context
from tests.selenium_utils import expand_competition_category_upper_tab
from tests.utils import wait_for_url

DEFAULT_WEIGHTS = [
    ("Architektur – Allgemein", "27%"),
    ("Architektur – Projektspezifisch", "38%"),
    ("Umgebung – Allgemein", "20%"),
    ("Architektur – Kennzahlen", "15%"),
]

NEW_WEIGHTS = [
    ("Architektur – Allgemein", 30),
    ("Architektur – Projektspezifisch", 20),
    ("Umgebung – Allgemein", 15),
    ("Architektur – Kennzahlen", 35),
]

SAVE_BUTTON_TXT = "Speichern"


def enable_editing(browser, path):
    element = browser.driver.find_element_by_xpath(path)
    action = ActionChains(browser.driver)
    action.double_click(element).perform()


def fill_and_save(browser, input_name, value):
    browser.fill(input_name, value)
    input_element = browser.driver.find_element_by_xpath(
        f"//input[@name='{input_name}']"
    )
    input_element.send_keys(Keys.ENTER)


def expand_category_and_find_cells(browser, category_structure):
    category, sub_category, feature_name = category_structure

    expand_competition_category_upper_tab(browser=browser, category=category)
    browser.find_by_xpath(
        f"//div[text()='{sub_category}']/following-sibling::div//button"
    ).first.click()

    return find_cells_by_data_feature_name(browser, name=feature_name)


def find_cells_by_data_feature_name(browser, name):
    """
    Row has next structure:
    <tr>
        <td>Architecture Overview</td>
        <td>1</td>
        <td>2</td>
    </tr>
    Therefore in order to extract values we should ignore the first cell
    """
    cells = browser.find_by_xpath(
        f"//div[contains(text(), '{name}')]/ancestor::tr/td",
        wait_time=TIME_TO_WAIT,
    )

    return cells[1:]


def sign_in(browser, client_db, dashboard_url, user):
    browser.visit(dashboard_url + "/login")
    browser.fill("user", user["login"])
    browser.fill("password", user["password"])
    browser.find_by_text("Sign in").first.click()


@pytest.fixture
def login_as_competition_admin(browser, client_db, dashboard_url):
    user = create_user_context(USERS["COMPETITION_ADMIN"])["user"]
    sign_in(browser, client_db, dashboard_url, user)

    assert browser.is_element_visible_by_css(".competitions", wait_time=TIME_TO_WAIT)


@pytest.fixture
def login_as_admin(
    browser, client_db, dashboard_url, competition_with_fake_feature_values
):
    competition_id = competition_with_fake_feature_values["id"]
    user = create_user_context(USERS["ADMIN"])["user"]
    sign_in(browser, client_db, dashboard_url, user)

    # ADMIN user redirects to QA page by default
    assert browser.is_element_visible_by_css(".qa", wait_time=TIME_TO_WAIT)

    browser.visit(dashboard_url + f"/competition/{competition_id}")

    assert browser.is_element_visible_by_css(
        ".competition-tool", wait_time=TIME_TO_WAIT
    )


def test_dashboard_load_competitions(
    browser,
    dashboard_url,
    fake_competitions,
    login_as_competition_admin,
):
    """
    When an user logs as a competition admin
    It sees all the competitions related to its client
    If the user clicks on a competition name
    It will go to the view of that competition
    And using the navbar
    The user can navigate back to the list of competitions
    """

    # On load, all competitions should be shown
    for competition in fake_competitions:
        assert browser.find_by_text(competition["name"], wait_time=TIME_TO_WAIT)

    # Clicking in one will redirect to the specific view
    first_competition = fake_competitions[0]
    browser.find_by_text(first_competition["name"]).first.click()
    expected_url = f"{dashboard_url}/competition/{first_competition['id']}"
    wait_for_url(browser, expected_url)

    # We can navigate back using the navbar
    browser.find_by_text("Wettbewerbe", wait_time=TIME_TO_WAIT).first.click()

    expected_url = f"{dashboard_url}/competitions"
    wait_for_url(browser, expected_url)


def test_competition_change_weights(
    browser,
    dashboard_url,
    competition_with_fake_feature_values,
    login_as_competition_admin,
):
    """
    Log in into Competition Tool
    There should be table and sidebar with weights
    Update weights with new values
    Click on the Save button
    The competitors order should be changed
    """

    browser.visit(
        dashboard_url + f"/competition/{competition_with_fake_feature_values['id']}"
    )
    default_winner = SiteDBHandler.get_by(
        id=competition_with_fake_feature_values["competitors"][0]
    )["name"]
    big_weight_value = 60
    small_weight_value = 10

    # there should be all default weights and default winner
    for (label, value) in DEFAULT_WEIGHTS:
        assert browser.find_by_text(label, wait_time=TIME_TO_WAIT).first
        assert browser.find_by_text(value, wait_time=TIME_TO_WAIT).first

    assert browser.find_by_xpath(
        f"//th[@data-testid='winner' and text() = '{default_winner}']"
    ).first

    enable_editing(
        browser,
        path=f"//p[text()='{DEFAULT_WEIGHTS[0][0]}']/following-sibling::div",
    )
    fill_and_save(browser, "editable-weight", big_weight_value)
    browser.find_by_text(SAVE_BUTTON_TXT).first.click()
    assert browser.find_by_id("notification-error", wait_time=TIME_TO_WAIT)

    enable_editing(
        browser,
        path=f"//p[text()='{DEFAULT_WEIGHTS[0][0]}']/following-sibling::div",
    )
    fill_and_save(browser, "editable-weight", small_weight_value)
    browser.find_by_text(SAVE_BUTTON_TXT).first.click()
    assert browser.find_by_id("notification-error", wait_time=TIME_TO_WAIT)

    for (label, value) in NEW_WEIGHTS:
        enable_editing(browser, path=f"//p[text()='{label}']/following-sibling::div")
        fill_and_save(browser, "editable-weight", value)

    browser.find_by_text(SAVE_BUTTON_TXT).first.click()
    assert browser.find_by_id("notification-success", wait_time=TIME_TO_WAIT)

    for (label, value) in NEW_WEIGHTS:
        assert browser.find_by_text(label, wait_time=TIME_TO_WAIT).first
        assert browser.find_by_text(f"{value}%", wait_time=TIME_TO_WAIT).first


def test_competition_selected_features(
    browser,
    dashboard_url,
    competition_with_fake_feature_values,
    login_as_competition_admin,
):
    """Given a competition with all features"""
    browser.visit(
        dashboard_url + f"/competition/{competition_with_fake_feature_values['id']}"
    )
    browser.find_by_value("architecture_usage").click()
    """Both subcategories are present"""
    assert browser.is_element_present_by_text("Nutzung")
    assert browser.is_element_present_by_text("Lärm")
    """and noise features appear"""
    browser.find_by_id("expand_noise").click()
    assert browser.is_element_present_by_text('Analyse "Lärm"')
    assert browser.is_element_present_by_text("Lärm abgewandte Räume")
    scores_row = browser.find_by_css(
        "div.competition-tool-table-container > table > tbody > tr:nth-child(1)"
    )
    assert "6.1 5.6" in scores_row.text

    """Given we deselect one noise feature and refresh"""
    removed_features = {
        CompetitionFeatures.NOISE_STRUCTURAL,
    }
    features_selected = [f for f in CompetitionFeatures if f not in removed_features]
    CompetitionDBHandler.update(
        item_pks={"id": competition_with_fake_feature_values["id"]},
        new_values={"features_selected": features_selected},
    )
    browser.reload()
    browser.find_by_value("architecture_usage").click()
    """Both subcategories are still present"""
    assert browser.is_element_present_by_text("Nutzung")
    assert browser.is_element_present_by_text("Lärm")
    """and only one noise features appear"""
    browser.find_by_id("expand_noise").click()
    assert browser.is_element_not_present_by_text('Analyse "Lärm"', wait_time=0.5)
    assert browser.is_element_present_by_text("Lärm abgewandte Räume")
    scores_row = browser.find_by_css(
        "div.competition-tool-table-container > table > tbody > tr:nth-child(1)"
    )
    assert "5.4 4.9" in scores_row.text

    """Given we deselect ALL noise features and refresh"""
    removed_features = {
        CompetitionFeatures.NOISE_STRUCTURAL,
        CompetitionFeatures.NOISE_INSULATED_ROOMS,
    }
    features_selected = [f for f in CompetitionFeatures if f not in removed_features]
    CompetitionDBHandler.update(
        item_pks={"id": competition_with_fake_feature_values["id"]},
        new_values={"features_selected": features_selected},
    )
    browser.reload()
    browser.find_by_value("architecture_usage").click()
    """Only one subcategory is still present"""
    assert browser.is_element_present_by_text("Nutzung")
    assert browser.is_element_not_present_by_text("Lärm", wait_time=0.5)
    scores_row = browser.find_by_css(
        "div.competition-tool-table-container > table > tbody > tr:nth-child(1)"
    )
    assert "6.8 6.3" in scores_row.text


def test_competition_upload_competitors_data(
    browser,
    competition_with_fake_feature_values,
    login_as_admin,
):
    """
    As an ADMIN user
    I can see competition table
    And I can open 'Upload competitors data' modal, still in english (only for admins)
    And I can fill the table with competitors raw data
    Then I can see changed values in the table
    """
    competitors = [
        SiteDBHandler.get_by(id=competitor_id)
        for competitor_id in competition_with_fake_feature_values["competitors"]
    ]
    expected_raw_data = {
        CompetitionFeatures.DRYING_ROOM_SIZE.value: ("Yes", "No"),
    }
    raw_data_placeholders = {
        CompetitionFeatures.DRYING_ROOM_SIZE.value: "Yes/No",
    }

    browser.find_by_text("Upload Competitors data").first.click()
    modal = browser.find_by_css(".common-modal-container").first

    # ensure that competitors are there
    for competitor in competitors:
        assert modal.find_by_text(competitor["name"])

    # fill dropdown values
    for key in expected_raw_data:
        for expected_value in expected_raw_data[key]:
            placeholder = raw_data_placeholders[key]
            enable_editing(browser, path=f"//span[text()='{placeholder}']")

            dropdown = browser.find_by_xpath("//div[@role='presentation']").first
            dropdown.find_by_xpath(
                f"//li[text()='{expected_value}']", wait_time=TIME_TO_WAIT
            ).first.click()

    modal.find_by_text("Save").first.click()
    modal.find_by_text("Close").first.click()

    categories_structure = {
        "drying_room_size": [
            "Architektur – Projektspezifisch",
            "Trockenräume",
            "Anforderungen Trocknungsräume",
        ],
    }

    for key in categories_structure:
        cells = expand_category_and_find_cells(
            browser, category_structure=categories_structure[key]
        )
        for index, expected_text in enumerate(expected_raw_data[key]):
            cell = cells[index]
            assert cell.find_by_xpath(
                f"//*[text()='{expected_text}']", wait_time=TIME_TO_WAIT
            ).visible
