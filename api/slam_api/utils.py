import functools
import json
import mimetypes
from http import HTTPStatus
from itertools import dropwhile, takewhile
from typing import Dict, Iterator, Set, Union

from flask import abort, jsonify, request, stream_with_context
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from jwt import InvalidSignatureError
from werkzeug.exceptions import BadRequest

from common_utils.constants import TASK_READY_STATES, USER_ROLE
from common_utils.exceptions import (
    JWTSignatureExpiredException,
    UserAuthorizationException,
)
from common_utils.logger import logger
from db_models import BuildingDBModel, FloorDBModel, SiteDBModel, UnitDBModel
from db_models.db_entities import FileDBModel, FolderDBModel, PlanDBModel
from handlers.db import (
    BuildingDBHandler,
    ClientDBHandler,
    FileDBHandler,
    FloorDBHandler,
    FolderDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_site_id_from_any_level


class Entities:
    keys = ["unit_id", "floor_id", "building_id", "site_id", "client_id"]

    @classmethod
    def child_keys(cls, entity_key: str) -> Iterator[str]:
        return takewhile(lambda k: entity_key != k, cls.keys)


handler_by_entity_type = {
    Entities.keys[0]: UnitDBHandler,
    Entities.keys[1]: FloorDBHandler,
    Entities.keys[2]: BuildingDBHandler,
    Entities.keys[3]: SiteDBHandler,
    Entities.keys[4]: ClientDBHandler,
}

db_handler_with_primary_key_by_db_model = {
    SiteDBModel: (SiteDBHandler, "site_id"),
    BuildingDBModel: (BuildingDBHandler, "building_id"),
    FloorDBModel: (FloorDBHandler, "floor_id"),
    PlanDBModel: (PlanDBHandler, "plan_id"),
    UnitDBModel: (UnitDBHandler, "unit_id"),
    FileDBModel: (FileDBHandler, "file_id"),
    FolderDBModel: (FolderDBHandler, "folder_id"),
}


def group_id_loader(func):
    """Adds the group id from the request authorization user"""

    @functools.wraps(func)
    def wrap(*args, **kwargs):
        current_user = get_user_authorized()

        group_id = (
            current_user["group_id"]
            if USER_ROLE.ADMIN not in current_user["roles"]
            else None
        )
        return func(*args, **kwargs, group_id=group_id)

    return wrap


def client_id_loader(func):
    @functools.wraps(func)
    def wrap(*args, **kwargs):
        user = get_user_authorized()
        if client_id := user["client_id"]:
            return func(*args, **kwargs, client_id=client_id)
        raise UserAuthorizationException(
            "The current user is not associated with any client. "
            "Please login with an appropriate user."
        )

    return wrap


class ensure_site_consistency:
    """
    Flask decorator that checks site status consistency
    """

    @staticmethod
    def handle_put_method() -> bool:
        if request.method == "PUT" and isinstance(request.get_json(), dict):
            # Some put methods shouldn't affect the status of the site, this is a hack to control that
            if not {"labels"}.symmetric_difference(
                set(request.get_json().keys())
            ) or not {
                "type"
            }.symmetric_difference(  # for manual surroundings
                set(request.get_json().keys())
            ):
                return True
        return False

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get params from url as 1st option
            site_id = get_site_id_from_any_level(kwargs)
            if not site_id:
                if request.content_type.startswith(mimetypes.types_map[".json"]):
                    # Get params from JSON payload
                    site_id = get_site_id_from_any_level(request.get_json())
                elif request.content_type.startswith("multipart/form-data"):
                    # Get params from form
                    site_id = get_site_id_from_any_level(request.form.to_dict())
                else:
                    logger.error("Request with unknown content-type")

            if site_id:
                # TODO: while we develop a better solution to control pipeline actions vs DMS actions
                if self.handle_put_method():
                    return func(*args, **kwargs)

                from handlers.db import SiteDBHandler

                site = SiteDBHandler.get_by(id=site_id)
                if (
                    site["full_slam_results"] not in TASK_READY_STATES
                    or site["basic_features_status"] not in TASK_READY_STATES
                ):
                    return (
                        jsonify(
                            {
                                "msg": "Can't make changes to the pipeline while simulation tasks are running."
                            }
                        ),
                        HTTPStatus.BAD_REQUEST,
                    )
                SiteDBHandler.set_site_to_unprocessed(site_id=site_id)
                return func(*args, **kwargs)
            else:
                return (
                    jsonify(
                        {
                            "msg": "This decorator can not be used in views without "
                            "plan_id, floor_id or site_id as kwarg"
                        }
                    ),
                    400,
                )

        return wrapper


def role_access_control(roles: Set[USER_ROLE], allow_user_id_field=None):
    """
    Decorator controlling access to view functions. Can be used in conjunction with
    multiple other access_control decorators that verify different roles. If roles are
    all the same for a given view controller,
    `verify_role_membership` can be used instead in a `before_request` context.

    If allow_user_id_field is set, it will only be checked whether the logged in user
    matches the user id in this method argument.
    """
    if not roles:
        raise ValueError(
            "Cannot control resource access without providing protected user roles."
        )

    def wrapper(func):
        func.__access_control__ = True

        @functools.wraps(func)
        def wrap(*args, **kwargs):
            authenticate_request(
                roles=roles, resource_user_id=kwargs.get(allow_user_id_field)
            )
            return func(*args, **kwargs)

        return wrap

    return wrapper


def authenticate_request(roles: Set[USER_ROLE], resource_user_id=None):
    if not roles:
        raise ValueError(
            "Cannot control resource access without providing protected user roles."
        )
    try:
        verify_jwt_in_request()
    except InvalidSignatureError as e:
        # the FE applications are not handling changes of signature
        # required when the internal structure of the tokens change, by returning an access
        # forbidden code the FE applications redirect the user to the login page, forcing the
        # token recreation
        raise JWTSignatureExpiredException(f"Access forbidden: {e}")
    verify_role_membership(roles=roles, resource_user_id=resource_user_id)


def verify_role_membership(roles: Set[USER_ROLE], resource_user_id=None):
    """
    Function controlling access to view functions. Can be used in a `before_request`
    decorated context, if a certain role is applicable to all RESTful resources within
    that view function.

    If resource_user_id is set, it will only be checked whether the logged in user
    matches this user id.
    """
    from handlers.db import UserDBHandler

    assert roles

    if request.method == "OPTIONS":
        return

    jwt_identity = get_jwt_identity()
    if jwt_identity is None:
        abort(jsonify({"message": "User is not valid"}), HTTPStatus.UNAUTHORIZED)

    try:
        user_id: int = jwt_identity["id"]
    except KeyError:
        abort(
            jsonify({"message": "Illegal token state"}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    if user_id == resource_user_id:
        user = UserDBHandler.get_by(id=user_id)
    else:
        user = UserDBHandler.get_user_roles_verified(
            user_id=user_id, required_roles=roles
        )

    if not user:
        raise UserAuthorizationException("Access to this resource is forbidden.")

    # NOTE: setting the property of the request is the standard form of
    # authentication in flask, many libraries will expect this to be completed
    # and also we could use this to store the user data within the call minimizing
    # DB requests. But not exactly with a dictionary containing our serialized user but with
    # a Authorization instance of werkzeug
    request.authorization = user  # type: ignore


def ensure_parent_entities():
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):

            entities = get_entities(**kwargs)

            if not entities.get("client_id"):
                raise BadRequest(description="No parent entities provided")

            for key in Entities.keys:
                kwargs[key] = entities.get(key)

            return function(*args, **kwargs)

        return wrapper

    return decorator


def get_entities(**kwargs) -> Dict[str, int]:

    from handlers.db import FolderDBHandler

    if parent_folder_id := parent_folder_provided(**kwargs):
        return {
            key: value
            for key, value in FolderDBHandler.get_by(id=parent_folder_id).items()
            if key in Entities.keys
        }

    return get_entities_from_kwargs(**kwargs)


def parent_folder_provided(**kwargs) -> Union[str, None]:
    """
    parent_folder_id is the key for a file's parent folder
    folder_id is the key for a folder's parent folder
    """
    return kwargs.get("parent_folder_id") or kwargs.get("folder_id")


def get_entities_from_kwargs(**kwargs) -> Dict[str, int]:
    """
    returns for example {"building_id": 120, "site_id": 3, "client_id": 1}
    """
    db_entity_id_by_type = {key: kwargs.get(key, None) for key in Entities.keys}

    hierarchy_iter = dropwhile(
        lambda x: not db_entity_id_by_type[x[0]],
        handler_by_entity_type.items(),
    )

    current_item = next(hierarchy_iter, None)
    if not current_item:
        return {}

    association_chain = {current_item[0]: kwargs[current_item[0]]}
    association_chain = get_association_chain(
        current_db_entity=current_item[1].get_by(id=kwargs[current_item[0]]),
        entity_hierarchy=hierarchy_iter,
        association_chain=association_chain,
    )
    db_entity_id_by_type.update(association_chain)
    return db_entity_id_by_type


def get_association_chain(
    current_db_entity, entity_hierarchy: Iterator, association_chain: Dict
) -> Dict[str, int]:
    """
    e.g. current_db_entity unit from db

    the function returns all parent entities of this entity e.g. {"floor_id": 4326, "building_id": 200, "site_id": 10, "client_id": 1}
    """
    next_hierarchy_entity = next(entity_hierarchy, None)
    if next_hierarchy_entity:
        next_element_field, next_element_handler = next_hierarchy_entity
        db_id = current_db_entity[next_element_field]
        next_element = next_element_handler.get_by(id=db_id)
        association_chain[next_element_field] = next_element["id"]
        return get_association_chain(next_element, entity_hierarchy, association_chain)
    return association_chain


def eventstream(iterator: Iterator[Dict]):
    from slam_api.app import app

    def _generator():
        for event in iterator:
            yield f"data: {json.dumps(event)}\n\n"

        yield "data: close\n\n"

    return app.response_class(
        stream_with_context(_generator()), mimetype="text/event-stream"
    )


def get_user_authorized() -> Dict:
    if user_authorized := request.authorization:  # type: ignore
        return dict(user_authorized)
    raise UserAuthorizationException("Access to this resource is forbidden.")
