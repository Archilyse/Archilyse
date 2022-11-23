import pytest

from common_utils.constants import DMS_PERMISSION
from common_utils.exceptions import UserAuthorizationException
from handlers import DmsPermissionHandler
from handlers.db import ClientDBHandler, DmsPermissionDBHandler


class TestDmsPermissionHandler:
    @pytest.mark.parametrize(
        "permission_type_all,expected_permission_type",
        [
            (DMS_PERMISSION.READ_ALL.name, DMS_PERMISSION.READ),
            (DMS_PERMISSION.WRITE_ALL.name, DMS_PERMISSION.WRITE),
        ],
    )
    def test_get_permissions_of_user_for_all_permission_types(
        self,
        client_db,
        make_sites,
        permission_type_all,
        expected_permission_type,
        make_users,
    ):
        (user1,) = make_users((client_db))
        other_client = ClientDBHandler.add(name="OtherClient")
        make_sites(*(other_client,))
        sites = make_sites(*(client_db, client_db, client_db))
        DmsPermissionDBHandler.add(user_id=user1["id"], rights=permission_type_all)
        permissions = DmsPermissionHandler.get_permissions_of_user_per_site(user=user1)
        assert len(permissions) == len(sites)

        for site in sites:
            assert permissions.get(site["id"]) == expected_permission_type

    def test_get_permissions_for_permissions_types_per_site(
        self, client_db, make_sites, make_users
    ):
        user1, user2 = make_users(*(client_db, client_db))
        other_client = ClientDBHandler.add(name="OtherClient")
        make_sites(*(other_client,))
        sites = make_sites(*(client_db, client_db, client_db))
        DmsPermissionDBHandler.add(
            user_id=user1["id"], site_id=sites[0]["id"], rights=DMS_PERMISSION.READ.name
        )
        DmsPermissionDBHandler.add(
            user_id=user1["id"],
            site_id=sites[1]["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )
        DmsPermissionDBHandler.add(
            user_id=user2["id"],
            site_id=sites[2]["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )

        permissions = DmsPermissionHandler.get_permissions_of_user_per_site(user=user1)
        assert len(permissions) == 2
        assert permissions.get(sites[0]["id"]) == DMS_PERMISSION.READ
        assert permissions.get(sites[1]["id"]) == DMS_PERMISSION.WRITE

    @pytest.mark.parametrize(
        "permission,expected",
        [(DMS_PERMISSION.READ, True), (DMS_PERMISSION.WRITE, True), (None, False)],
    )
    def test_has_read_permission(
        self, client_db, make_sites, permission, expected, make_users
    ):
        (user1,) = make_users((client_db))
        (site,) = make_sites(*(client_db,))
        if permission:
            DmsPermissionDBHandler.add(
                user_id=user1["id"], site_id=site["id"], rights=permission.name
            )

        assert (
            DmsPermissionHandler.has_read_permission(user=user1, site_id=site["id"])
            == expected
        )

    @pytest.mark.parametrize(
        "permission,expected",
        [(DMS_PERMISSION.READ, False), (DMS_PERMISSION.WRITE, True), (None, False)],
    )
    def test_has_write_permission(
        self, client_db, make_sites, permission, expected, make_users
    ):
        (user1,) = make_users((client_db))
        (site,) = make_sites(*(client_db,))
        if permission:
            DmsPermissionDBHandler.add(
                user_id=user1["id"], site_id=site["id"], rights=permission.name
            )

        assert (
            DmsPermissionHandler.has_write_permission(user=user1, site_id=site["id"])
            == expected
        )

    def test_get_all_permissions_of_client(self, client_db, site, make_users):
        other_client = ClientDBHandler.add(name="OtherClient")
        user1, user2, user_other_client = make_users(
            *(client_db, client_db, other_client)
        )

        DmsPermissionDBHandler.add(
            user_id=user1["id"], site_id=site["id"], rights=DMS_PERMISSION.READ.name
        )
        DmsPermissionDBHandler.add(
            user_id=user2["id"], rights=DMS_PERMISSION.WRITE_ALL.name
        )
        DmsPermissionDBHandler.add(
            user_id=user_other_client["id"], rights=DMS_PERMISSION.READ_ALL.name
        )

        permissions = DmsPermissionHandler.get_all_permissions_of_client(
            client_id=client_db["id"]
        )

        assert len(permissions) == 2
        assert {permission["rights"] for permission in permissions} == {
            DMS_PERMISSION.WRITE_ALL,
            DMS_PERMISSION.READ,
        }

    def test_put_permissions_successfull(self, site, client_db, make_users):
        user1, user2 = make_users(*(client_db, client_db))
        new_permissions = [
            {"site_id": site["id"], "rights": DMS_PERMISSION.WRITE.name},
        ]

        DmsPermissionHandler.put_permissions(
            user_id=user2["id"], data=new_permissions, requesting_user=user1
        )
        permissions = DmsPermissionDBHandler.find()
        assert len(permissions) == 1
        assert permissions[0]["rights"] == DMS_PERMISSION.WRITE
        assert permissions[0]["site_id"] == site["id"]
        assert permissions[0]["user_id"] == user2["id"]

        new_permissions = [
            {"rights": DMS_PERMISSION.READ_ALL.name},
        ]

        DmsPermissionHandler.put_permissions(
            user_id=user2["id"], data=new_permissions, requesting_user=user1
        )
        permissions = DmsPermissionDBHandler.find()
        assert len(permissions) == 1
        assert permissions[0]["rights"] == DMS_PERMISSION.READ_ALL
        assert permissions[0]["site_id"] is None
        assert permissions[0]["user_id"] == user2["id"]

    def test_put_permissions_other_client_forbidden(self, site, make_users):
        other_client = ClientDBHandler.add(name="OtherClient")
        (requesting_user,) = make_users((other_client))

        new_permissions = [
            {"site_id": site["id"], "rights": DMS_PERMISSION.WRITE.name},
        ]

        with pytest.raises(UserAuthorizationException) as e:
            DmsPermissionHandler.put_permissions(
                user_id=requesting_user["id"],
                data=new_permissions,
                requesting_user=requesting_user,
            )
        assert str(e.value) == "Access to this resource is forbidden."

    def test_put_permissions_user_from_other_client_forbidden(
        self, site, client_db, make_users
    ):

        other_client = ClientDBHandler.add(name="OtherClient")
        user1, other_user = make_users(*(client_db, other_client))

        new_permissions = [
            {"rights": DMS_PERMISSION.WRITE_ALL.name},
        ]

        with pytest.raises(UserAuthorizationException) as e:
            DmsPermissionHandler.put_permissions(
                user_id=other_user["id"],
                data=new_permissions,
                requesting_user=user1,
            )
        assert str(e.value) == "Access to this resource is forbidden."
