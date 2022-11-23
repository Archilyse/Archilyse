import functools
from typing import Dict, Tuple

from flask import request
from sqlalchemy import or_

from common_utils.constants import DMS_PERMISSION, USER_ROLE
from common_utils.exceptions import UserAuthorizationException
from connectors.db_connector import BaseDBModel
from db_models import BuildingDBModel, FloorDBModel, SiteDBModel, UnitDBModel
from db_models.db_entities import FileDBModel, FolderDBModel
from handlers.db import BuildingDBHandler
from slam_api.utils import get_user_authorized


def foreign_key_filter(db_model: BaseDBModel, allow_none: bool = True):
    def _filter(permissions: Dict[int, DMS_PERMISSION]):
        sql_filter = db_model.site_id.in_(permissions.keys())
        if allow_none:
            sql_filter = (
                or_(
                    sql_filter,
                    db_model.site_id.is_(None),
                ),
            )
        return sql_filter

    return _filter


def site_filter(permissions: Dict[int, DMS_PERMISSION]) -> Tuple:
    return (SiteDBModel.id.in_(permissions.keys()),)


def floor_filter(permissions: Dict[int, DMS_PERMISSION]) -> Tuple:
    building_ids = BuildingDBHandler.find_in(
        site_id=[site_id for site_id in permissions.keys()],
        output_columns=["id"],
    )
    return (
        FloorDBModel.building_id.in_(building_id["id"] for building_id in building_ids),
    )


dms_sql_filters = {
    SiteDBModel: site_filter,
    BuildingDBModel: foreign_key_filter(db_model=BuildingDBModel, allow_none=False),
    FloorDBModel: floor_filter,
    UnitDBModel: foreign_key_filter(db_model=UnitDBModel, allow_none=False),
    FolderDBModel: foreign_key_filter(db_model=FolderDBModel, allow_none=True),
    FileDBModel: foreign_key_filter(db_model=FileDBModel, allow_none=True),
}


def document_collection_post_validator(exception_message: str):
    def _validator(requesting_user: Dict, **kwargs):
        if site_id := kwargs.get("site_id"):
            from handlers import DmsPermissionHandler

            if not DmsPermissionHandler.has_write_permission(
                user=requesting_user, site_id=site_id
            ):
                raise UserAuthorizationException(exception_message)
        else:
            raise UserAuthorizationException(exception_message)

    return _validator


def dms_limited_collection_view(db_model: BaseDBModel):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            requesting_user = get_user_authorized()
            if USER_ROLE.DMS_LIMITED in requesting_user["roles"]:
                if request.method == "GET":
                    from handlers import DmsPermissionHandler

                    kwargs["dms_limited_sql_filter"] = dms_sql_filters[db_model](
                        permissions=DmsPermissionHandler.get_permissions_of_user_per_site(
                            user=requesting_user
                        )
                    )
                else:

                    document_collection_post_validator(
                        exception_message=(
                            "User is not allowed to create this folder"
                            if db_model == FolderDBModel
                            else "User is not allowed to create this file"
                        )
                    )(**kwargs, requesting_user=requesting_user)

            return function(*args, **kwargs)

        return wrapper

    return decorator
