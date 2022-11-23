from pathlib import Path

import pytest

from common_utils.constants import ADMIN_SIM_STATUS, USER_ROLE
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from tests.celery_utils import wait_for_celery_tasks
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_editor import (
    accept_snack_bar_message,
    assert_snack_bar_successful,
    click_save_button,
    make_login,
)
from tests.e2e_browser.utils_pipeline import assert_quality_is_visible_in_page
from tests.utils import get_wait_downloaded_file


@pytest.fixture(autouse=True)
def do_login(browser, login_url):
    make_login(browser, login_url)


def assert_button_enabled(enabled, button: str):
    if enabled:
        assert 'disabled=""' not in button
    else:
        assert 'disabled=""' in button


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER])
def test_quality_basic_flow(
    browser,
    quality_url,
    site,
    plan_box_pipelined,
    unit,
    qa_db,
    make_buildings,
    user_role,
    login_url,
):
    """
    Go to the quality window as a non-dev user
    When the quality window opens
    then the results are shown when the info is in the DB already
    then there are pipeline links for the displayed issues
    And we fill the validation notes and save the site.
    Then the site is marked as qa complete and the validation notes are saved
    """

    login = make_login(browser=browser, url=login_url, user_type=user_role.name)
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"group_id": login["group_id"]}
    )
    # Another building without plans to have blocking errors in the screen
    (building,) = make_buildings(site)
    # A unit with an unexpected client id for the site, so we have site warnings
    second_unit = UnitDBHandler.add(
        site_id=site["id"],
        plan_id=unit["plan_id"],
        floor_id=unit["floor_id"],
        apartment_no=1,
        client_id="random",
    )
    area = AreaDBHandler.find(plan_id=unit["plan_id"])[0]

    UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area["id"])
    UnitAreaDBHandler.add(unit_id=second_unit["id"], area_id=area["id"])

    assert SiteDBHandler.get_by(id=site["id"])["pipeline_and_qa_complete"] is False
    browser.visit(quality_url(site["id"]))
    browser.find_by_id("QaAnalysisButton", wait_time=TIME_TO_WAIT).first.click()
    wait_for_celery_tasks(num_tasks_expected=4)
    browser.reload()

    browser.is_element_present_by_id("quality_app")

    assert_quality_is_visible_in_page(browser=browser)

    # We display the client site id info & link
    assert browser.is_element_present_by_id("clientSiteIdBlock")
    assert browser.find_by_id("clientSiteIdBlockValue").text == site["client_site_id"]

    # Results loaded by default
    pipeline_links = browser.links.find_by_partial_href("/classification")
    # There is only one plan to click but is clickable both in the name and the external arrow
    assert len(pipeline_links) == 2

    # We can see the site error blockers
    errors_div = browser.find_by_xpath("//div[contains(@class, 'key error')]")
    assert len(errors_div) == 1
    assert errors_div.first.text == "Site Errors (Blockers):"
    assert (
        "Site contains a building without plans"
        in browser.find_by_css("div.value:nth-child(1)")[0].text
    )

    assert (
        browser.find_by_xpath("//div[contains(@class, 'key warning')]")[1].text
        == unit["client_id"]
    )
    assert browser.find_by_css("div.value:nth-child(1)")[1].text == "Kitchen missing"

    # Check building info appears
    assert browser.find_by_text(
        f" Building: {building['street']}, {building['housenumber']} ",
        wait_time=TIME_TO_WAIT,
    ).first

    # Check over the site warnings
    assert (
        browser.find_by_xpath("//div[contains(@class, 'key warning')]")[2].text
        == "Site warnings"
    )
    assert (
        "The following client unit ids you assigned are not part of this site"
        in browser.find_by_css("div.value:nth-child(1)")[2].text
    )

    # saving notes works
    expected_text = "This site is just a mess"
    browser.find_by_xpath("//textarea").first.fill(expected_text)
    browser.find_by_id("save_notes_button").first.click()
    assert_snack_bar_successful(browser=browser, msg_to_check="Quality notes saved")
    accept_snack_bar_message(browser=browser)
    assert browser.find_by_xpath(
        "//button[@id='save_notes_button' and contains(text(), 'Saved')]", wait_time=0.5
    ).first

    # Validating button
    # Validate button is first disabled because there are errors
    assert_button_enabled(
        enabled=False, button=browser.find_by_id("save_button").first.outer_html
    )
    # The building causing the site error is removed
    BuildingDBHandler.delete(item_pk={"id": building["id"]})

    browser.find_by_id("QaAnalysisButton").first.click()
    wait_for_celery_tasks(num_tasks_expected=8)
    # To display the QA data now we have to reload the browser to load from the API directly
    browser.reload()
    # After clicking again in run QA the button to VALIDATE is enabled
    click_save_button(browser=browser)
    # After press save, we wait till the successful message appears
    assert_snack_bar_successful(browser=browser)
    site_info = SiteDBHandler.get_by(id=site["id"])
    assert site_info["pipeline_and_qa_complete"] is True
    assert site_info["validation_notes"] == expected_text


