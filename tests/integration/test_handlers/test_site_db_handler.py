import pytest

from brooks.util.projections import REGIONS_CRS
from common_utils.constants import CURRENCY, REGION
from common_utils.exceptions import DBException, DBValidationException
from handlers.db import PlanDBHandler, SiteDBHandler


def test_get_sites_with_ready_field_no_plans(site):
    handler_site = SiteDBHandler.get_sites_with_ready_field(
        client_id=site["client_id"]
    )[0]
    assert handler_site.pop("ready") is False
    assert handler_site == site


def test_get_sites_with_ready_field_plan_no_annotations(site, plan):
    handler_site = SiteDBHandler.get_sites_with_ready_field(
        client_id=site["client_id"]
    )[0]
    assert handler_site.pop("ready") is False
    assert handler_site == site


def test_get_sites_with_client_site_id(client_db, site, make_sites):
    site["ready"] = False
    client_site_id_test = "c_s_id"

    # We create the site manually so the 'client_site_id' is not null
    SiteDBHandler.update({"id": site["id"]}, {"client_site_id": client_site_id_test})
    make_sites(client_db)

    sites_result = SiteDBHandler.get_sites_with_ready_field(
        client_id=site["client_id"], client_site_id=client_site_id_test
    )

    assert len(sites_result) == 1, "Only one site filtered"
    assert (
        sites_result[0]["client_site_id"] == client_site_id_test
    ), "Client site id fits with the filtered site"


def test_get_sites_with_ready_field_plan_annotations(site, plan, make_annotations):
    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]), new_values=dict(annotation_finished=True)
    )

    handler_site = SiteDBHandler.get_sites_with_ready_field(
        client_id=site["client_id"]
    )[0]
    assert handler_site.pop("ready") is True
    assert handler_site == site


def test_add_site_with_string_coordinates_containing_invalid_chars(client_db):
    with pytest.raises(DBValidationException):
        SiteDBHandler.add(
            client_id=client_db["id"],
            client_site_id="foobar",
            lat="12'333.0",
            lon="12'333.0",
            name="Some portfolio",
            region="Switzerland",
        )


def test_update_site_with_string_coordinates_containing_invalid_chars(site):
    with pytest.raises(DBValidationException):
        SiteDBHandler.update(
            item_pks=dict(id=site["id"]),
            new_values=dict(lat="12'333.0", lon="12'333.0"),
        )


def test_site_unique_constraints_raised(
    site,
    site_coordinates,
    site_region_proj_ch,
):
    with pytest.raises(
        DBException, match="duplicate key value violates unique constraint"
    ):
        SiteDBHandler.add(
            client_id=site["client_id"],
            client_site_id=site["client_site_id"],
            name="has to fail",
            region="Noland",
            **site_region_proj_ch,
            **site_coordinates,
        )


def test_site_unique_constraints_raised_when_update(
    site, site_coordinates, site_region_proj_ch
):

    new_site = SiteDBHandler.add(
        client_id=site["client_id"],
        client_site_id="some site",
        name="has to fail",
        region="Noland",
        **site_region_proj_ch,
        **site_coordinates,
    )
    with pytest.raises(
        DBException, match="duplicate key value violates unique constraint"
    ):
        SiteDBHandler.update(
            item_pks={"id": new_site["id"]},
            new_values={"client_site_id": site["client_site_id"]},
        )


def test_site_georef_proj_correct_outside_ch(
    client_db, site_coordinates_outside_switzerland
):
    new_site = SiteDBHandler.add(
        client_id=client_db["id"],
        client_site_id="some site",
        name="has to fail",
        region="Noland",
        georef_region=REGION.CZ.name,
        **site_coordinates_outside_switzerland,
    )
    assert new_site["georef_proj"] == REGIONS_CRS[REGION.CZ].to_string()


@pytest.mark.parametrize(
    "region, currency_expected",
    [
        (REGION.CH, CURRENCY.CHF),
        (REGION.AT, CURRENCY.EUR),
        (REGION.US_GEORGIA, CURRENCY.USD),
        (REGION.DE_HAMBURG, CURRENCY.EUR),
        (REGION.CZ, CURRENCY.CZK),
    ],
)
def test_site_currency(
    client_db, site_coordinates_outside_switzerland, region, currency_expected
):
    new_site = SiteDBHandler.add(
        client_id=client_db["id"],
        client_site_id="client_id",
        name="foo",
        region="bar",
        georef_region=region.name,
        **site_coordinates_outside_switzerland,
    )
    assert (
        SiteDBHandler.get_by(id=new_site["id"])["currency"] == currency_expected.value
    )
