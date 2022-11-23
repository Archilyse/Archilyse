from slam_api.entity_ownership_validation import (
    validate_plan_ownership,
    validate_site_ownership,
)


def test_validate_site_ownership(site):
    assert validate_site_ownership(
        user={"client_id": site["client_id"]}, **{"id": site["id"]}
    )


def test_validate_site_ownership_returns_false(site):
    assert not validate_site_ownership(
        user={"client_id": site["client_id"] + 1}, **{"id": site["id"]}
    )


def test_validate_plan_ownership(site, plan):
    assert validate_plan_ownership(
        user={"client_id": site["client_id"]}, **{"id": plan["id"]}
    )


def test_validate_plan_ownership_returns_false(site, plan):
    assert not validate_plan_ownership(
        user={"client_id": site["client_id"] + 1}, **{"id": site["id"]}
    )
