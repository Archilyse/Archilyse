import pytest

from common_utils.exceptions import DBNotFoundException
from handlers.db import GroupDBHandler, UserDBHandler


def test_create_group():
    group = GroupDBHandler.add(name="Archilyse")
    db_group = GroupDBHandler.get_by(id=group["id"])
    assert db_group["name"] == "Archilyse"


def test_assign_site_to_group_and_delete_group(site, login):
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"group_id": login["group"]["id"]}
    )
    site = SiteDBHandler.get_by(id=site["id"])
    assert site["group_id"] == login["group"]["id"]

    GroupDBHandler.delete(item_pk={"id": login["group"]["id"]})

    with pytest.raises(DBNotFoundException):
        GroupDBHandler.get_by(id=login["group"]["id"])
    assert SiteDBHandler.get_by(id=site["id"])["group_id"] is None


def test_delete_group_also_delete_user(login):
    GroupDBHandler.delete(item_pk={"id": login["group"]["id"]})
    with pytest.raises(DBNotFoundException):
        UserDBHandler.get_by(id=login["user"]["id"])