def test_status_quality(browser, quality_url, site, plan_box_pipelined, unit, qa_db):
    for status, bf_button_enabled, qa_button_exist, msg in [
        (ADMIN_SIM_STATUS.FAILURE, True, True, "has failed"),
        (ADMIN_SIM_STATUS.PROCESSING, False, False, "being calculated"),
        (ADMIN_SIM_STATUS.PENDING, False, False, "on the queue to be calculated"),
        (
            ADMIN_SIM_STATUS.UNPROCESSED,
            True,
            True,
            "Click on Generate QA analysis to start",
        ),
    ]:
        SiteDBHandler.update(
            item_pks={"id": site["id"]},
            new_values={"basic_features_status": status.value},
        )

        if status == ADMIN_SIM_STATUS.FAILURE:
            SiteDBHandler.update(
                item_pks={"id": site["id"]},
                new_values={
                    "basic_features_error": {
                        "errors": [
                            {
                                "type": "AREA_NOT_DEFINED",
                                "human_id": f'Plan id: {plan_box_pipelined["id"]}, apartment_no: {unit["apartment_no"]}',
                                "position": {
                                    "type": "Point",
                                    "coordinates": [598.35, -455.61],
                                },
                                "object_id": 0,
                                "text": "An area is NOT_DEFINED",
                            }
                        ]
                    }
                },
            )

        browser.visit(quality_url(site["id"]))
        browser.is_element_present_by_id("quality_app", wait_time=TIME_TO_WAIT)

        browser.is_element_present_by_id("QaAnalysisButton", wait_time=TIME_TO_WAIT)
        browser.is_element_present_by_id("clientSiteIdBlock", wait_time=TIME_TO_WAIT)

        bf_button = browser.find_by_id("QaAnalysisButton").first.outer_html
        assert_button_enabled(bf_button_enabled, bf_button)

        if qa_button_exist:
            assert_button_enabled(
                enabled=True,
                button=browser.find_by_id(
                    "QaAnalysisButton", wait_time=1
                ).first.outer_html,
            )

        assert (
            msg in browser.find_by_id("base_app_surface", wait_time=TIME_TO_WAIT).text
        )


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER])
def test_click_basic_features_launch_task(
    browser, quality_url, site, plan_box_pipelined, unit, qa_db, user_role, login_url
):
    """
    Given a site with basic_features_status UNPROCESSED
    then the text for unprocessed is shown
    when clicking in the basicfeatures button
    then the task is launched
    """

    login = make_login(browser=browser, url=login_url, user_type=user_role.name)
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"group_id": login["group_id"]}
    )

    area = AreaDBHandler.find(plan_id=unit["plan_id"])[0]
    UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area["id"])

    browser.visit(quality_url(site["id"]))
    browser.is_element_present_by_id("quality_app", wait_time=TIME_TO_WAIT)
    browser.is_element_present_by_id("QaAnalysisButton", wait_time=TIME_TO_WAIT)
    browser.is_element_present_by_id("clientSiteIdBlock", wait_time=TIME_TO_WAIT)
    assert (
        "Click on Generate QA analysis to start"
        in browser.find_by_id("base_app_surface").text
    )

    browser.find_by_id("QaAnalysisButton", wait_time=TIME_TO_WAIT).first.click()

    queue_text = browser.is_text_present(
        "on the queue to be calculated soon", wait_time=TIME_TO_WAIT
    )
    refresh_text = browser.is_text_present(
        "QA analysis is being calculated, please refresh the page in a few minutes",
        wait_time=TIME_TO_WAIT,
    )
    assert queue_text or refresh_text
    bf_button = browser.find_by_id("QaAnalysisButton").first.outer_html
    assert_button_enabled(False, bf_button)

    wait_for_celery_tasks(num_tasks_expected=4)

    assert (
        SiteDBHandler.get_by(id=site["id"])["basic_features_status"]
        == ADMIN_SIM_STATUS.SUCCESS.value
    )


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN])
def test_generate_sample_surr_launch_task_failure(
    browser,
    quality_url,
    site,
    plan_box_pipelined,
    unit,
    qa_db,
    user_role,
    login_url,
):
    """
    Given a site with pipeline done and sample_surr UNPROCESSED
    then button shows Generate 3D and is blue
    when clicking in the Generate 3D button
    then the sample surr task is launched
    """

    login = make_login(browser=browser, url=login_url, user_type=user_role.name)
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"group_id": login["group_id"]}
    )

    area = AreaDBHandler.find(plan_id=unit["plan_id"])[0]
    UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area["id"])

    browser.visit(quality_url(site["id"]))
    browser.is_element_present_by_id("quality_app", wait_time=TIME_TO_WAIT)
    browser.is_element_present_by_id("SampleSurrButton", wait_time=TIME_TO_WAIT)
    browser.is_element_present_by_id("clientSiteIdBlock", wait_time=TIME_TO_WAIT)

    # Asserts about button text and class
    bf_button = browser.find_by_id("SampleSurrButton").first.outer_html
    assert_button_enabled(True, bf_button)
    assert "btn-primary" in bf_button
    assert "Generate Surroundings" in bf_button

    assert (
        SiteDBHandler.get_by(id=site["id"])["sample_surr_task_state"]
        == ADMIN_SIM_STATUS.UNPROCESSED.value
    )

    browser.find_by_id("SampleSurrButton", wait_time=TIME_TO_WAIT).first.click()
    browser.is_text_present("Generating Surroundings", wait_time=TIME_TO_WAIT)
    bf_button = browser.find_by_id("SampleSurrButton").first.outer_html
    assert_button_enabled(False, bf_button)
    assert "btn-warning" in bf_button

    # the 3 tasks chain
    wait_for_celery_tasks(num_tasks_expected=3)

    # Fails as the bucket is not there and site incomplete
    assert (
        SiteDBHandler.get_by(id=site["id"])["sample_surr_task_state"]
        == ADMIN_SIM_STATUS.FAILURE.value
    )
    browser.reload()
    browser.is_text_present("Re-Generate Surroundings (Failed)", wait_time=TIME_TO_WAIT)
    bf_button = browser.find_by_id("SampleSurrButton").first.outer_html
    assert_button_enabled(True, bf_button)
    assert "btn-danger" in bf_button


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN])
def test_generate_sample_surr_launch_task_success(
    browser,
    recreate_test_gcp_bucket,
    upload_sample_surroundings_to_google_cloud,
    quality_url,
    site,
    plan_box_pipelined,
    unit,
    qa_db,
    user_role,
    login_url,
    splinter_download_dir_autoclean,
):
    """
    Given a site with pipeline done and sample_surr SUCCESS
    then button shows Download SUrroundings
    when clicking in the button
    then the sample surr task file is downloaded
    """
    login = make_login(browser=browser, url=login_url, user_type=user_role.name)
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={
            "group_id": login["group_id"],
            "sample_surr_task_state": ADMIN_SIM_STATUS.SUCCESS.value,
        },
    )
    area = AreaDBHandler.find(plan_id=unit["plan_id"])[0]
    UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area["id"])
    upload_sample_surroundings_to_google_cloud(site_id=site["id"])

    browser.visit(quality_url(site["id"]))
    browser.is_element_present_by_id("quality_app", wait_time=TIME_TO_WAIT)
    browser.is_element_present_by_id("clientSiteIdBlock", wait_time=TIME_TO_WAIT)

    # Asserts about button text and class
    bf_button = browser.find_by_id("SampleSurrButton").first.outer_html
    assert_button_enabled(True, bf_button)
    assert "btn-success" in bf_button
    assert "Download Surroundings" in bf_button

    browser.find_by_id("SampleSurrButton", wait_time=TIME_TO_WAIT).first.click()
    file = get_wait_downloaded_file(Path(splinter_download_dir_autoclean))
    assert file.suffix == ".html"


def test_qa_blocked_if_pipeline_not_completed(
    browser, quality_url, site, client_db, make_sites, plan_box_pipelined, qa_db
):
    """
    Given a non pipelined site and an "empty" site (site_2)
    when accessing QA validation
    then there is a message of Pipeline not done
    and buttons are disabled
    """
    (site_2,) = make_sites(client_db)

    for s in (site, site_2):
        browser.visit(quality_url(site_id=s["id"]))
        browser.is_element_present_by_id("quality_app")

        assert browser.is_text_present(
            "finish the PIPELINE for all plans", wait_time=TIME_TO_WAIT
        )

        assert_button_enabled(
            enabled=False,
            button=browser.find_by_id("QaAnalysisButton").first.outer_html,
        )
        assert_button_enabled(
            enabled=False, button=browser.find_by_id("save_button").first.outer_html
        )
        # SampleSurrButton
        bf_button = browser.find_by_id("SampleSurrButton").first.outer_html
        assert_button_enabled(False, bf_button)
        assert "btn-secondary" in bf_button
        assert "Generate Surroundings" in bf_button
