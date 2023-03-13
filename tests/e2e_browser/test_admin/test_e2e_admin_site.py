import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest
from celery.states import FAILURE, SUCCESS
from selenium.webdriver.common.keys import Keys
from splinter.driver.webdriver import BaseWebDriver

from brooks.classifications import CLASSIFICATIONS
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    REGION,
    SIMULATION_VERSION,
    USER_ROLE,
)
from handlers.db import (
    ClientDBHandler,
    GroupDBHandler,
    PlanDBHandler,
    QADBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from tasks.surroundings_tasks import generate_geo_referencing_surroundings_for_site_task
from tests.celery_utils import (
    confirm_no_tasks_unfinished,
    get_flower_all_tasks_metadata,
    wait_for_celery_tasks,
)
from tests.constants import TIME_TO_WAIT
from tests.db_fixtures import login_as
from tests.e2e_browser.utils_admin import (
    _get_admin_column_content,
    _get_admin_row_content_by_row_id,
    admin_assert_alert_successful,
    admin_click_save_and_assert_successful,
    expand_screen_size,
    make_login,
    navigate_to_child,
    navigate_to_child_and_create,
    reload_and_count_ready_columns,
    safe_wait_for_table_and_expand_columns,
)
from tests.utils import get_wait_downloaded_file

XPATH_FEATURES_GENERATION_BUTTON = (
    "//button[contains(@class, 'generate-features-button')]"
)
XPATH_DROP_DOWN_GROUP = "//div[contains(@class, 'MuiSelect-root') and @role='button']"


@pytest.fixture
def sites_groups(make_sites, client_db, upwork_group, oecc_group):
    return {
        "no_group": make_sites(client_db)[0],
        "other_group": make_sites(client_db, group_id=upwork_group["id"])[0],
        "teammember_group": make_sites(client_db, group_id=oecc_group["id"])[0],
    }


@pytest.fixture
def navigate_to_sites_table(admin_url, browser):
    def f(client_id, expected_sites):
        browser.visit(admin_url + "/clients")
        safe_wait_for_table_and_expand_columns(
            browser, "clients_table", expected_rows=1
        )
        navigate_to_child(browser, f"/sites?client_id={client_id}")
        safe_wait_for_table_and_expand_columns(
            browser, "sites_table", expected_rows=expected_sites
        )

    return f


def get_dropdown_for_site(browser, site_id, column_name="group"):
    row = _get_admin_row_content_by_row_id(browser, row_id=site_id)
    return row.find_by_xpath(f"div[@col-id='{column_name}']").first


class TestAsTeammember:
    @pytest.fixture(autouse=True)
    def do_login(self, browser, admin_url):
        make_login(browser, admin_url, user_type="TEAMMEMBER")

    def test_admin_panel_can_has_filters(self, client_db, admin_url, browser):
        browser.visit(admin_url + "/sites")
        assert len(browser.find_by_css(".site_id", wait_time=TIME_TO_WAIT)) > 0
        assert len(browser.find_by_css(".site_name", wait_time=TIME_TO_WAIT)) > 0
        assert len(browser.find_by_css(".client_site_id", wait_time=TIME_TO_WAIT)) > 0

    @pytest.mark.parametrize(
        "simulation_version",
        [SIMULATION_VERSION.PH_01_2021, SIMULATION_VERSION.PH_2022_H1],
    )
    def test_admin_panel_site_add_trigger_tasks(
        self,
        client_db,
        admin_url,
        browser,
        site_coordinates,
        qa_spreadsheet,
        simulation_version,
    ):
        """
        Given an existing client
        When a new site is created
        And its QA data filled
        Then there is a new site in the DB
        And QA data for that site
        and QA data format is not a list
        And 1 task have been triggered
        And 1 task is to create the surroundings for georeferencing
        And it fails because they are no swiss topo files in GCS
        """
        browser.visit(admin_url + "/clients")
        safe_wait_for_table_and_expand_columns(
            browser, "clients_table", expected_rows=1
        )
        navigate_to_child_and_create(
            browser, f"/sites?client_id={client_db['id']}", expected_table="sites_table"
        )
        navigation_started_time = datetime.utcnow()
        priority = 10
        browser.fill("name", "test_site")
        browser.fill("region", "1")
        browser.fill("lat", str(site_coordinates["lat"]))
        browser.fill("priority", priority)
        browser.fill("lon", str(site_coordinates["lon"]))

        # simulation version
        browser.find_by_css(".form-select-simulation_version").first.click()
        browser.find_by_xpath(
            f"//*[@data-value = '{simulation_version.name}']"
        ).first.click()

        browser.find_by_text("QA").first.click()
        qa_file = browser.find_by_id("qa_file")
        qa_file.fill(qa_spreadsheet.as_posix())

        browser.find_by_text("General").first.click()

        admin_click_save_and_assert_successful(browser=browser)

        sites = SiteDBHandler.get_all_by_client(client_id=client_db["id"])
        wait_for_celery_tasks(num_tasks_expected=1)
        tasks_metadata = get_flower_all_tasks_metadata()
        last_task_executed = tasks_metadata[-1]

        assert len(sites) == 1
        assert sites[0]["lat"] == float(site_coordinates["lat"])
        assert sites[0]["lon"] == float(site_coordinates["lon"])
        assert sites[0]["priority"] == priority
        assert sites[0]["simulation_version"] == simulation_version.name

        qa_data = QADBHandler.get_by(site_id=sites[0]["id"])
        assert isinstance(qa_data["data"], dict)

        assert last_task_executed["name"].endswith(
            generate_geo_referencing_surroundings_for_site_task.__name__
        ), last_task_executed["name"]
        assert last_task_executed["received"] > int(
            navigation_started_time.strftime("%s")
        )
        assert last_task_executed["state"] == FAILURE, last_task_executed

    def test_admin_panel_site_lat_lon_map(
        self,
        client_db,
        admin_url,
        browser,
        site_coordinates,
        qa_spreadsheet,
    ):
        """
        When user tries to create a new site
        It can enter the address in a map
        And the form will be filled with lat & lon of that address
        If it submit the form
        A new site with that lat & lon will be created
        """
        TECHNOPARK_LON = 8.5151409
        TECHNOPARK_LAT = 47.3901151

        browser.visit(admin_url + f"/sites?client_id={client_db['id']}")
        safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=0)
        browser.find_by_css(".add-icon", wait_time=TIME_TO_WAIT).first.click()

        priority = 10
        browser.fill("name", "test_site")
        browser.fill("region", "Zurich")
        browser.fill("priority", priority)

        # Enter address in the map
        map_search_input = browser.find_by_css(
            ".map-search-input", wait_time=TIME_TO_WAIT
        ).first
        map_search_input.type("Technopark, 1, Technoparkstrasse, Zurich")
        active_web_element = browser.driver.switch_to.active_element
        active_web_element.send_keys(Keys.ENTER)

        # The address should have turned into lat lon in the form
        assert browser.find_by_xpath(
            f"//input[@name = 'lon' and contains(@value, '{str(TECHNOPARK_LON)[:4]}')]"
        ).first
        assert browser.find_by_xpath(
            f"//input[@name = 'lat' and contains(@value, '{str(TECHNOPARK_LAT)[:4]}')]"
        ).first

        admin_click_save_and_assert_successful(browser=browser)

        # Ensure lat lon are saved succesfully
        sites = SiteDBHandler.get_all_by_client(client_id=client_db["id"])
        wait_for_celery_tasks(num_tasks_expected=1)

        assert len(sites) == 1
        assert sites[0]["lat"] == pytest.approx(TECHNOPARK_LAT, abs=0.1)
        assert sites[0]["lon"] == pytest.approx(TECHNOPARK_LON, abs=0.1)

    def test_admin_panel_site_edit_update_qa(
        self,
        site,
        qa_db,
        admin_url,
        browser,
        qa_spreadsheet,
    ):
        """
        Given an existing client and site and qa_data
        when editing a site
        then in the qa panel the data should be shown
        when uploading new qa data
        then the qa data should change
        """
        browser.visit(admin_url + f"/site/{site['id']}")
        browser.find_by_text("QA").first.click()

        safe_wait_for_table_and_expand_columns(browser, "site_qa_table")

        qa_file = browser.find_by_id("qa_file")
        qa_file.fill(qa_spreadsheet.as_posix())
        browser.find_by_text("General").first.click()

        admin_click_save_and_assert_successful(browser=browser)
        assert QADBHandler.get_by(id=qa_db["id"])["data"] != qa_db["data"]

    def test_admin_panel_site_edit_creates_qa(
        self,
        site,
        qa_db,
        admin_url,
        browser,
        qa_spreadsheet,
    ):
        """
        Given an existing client and site
        when editing a site
        when uploading new qa data
        then the qa data should change
        """
        browser.visit(admin_url + f"/site/{site['id']}")
        browser.find_by_text("QA").first.click()

        qa_file = browser.find_by_id("qa_file")
        qa_file.fill(qa_spreadsheet.as_posix())
        browser.find_by_text("General").first.click()

        admin_click_save_and_assert_successful(browser=browser)
        assert QADBHandler.get_by(id=qa_db["id"])["data"] != qa_db["data"]

    @login_as(["TEAMMEMBER"])
    def test_site_ready_column(
        self,
        browser: BaseWebDriver,
        admin_url,
        client_db,
        make_sites,
        make_buildings,
        make_plans,
        login,
    ):
        """
        Given 2 sites
        and a building for each site
        and 2 plans for first site and 1 for second site
        then at admin site view the ready column shows not ready symbols
        """
        num_sites = 2
        site1, site2 = make_sites(
            *((client_db,) * num_sites), group_id=login["group"]["id"]
        )
        building1, building2 = make_buildings(site1, site2)
        plan1, plan2, plan_building2 = make_plans(building1, building1, building2)

        browser.visit(admin_url + f"/sites?client_id={client_db['id']}")
        safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=2)
        assert browser.is_element_visible_by_css(
            "[col-id='ready']", wait_time=TIME_TO_WAIT
        )

        not_ready_elems = browser.find_by_css(
            "[col-id='ready'] .cross", wait_time=TIME_TO_WAIT
        )
        assert len(not_ready_elems) == 2

        # when plan for building2 is finished
        # then its ready sign is positive
        PlanDBHandler.update(
            item_pks=dict(id=plan_building2["id"]),
            new_values=dict(annotation_finished=True),
        )

        ready_elems, not_ready_elems = reload_and_count_ready_columns(browser)
        assert len(not_ready_elems) == 1
        assert len(ready_elems) == 1

        # when 1 plan for building1 is finished
        # then its ready sign is still negative because both plans for the site needs to be finished
        PlanDBHandler.update(
            item_pks=dict(id=plan1["id"]), new_values=dict(annotation_finished=True)
        )

        ready_elems, not_ready_elems = reload_and_count_ready_columns(browser)
        assert len(not_ready_elems) == 1
        assert len(ready_elems) == 1

        # when 1 plan for building1 is finished
        # then its ready sign is positive
        PlanDBHandler.update(
            item_pks=dict(id=plan2["id"]), new_values=dict(annotation_finished=True)
        )

        ready_elems, not_ready_elems = reload_and_count_ready_columns(browser)
        assert len(not_ready_elems) == 0
        assert len(ready_elems) == 2

    @login_as(["TEAMMEMBER"])
    def test_pipeline_completed_gets_updated(
        self, browser: BaseWebDriver, admin_url, client_db, make_sites, login
    ):
        site1 = make_sites(client_db, group_id=login["group"]["id"])[0]

        browser.visit(admin_url + f"/sites?client_id={client_db['id']}")
        safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=1)
        pipeline_and_qa_complete_false = _get_admin_column_content(
            browser, "pipeline_and_qa_complete", as_text=False
        ).find_by_css(".cross", wait_time=TIME_TO_WAIT)
        assert not pipeline_and_qa_complete_false.is_empty()

        SiteDBHandler.update(
            item_pks={"id": site1["id"]}, new_values={"pipeline_and_qa_complete": True}
        )
        browser.reload()
        safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=1)
        pipeline_and_qa_complete_true = _get_admin_column_content(
            browser, "pipeline_and_qa_complete", as_text=False
        ).find_by_css(".check", wait_time=TIME_TO_WAIT)

        assert not pipeline_and_qa_complete_true.is_empty()

    def test_user_cant_see_others_groups_sites(
        self,
        browser: BaseWebDriver,
        admin_url,
        sites_groups,
        client_db,
        navigate_to_sites_table,
    ):
        """
        Given 1 site with not group_id
        and a site with group_id = upwork
        and a site with group_id = oecc_group
        when user of group oecc access sites in admin
        then only one site is present
        and this site is the one belonging to oecc
        """
        navigate_to_sites_table(client_db["id"], expected_sites=1)

        assert _get_admin_column_content(browser, "id") == str(
            sites_groups["teammember_group"]["id"]
        )

    def test_uploader_cant_see_admin_fields(
        self,
        browser: BaseWebDriver,
        admin_url,
        client_db,
        navigate_to_sites_table,
        site_coordinates,
        oecc_group,
    ):
        for i, delivered in enumerate([True, False]):
            SiteDBHandler.add(
                client_id=client_db["id"],
                client_site_id=f"random site {i}",
                full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
                delivered=delivered,
                name=f"My custom site {i}",
                region="Switzerland",
                group_id=oecc_group["id"],
                georef_region=REGION.CH.name,
                **site_coordinates,
            )

        num_sites = 2
        num_sites_delivered = 1
        navigate_to_sites_table(client_db["id"], expected_sites=num_sites)
        expected_sites = num_sites - num_sites_delivered
        # the Pipelines link is not visible in the site that is delivered
        assert len(browser.links.find_by_text("Pipelines")) == expected_sites

        assert browser.is_element_not_present_by_xpath(
            XPATH_DROP_DOWN_GROUP, wait_time=1
        )
        assert browser.is_element_not_present_by_xpath(
            XPATH_FEATURES_GENERATION_BUTTON, wait_time=1
        )


