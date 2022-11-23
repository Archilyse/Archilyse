import functools
from typing import Dict

from flask import request

from common_utils.constants import USER_ROLE
from common_utils.exceptions import UserAuthorizationException
from connectors.db_connector import BaseDBModel
from handlers import DmsPermissionHandler
from handlers.db import PlanDBHandler
from slam_api.utils import (
    Entities,
    db_handler_with_primary_key_by_db_model,
    get_user_authorized,
)

LABELS_PUT_PARAM = "labels"


def entity_get_validator(
    db_model: BaseDBModel, requesting_user: Dict, request_method: str, **kwargs
):
    db_handler, primary_key_name = db_handler_with_primary_key_by_db_model.get(db_model)
    if primary_key_name in (
        "file_id",
        "folder_id",
    ):
        return entity_modify_validator(
            db_model=db_model, request_method=request_method
        )(requesting_user=requesting_user, **kwargs)

    entity_name, *_ = primary_key_name.split("_")
    if primary_key_name == "site_id":
        return site_get_validator(
            requesting_user=requesting_user,
            site_id=kwargs["site_id"],
            entity_name=entity_name,
        )

    if primary_key_name in ("floor_id", "area_id"):
        entity = db_handler.get_by(id=kwargs[primary_key_name])
        plan = PlanDBHandler.get_by(id=entity["plan_id"])
        return site_get_validator(
            requesting_user=requesting_user,
            site_id=plan["site_id"],
            entity_name=entity_name,
        )

    site_id = db_handler.get_by(id=kwargs[primary_key_name])["site_id"]
    return site_get_validator(
        requesting_user=requesting_user, site_id=site_id, entity_name=entity_name
    )


def site_get_validator(requesting_user: Dict, site_id: int, entity_name: str):

    if not DmsPermissionHandler.has_read_permission(
        user=requesting_user, site_id=site_id
    ):
        raise UserAuthorizationException(
            f"User is not allowed to access this {entity_name if entity_name != 'plan' else 'plan'}"
        )


def entity_modify_validator(db_model: BaseDBModel, request_method: str):
    """
    request_method: either "GET" or "POST". "POST" is also covering PUT & DELETE
    """
    db_handler, primary_key_name = db_handler_with_primary_key_by_db_model.get(db_model)
    entity_name, *_ = primary_key_name.split("_")
    exception_message = (
        f"User is not allowed to {'access' if request_method == 'GET' else 'edit'} "
        f"this {entity_name}"
    )

    def _validator(requesting_user: Dict, **kwargs):
        document = db_handler.get_by(id=kwargs[primary_key_name])
        if not document.get("site_id"):
            if request_method == "GET":
                """
                if no site_id is associated with the document its directly attached to the client and
                all users are per default allowed to GET it
                """
                return
            else:
                """
                If a document has no site associated with it, its directly attached to the client and
                dms limited users are not allowed to edit those documents
                """
                raise UserAuthorizationException(exception_message)
        else:
            site_id = document.get("site_id")
            if not (
                DmsPermissionHandler.has_write_permission(
                    user=requesting_user, site_id=site_id
                )
                if request_method in ("POST", "PUT", "DELETE")
                else DmsPermissionHandler.has_read_permission(
                    user=requesting_user, site_id=site_id
                )
            ):
                raise UserAuthorizationException(exception_message)

    return _validator


def allowed_to_add_labels(kwargs: Dict) -> bool:
    if request.method == "PUT":
        entity_pkeys = set(Entities.keys) | {"area_id"}
        payload_no_pkeys = kwargs.keys() - entity_pkeys
        if len(payload_no_pkeys) == 1 and LABELS_PUT_PARAM in payload_no_pkeys:
            return True
    return False


def dms_limited_entity_view(db_model: BaseDBModel):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            requesting_user = get_user_authorized()
            if USER_ROLE.DMS_LIMITED in requesting_user["roles"]:
                if (
                    request.method == "GET"
                    or request.method == "PUT"
                    and allowed_to_add_labels(kwargs)
                ):
                    entity_get_validator(
                        db_model=db_model,
                        requesting_user=requesting_user,
                        request_method=request.method,
                        **kwargs,
                    )
                else:
                    entity_modify_validator(db_model, request_method=request.method)(
                        **kwargs, requesting_user=requesting_user
                    )
            return function(*args, **kwargs)

        return wrapper

    return decorator
