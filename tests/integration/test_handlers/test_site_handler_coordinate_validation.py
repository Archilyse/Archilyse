import pytest
from deepdiff import DeepDiff

from common_utils.constants import REGION
from common_utils.exceptions import DBValidationException
from handlers import SiteHandler
from handlers.db import SiteDBHandler


def test_add_site_using_coordinates_outside_switzerland_not_trigger_footprints_task(
    client_db,
    qa_without_site,
    monkeypatch,
    site_coordinates_outside_switzerland,
    mocked_generate_geo_referencing_surroundings_for_site_task,
    mocked_geolocator_outside_ch,
):
    site = SiteHandler.add(
        client_id=client_db["id"],
        name="Big-ass portfolio",
        region="Switzerland",
        client_site_id="blah",
        qa_id=qa_without_site["id"],
        **site_coordinates_outside_switzerland,
    )
    assert REGION[site["georef_region"]] == REGION.CZ
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 0


def test_add_site_using_coordinates_inside_switzerland(
    qa_without_site,
    client_db,
    site_coordinates,
    mocked_generate_geo_referencing_surroundings_for_site_task,
    mocked_geolocator,
    site_region_proj_ch,
):
    site_added = SiteHandler.add(
        client_id=client_db["id"],
        name="Big-ass portfolio",
        region="Switzerland",
        client_site_id="blah",
        qa_id=qa_without_site["id"],
        **site_region_proj_ch,
        **site_coordinates,
    )

    site_added = SiteDBHandler.get_by(id=site_added["id"])

    assert REGION[site_added["georef_region"]] == REGION.CH

    assert site_added["client_id"] == client_db["id"]
    assert site_added["client_site_id"] == "blah"
    assert site_added["group_id"] is None
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 1


def test_add_site_with_incomplete_coordinates(mocked_geolocator, qa_without_site):
    with pytest.raises(DBValidationException):
        SiteHandler.add(
            client_id=1,
            client_site_id="Leszku-payaso",
            name="Big-ass portfolio",
            region="Switzerland",
            lon=0,
            qa_id=qa_without_site["id"],
        )


def test_add_site_without_coordinates(mocked_geolocator, qa_without_site):
    with pytest.raises(DBValidationException):
        SiteHandler.add(
            client_id=1,
            client_site_id="Leszku-payaso",
            name="Big-ass portfolio",
            region="Switzerland",
            qa_id=qa_without_site["id"],
        )


def test_update_site_using_coordinates_outside_switzerland(
    site_for_coordinate_validation,
    site_coordinates_outside_switzerland,
    mocked_generate_geo_referencing_surroundings_for_site_task,
    mocked_geolocator_outside_ch,
):

    site_updated = SiteHandler.update(
        site_id=site_for_coordinate_validation["id"],
        **site_coordinates_outside_switzerland,
    )
    assert REGION[site_updated["georef_region"]] == REGION.CZ
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 0


def test_update_site_using_coordinates_inside_switzerland(
    site_for_coordinate_validation,
    mocked_generate_geo_referencing_surroundings_for_site_task,
    mocked_geolocator,
    qa_db,
):
    new_coordinates = {
        "lat": site_for_coordinate_validation["lat"] + 0.1,
        "lon": site_for_coordinate_validation["lon"] + 0.1,
    }

    site_updated = SiteHandler.update(
        site_id=site_for_coordinate_validation["id"], **new_coordinates
    )
    assert REGION[site_updated["georef_region"]] == REGION.CH

    assert not DeepDiff(
        new_coordinates,
        {k: site_updated[k] for k in ("lat", "lon")},
        significant_digits=10,
    )
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 1


def test_update_site_same_coordinates_does_not_trigger_task(
    site_for_coordinate_validation,
    mocked_generate_geo_referencing_surroundings_for_site_task,
    mocked_geolocator,
):
    new_coordinates = {
        "lat": site_for_coordinate_validation["lat"],
        "lon": site_for_coordinate_validation["lon"],
    }

    site_updated = SiteHandler.update(
        site_id=site_for_coordinate_validation["id"], **new_coordinates
    )
    assert REGION[site_updated["georef_region"]] == REGION.CH
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 0