class TestAsAdmin:
    @pytest.fixture(autouse=True)
    def do_login(self, browser, admin_url):
        make_login(browser, admin_url)

    def test_download_existing_zip_file_from_website(
        self,
        browser: BaseWebDriver,
        admin_url,
        client_db,
        site,
        upload_deliverable_zip_file_to_gcs,
        splinter_download_dir_autoclean,
    ):

        SiteDBHandler.update(
            item_pks={"id": site["id"]},
            new_values={"full_slam_results": ADMIN_SIM_STATUS.SUCCESS},
        )

        browser.visit(admin_url + f"/sites?client_id={client_db['id']}")
        safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=1)

        download_zip = browser.find_by_text("Zip")
        assert len(download_zip) == 1

        download_zip.click()
        file = get_wait_downloaded_file(Path(splinter_download_dir_autoclean))
        assert file.suffix == ".zip"
        assert zipfile.ZipFile(file).testzip() is None

    def test_upload_custom_valuator_results(
        self,
        browser: BaseWebDriver,
        admin_url,
        site,
        units_with_vector_with_balcony,
        navigate_to_sites_table,
        fixtures_path,
    ):
        num_sites = 1
        navigate_to_sites_table(site["client_id"], expected_sites=num_sites)
        with expand_screen_size(browser=browser):

            safe_wait_for_table_and_expand_columns(
                browser, "sites_table", expected_rows=num_sites
            )

            # upload good file = success
            browser.find_by_id("ph_results_file_upload", wait_time=TIME_TO_WAIT).fill(
                fixtures_path.joinpath("ph_upload/rent_example.xlsx").as_posix()
            )
            admin_assert_alert_successful(browser=browser)

            # upload shitty file = error
            browser.find_by_id("ph_results_file_upload", wait_time=TIME_TO_WAIT).fill(
                fixtures_path.joinpath(
                    "ph_upload/sales_example_wrong_ids.xlsx"
                ).as_posix()
            )
            browser.find_by_id("notification-error", wait_time=TIME_TO_WAIT)

    def test_manual_surr_link(
        self, browser: BaseWebDriver, admin_url, site, navigate_to_sites_table
    ):
        num_sites = 1
        navigate_to_sites_table(site["client_id"], expected_sites=num_sites)
        with expand_screen_size(browser=browser):

            safe_wait_for_table_and_expand_columns(
                browser, "sites_table", expected_rows=num_sites
            )

            browser.find_by_text("Surroundings", wait_time=TIME_TO_WAIT).click()
            assert browser.url == f"{admin_url}/manual_surroundings/{site['id']}"
            browser.is_element_present_by_css(".editor-map", wait_time=TIME_TO_WAIT)

    def test_admin_sees_all_sites_and_fields_exclusive_for_admins(
        self,
        browser: BaseWebDriver,
        admin_url,
        site,
        client_db,
        navigate_to_sites_table,
    ):
        """
        Given 1 site with not group_id
        when admin user access sites in admin
        Then 1 site is present
        And Run analysis button is visible
        And group dropdown is visible
        """
        num_sites = 1
        navigate_to_sites_table(client_db["id"], expected_sites=num_sites)
        browser.visit(admin_url + "/clients")
        safe_wait_for_table_and_expand_columns(
            browser, "clients_table", expected_rows=1
        )
        navigate_to_child(browser, f"/sites?client_id={client_db['id']}")
        safe_wait_for_table_and_expand_columns(
            browser, "sites_table", expected_rows=num_sites
        )

        assert len(browser.find_by_xpath(XPATH_FEATURES_GENERATION_BUTTON)) == num_sites
        assert browser.is_element_present_by_xpath(XPATH_DROP_DOWN_GROUP, wait_time=1)

    def test_copy_site_link(
        self, browser: BaseWebDriver, admin_url, site, navigate_to_sites_table
    ):
        num_sites = 1
        navigate_to_sites_table(site["client_id"], expected_sites=num_sites)
        with expand_screen_size(browser=browser):

            safe_wait_for_table_and_expand_columns(
                browser, "sites_table", expected_rows=num_sites
            )

            # Click on the Copy site link
            browser.find_by_text("Copy site", wait_time=TIME_TO_WAIT).click()
            assert browser.url == f"{admin_url}/site/{site['id']}/copy"

            # Identify dropdown and click on it
            target_id_dropdown = browser.find_by_xpath(
                "//*[contains(@class, 'client_target_id')]",
                wait_time=TIME_TO_WAIT,
            ).first
            target_id_dropdown.click()

            # Select the first option
            first_option = browser.find_by_xpath(
                "//*[contains(@role, 'option')]",
                wait_time=TIME_TO_WAIT,
            ).first
            first_option.click()

            # Click on the Copy site button
            browser.find_by_css(".save-button", wait_time=TIME_TO_WAIT).first.click()

            # Match snackbar text to ascertain that the site is actually copied
            assert browser.find_by_text("Copied succesfully", wait_time=TIME_TO_WAIT)

    def test_classification_scheme_change(
        self, browser: BaseWebDriver, client_db, site, navigate_to_sites_table
    ):
        """A bit useless test as of now we only have one option
        and cant mock it as it is an enum in the DB too.
        But the test makes sure it is clickable and present
        """
        navigate_to_sites_table(client_db["id"], expected_sites=1)

        assert (
            SiteDBHandler.get_by(id=site["id"])["classification_scheme"]
            == CLASSIFICATIONS.UNIFIED.name
        )

        get_dropdown_for_site(
            browser=browser,
            site_id=site["id"],
            column_name="classification_scheme",
        ).click()

        browser.find_by_css(".MuiList-root").find_by_text(
            CLASSIFICATIONS.UNIFIED.name,
            wait_time=TIME_TO_WAIT,
        ).click()

        browser.reload()
        assert browser.find_by_xpath(
            f"//div[@role = 'button' and text() = '{CLASSIFICATIONS.UNIFIED.name}']"
        ).first

    def test_group_id_change(
        self,
        browser: BaseWebDriver,
        sites_groups,
        client_db,
        navigate_to_sites_table,
        upwork_group,
        oecc_group,
    ):

        with expand_screen_size(browser=browser):

            num_sites = 3
            navigate_to_sites_table(client_db["id"], expected_sites=num_sites)

            self.assert_group_names_correct_in_sites_table(
                browser=browser, num_sites=num_sites, client_id=client_db["id"]
            )

            # Find and click on group dropdown
            get_dropdown_for_site(
                browser=browser, site_id=sites_groups["no_group"]["id"]
            ).click()

            # Select OECC group
            browser.find_by_css(".MuiList-root").find_by_text(
                oecc_group["name"], wait_time=TIME_TO_WAIT
            ).click()

            self.assert_group_names_correct_in_sites_table(
                browser=browser, num_sites=num_sites, client_id=client_db["id"]
            )

            # Select NO group
            get_dropdown_for_site(
                browser=browser, site_id=sites_groups["no_group"]["id"]
            ).click()
            browser.find_by_css(".MuiList-root").find_by_text("-").click()
            self.assert_group_names_correct_in_sites_table(
                browser=browser, num_sites=num_sites, client_id=client_db["id"]
            )

    def assert_group_names_correct_in_sites_table(
        self, browser, num_sites, client_id: int
    ):
        browser.reload()
        safe_wait_for_table_and_expand_columns(
            browser=browser, table_name="sites_table", expected_rows=num_sites
        )
        group_names_by_id = {x["id"]: x["name"] for x in GroupDBHandler.find()}
        sites = SiteDBHandler.find(client_id=client_id)
        for i in range(len(sites)):
            site_id = int(_get_admin_column_content(browser, "id", row_number=i + 1))
            group = _get_admin_column_content(
                browser, "group", row_number=i + 1, as_text=False
            )

            site = [s for s in sites if s["id"] == site_id][0]
            # Check group_id is correct
            assert f'value="{site["group_id"] or ""}"' in group.outer_html
            # Check label is correct
            group_label = (
                group_names_by_id[site["group_id"]] if site["group_id"] else ""
            )
            assert group_label == group.text

    def test_admin_panel_site_simulation_status(
        self, make_sites, client_db, admin_url, browser
    ):
        sites = [
            make_sites(client_db, full_slam_results=status)[0]
            for status in ADMIN_SIM_STATUS
        ]
        sites = {s["id"]: s for s in sites}

        browser.visit(admin_url + f"/sites?client_id={client_db['id']}")

        safe_wait_for_table_and_expand_columns(
            browser, "sites_table", expected_rows=len(ADMIN_SIM_STATUS)
        )

        for row in range(1, len(sites) + 1):
            status = _get_admin_column_content(
                browser=browser,
                column_name="full_slam_results",
                row_number=row,
                as_text=False,
            )
            site_id = int(
                _get_admin_column_content(
                    browser=browser, column_name="id", row_number=row
                )
            )
            site_status = sites[site_id]["full_slam_results"]
            assert status.text == site_status

            heatmaps = _get_admin_column_content(
                browser=browser,
                column_name="simulations",
                row_number=row,
                as_text=False,
            )

            if site_status == ADMIN_SIM_STATUS.SUCCESS.value:
                assert "color: green" in status.outer_html
                assert "<a" in heatmaps.outer_html
            else:
                assert "color: black" in status.outer_html
                assert "<p" in heatmaps.outer_html

    @pytest.mark.parametrize(
        ["button", "expected_tasks"],
        [
            (
                "Force Simulation Status to success",
                {"tasks.workflow_tasks.slam_results_success": 1},
            ),
            ("Generate IFC", {"tasks.deliverables_tasks.generate_ifc_file_task": 1}),
            (
                "Generate Benchmark Charts",
                {"tasks.deliverables_tasks.generate_unit_plots_task": 1},
            ),
            (
                "Generate EBF Summary",
                {"tasks.deliverables_tasks.generate_energy_reference_area_task": 1},
            ),
            (
                "Generate Vector Files",
                {"tasks.deliverables_tasks.generate_vector_files_task": 1},
            ),
            (
                "Generate All Deliverables",
                {
                    "tasks.deliverables_tasks.generate_ifc_file_task": 1,
                    "tasks.deliverables_tasks.generate_energy_reference_area_task": 1,
                    "tasks.deliverables_tasks.generate_pngs_and_pdfs_for_floor_task": 1,
                    "tasks.deliverables_tasks.generate_unit_pngs_and_pdfs": 1,
                },
            ),
        ],
    )
    def test_admin_panel_site_run_jobs(
        self,
        site,
        building,
        floor,
        unit,
        qa_db,
        admin_url,
        browser,
        button,
        expected_tasks,
    ):
        """
        Given an existing client and site
        when editing a site
        when triggering a job
        then the job should be started
        """

        browser.visit(admin_url + f"/site/{site['id']}")
        browser.find_by_text("Jobs").first.click()
        navigation_started_time = datetime.now()

        browser.find_by_xpath(f"//button[span[text()='{button}']]").first.click()
        wait_for_celery_tasks(num_tasks_expected=sum(expected_tasks.values()))
        confirm_no_tasks_unfinished()

        tasks_metadata = get_flower_all_tasks_metadata(
            after_time=navigation_started_time.timestamp()
        )
        assert Counter({task["name"] for task in tasks_metadata}) == expected_tasks


