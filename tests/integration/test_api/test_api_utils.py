import contextlib
from http import HTTPStatus

import flask
import pytest
from werkzeug.exceptions import HTTPException

from common_utils.constants import USER_ROLE
from common_utils.exceptions import UserAuthorizationException
from handlers.db import UserDBHandler
from slam_api.utils import Entities, get_entities_from_kwargs, verify_role_membership
from tests.constants import USERS
from tests.utils import login_with


def test_associations(client_db, site, building, floor, unit):
    hierarchy = [
        ("unit_id", unit["id"]),
        ("floor_id", floor["id"]),
        ("building_id", building["id"]),
        ("site_id", site["id"]),
        ("client_id", client_db["id"]),
    ]

    for i, element in enumerate(hierarchy):
        elem_id_by_type = {elem_type: None for elem_type in Entities.keys}
        elem_id_by_type.update(
            {elem[0]: elem[1] for j, elem in enumerate(hierarchy) if j >= i}
        )
        assert elem_id_by_type == get_entities_from_kwargs(**{element[0]: element[1]})


@pytest.mark.parametrize(
    "user_role,protected_role,resource_id",
    [
        (USER_ROLE.ADMIN, USER_ROLE.ADMIN, None),
        (USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMMEMBER, 666),
        (USER_ROLE.ADMIN, USER_ROLE.TEAMMEMBER, None),
        (USER_ROLE.ADMIN, USER_ROLE.TEAMMEMBER, 666),
    ],
)
def test_verify_role_memberships_should_allow_specified_roles(
    mocker, app, client, user_role, protected_role, resource_id
):
    user = login_with(client, USERS[user_role.name])["user"]
    from slam_api import utils

    mocker.patch.object(utils, "get_jwt_identity", return_value={"id": user["id"]})
    with app.test_request_context(method="POST"):
        verify_role_membership({protected_role}, resource_user_id=resource_id)
        assert flask.request.authorization == UserDBHandler.get_by(id=user["id"])


def test_verify_role_memberships_request_method_options(mocker, app, client):
    user = login_with(client, USERS[USER_ROLE.ADMIN.name])["user"]
    from slam_api import utils

    mocker.patch.object(utils, "get_jwt_identity", return_value={"id": user["id"]})
    with app.test_request_context(method="OPTIONS"):
        assert (
            verify_role_membership({USER_ROLE.ADMIN}, resource_user_id=user["id"])
            is None
        )
        assert flask.request.authorization is None


def test_verify_role_memberships_missing_jwt(mocker, app, client):
    from slam_api import utils

    # as per flask_jwt_extended docs, 'None' is returned if the JWT has not been supplied with the API call
    mocker.patch.object(utils, "get_jwt_identity", return_value=None)
    response_spy = mocker.spy(utils, "abort")
    with app.test_request_context(method="GET"):
        # silly workaround for serialization error of 'pytest_flask.plugin.JSONResponse' by the abort method
        with contextlib.suppress(HTTPException):
            verify_role_membership({USER_ROLE.ADMIN})
        response, status = response_spy.mock_calls[0][1]
        assert response.json == {"message": "User is not valid"}
        assert status == HTTPStatus.UNAUTHORIZED
        assert flask.request.authorization is None


def test_verify_role_memberships_mangled_jwt_entry(mocker, app, client):
    from slam_api import utils

    mocker.patch.object(utils, "get_jwt_identity", return_value={})
    response_spy = mocker.spy(utils, "abort")
    with app.test_request_context(method="GET"):
        # silly workaround for serialization error of 'pytest_flask.plugin.JSONResponse' by the abort method
        with contextlib.suppress(HTTPException):
            verify_role_membership({USER_ROLE.ADMIN})
        response, status = response_spy.mock_calls[0][1]
        assert response.json == {"message": "Illegal token state"}
        assert status == HTTPStatus.INTERNAL_SERVER_ERROR
        assert flask.request.authorization is None


def test_verify_role_memberships_user_with_invalid_role(mocker, app, client):
    user = login_with(client, USERS[USER_ROLE.TEAMMEMBER.name])["user"]
    from slam_api import utils

    mocker.patch.object(utils, "get_jwt_identity", return_value={"id": user["id"]})
    with app.test_request_context(method="GET"):
        with pytest.raises(UserAuthorizationException):
            verify_role_membership({USER_ROLE.ADMIN})
        assert flask.request.authorization is None
