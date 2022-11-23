from time import sleep

import pytest
from deepdiff import DeepDiff

from handlers.db import ManualSurroundingsDBHandler
from tests.constants import TIME_TO_WAIT
from tests.e2e_browser.utils_admin import make_login


@pytest.fixture(autouse=True)
def do_login(browser, admin_url):
    make_login(browser, admin_url)


def test_manual_surrounding_load(browser, admin_url, site):
    browser.visit(admin_url + f"/manual_surroundings/{site['id']}")
    assert browser.is_element_present_by_css(".editor-map", wait_time=TIME_TO_WAIT)


def test_manual_surrounding_save(
    browser, admin_url, site, manually_created_surroundings
):
    manual_surroundings = ManualSurroundingsDBHandler.add(
        site_id=site["id"], surroundings=manually_created_surroundings
    )
    browser.visit(admin_url + f"/manual_surroundings/{site['id']}")
    assert browser.is_element_present_by_css(".editor-map", wait_time=TIME_TO_WAIT)

    # We delete manual surroundings from db
    ManualSurroundingsDBHandler.delete(item_pk={"site_id": site["id"]})
    assert len(ManualSurroundingsDBHandler.find(site_id=site["id"])) == 0

    # We save manually created surroundings to db again
    browser.find_by_css(".leaflet-pm-icon-save").click()
    # Make sure it has time to save
    sleep(0.5)
    # We check that the surroundings are saved
    assert not DeepDiff(
        ManualSurroundingsDBHandler.get_by(site_id=site["id"])["surroundings"],
        manual_surroundings["surroundings"],
        significant_digits=5,
    )