class TestAsTeamLeader:
    def test_admin_only_functionalities_not_visible(
        self,
        browser: BaseWebDriver,
        admin_url,
        client_db,
        site,
    ):
        """
        Tests that a teamleader does not have access to:
        - ZIP delivery download
        - Reassigning groups
        """
        login = make_login(browser=browser, admin_url=admin_url, user_type="TEAMLEADER")
        SiteDBHandler.update(
            item_pks={"id": site["id"]},
            new_values={
                "full_slam_results": ADMIN_SIM_STATUS.SUCCESS,
                "group_id": login["group_id"],
            },
        )

        browser.visit(admin_url + f"/sites?client_id={client_db['id']}")
        safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=1)
        assert browser.find_by_text("Zip").is_empty()
        assert browser.find_by_text("Group").is_empty()


@pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER])
def test_admin_panel_start_feature_generation(
    client_db, site, admin_url, browser, plan_box_pipelined, plan, unit, user_role
):
    """
    Given an existing client
    And an empty GCP bucket
    And a client with all the pricing options but the PDF to False
    And a populated site in the database
    When a feature generation for that site is triggered by pressing button
    Then 6 celery task has been triggered of the chain and site is set to failure as some tasks will fail
    """
    login = make_login(browser=browser, admin_url=admin_url, user_type=user_role.name)

    from tasks import workflow_tasks

    ClientDBHandler.update(
        item_pks={"id": client_db["id"]},
        new_values={
            "option_dxf": False,
            "option_pdf": True,
            "option_analysis": False,
        },
    )
    UnitDBHandler.update(item_pks={"id": unit["id"]}, new_values={"client_id": "1"})
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"pipeline_and_qa_complete": True, "group_id": login["group_id"]},
    )

    navigation_started_time = datetime.now()
    browser.visit(admin_url + f"/sites?client_id={client_db['id']}")
    safe_wait_for_table_and_expand_columns(browser, "sites_table", expected_rows=1)

    browser.find_by_xpath(
        XPATH_FEATURES_GENERATION_BUTTON, wait_time=TIME_TO_WAIT
    ).first.click()

    text_message = (
        f"Successfully started running analysis for site with id [{site['id']}]"
    )
    assert (
        len(
            browser.find_by_xpath(
                f"//div[contains(text(), '{text_message}')]", wait_time=TIME_TO_WAIT
            )
        )
        == 1
    )

    num_tasks_expected = 7
    # run_digitize_analyze_client_tasks, the basic features ones (2),
    # update_site_location, run_buildings_elevation_task + celery chord

    wait_for_celery_tasks(wait_for_subtasks=True)

    tasks_metadata = get_flower_all_tasks_metadata(
        after_time=navigation_started_time.timestamp()
    )
    assert len(tasks_metadata) == num_tasks_expected, [
        task["name"] for task in tasks_metadata
    ]

    task_dict = {task["name"]: task for task in tasks_metadata}
    assert workflow_tasks.run_digitize_analyze_client_tasks.name in task_dict
    task_info = task_dict[workflow_tasks.run_digitize_analyze_client_tasks.name]

    assert task_info["received"] > navigation_started_time.timestamp()
    assert task_info["state"] == SUCCESS, task_info

    assert (
        SiteDBHandler.get_by(id=site["id"])["full_slam_results"]
        == ADMIN_SIM_STATUS.FAILURE.value
    )
