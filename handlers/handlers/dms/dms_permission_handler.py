from typing import Dict, List

from common_utils.constants import DMS_PERMISSION
from common_utils.exceptions import UserAuthorizationException
from connectors.db_connector import get_db_session_scope
from handlers.db import DmsPermissionDBHandler, SiteDBHandler, UserDBHandler
from handlers.db.utils import retry_on_db_operational_error


class DmsPermissionHandler:
    @classmethod
    @retry_on_db_operational_error()
    def put_permissions(
        cls, user_id: int, data: List[dict], requesting_user: dict
    ) -> None:
        if not UserDBHandler.exists(
            id=user_id, client_id=requesting_user["client_id"]
        ) or any(
            requesting_user["client_id"] != site["client_id"]
            for site in SiteDBHandler.find_in(
                id=[
                    permission["site_id"]
                    for permission in data
                    if permission.get("site_id")
                ],
                output_columns=["client_id"],
            )
        ):
            raise UserAuthorizationException("Access to this resource is forbidden.")

        with get_db_session_scope():
            DmsPermissionDBHandler.delete_in(user_id=[user_id])
            DmsPermissionDBHandler.bulk_insert(
                items=[
                    {
                        "user_id": user_id,
                        "site_id": permission.get("site_id"),
                        "rights": permission["rights"],
                    }
                    for permission in data
                ]
            )

    @classmethod
    def has_read_permission(cls, user: dict, site_id: int) -> bool:
        return site_id in cls.get_permissions_of_user_per_site(user=user)

    @classmethod
    def has_write_permission(cls, user: dict, site_id: int) -> bool:
        return (
            cls.get_permissions_of_user_per_site(user=user).get(site_id)
            == DMS_PERMISSION.WRITE
        )

    @classmethod
    def get_all_permissions_of_client(cls, client_id: int) -> List[Dict]:
        """
        returns permissions as stored in db. this means it also returns
        site unspecific read_all / write_all permissions
        """

        return [
            permission
            for user in UserDBHandler.find(
                output_columns=["id", "client_id"], client_id=client_id
            )
            for permission in DmsPermissionDBHandler.find(
                output_columns=["user_id", "site_id", "rights"], user_id=user["id"]
            )
        ]

    @classmethod
    def get_permissions_of_user_per_site(cls, user: dict) -> Dict[int, DMS_PERMISSION]:
        """
        e.g. {1:"READ", 5:"WRITE"}

        - Remark: if a user has READ_ALL we assume he has no write permissions for any of the sites.
        """
        permissions = DmsPermissionDBHandler.find(
            user_id=user["id"],
        )
        permission_types = {permission["rights"] for permission in permissions}
        if DMS_PERMISSION.READ_ALL in permission_types:
            return {
                site["id"]: DMS_PERMISSION.READ
                for site in SiteDBHandler.find(
                    output_columns=["id"], client_id=user["client_id"]
                )
            }

        elif DMS_PERMISSION.WRITE_ALL in permission_types:
            return {
                site["id"]: DMS_PERMISSION.WRITE
                for site in SiteDBHandler.find(
                    output_columns=["id"], client_id=user["client_id"]
                )
            }

        else:
            return {
                permission["site_id"]: permission["rights"]
                for permission in permissions
            }
