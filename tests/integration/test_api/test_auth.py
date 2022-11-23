from http import HTTPStatus

import pytest
from flask import Flask

from common_utils.constants import USER_ROLE
from handlers.db import UserDBHandler
from slam_api.apis.login import Login, login_app
from tests.constants import USERS
from tests.db_fixtures import create_user_context, login_as, login_with
from tests.flask_utils import (
    blueprint_with_before_request,
    blueprint_with_decorator,
    configure_auth_server,
    get_address_for,
    make_request,
)


@pytest.mark.parametrize(
    "user,protected_roles,expected_status_code",
    [
        (USERS["TEAMMEMBER"], {USER_ROLE.ADMIN}, HTTPStatus.FORBIDDEN),
        (USERS["ADMIN"], {USER_ROLE.TEAMMEMBER}, HTTPStatus.OK),
        (USERS["TEAMMEMBER"], {USER_ROLE.TEAMMEMBER}, HTTPStatus.OK),
        (USERS["ARCHILYSE_ONE_ADMIN"], {USER_ROLE.TEAMMEMBER}, HTTPStatus.FORBIDDEN),
        (USERS["ARCHILYSE_ONE_ADMIN"], {USER_ROLE.ARCHILYSE_ONE_ADMIN}, HTTPStatus.OK),
    ],
)
def test_access_control_view_function(user, protected_roles, expected_status_code):

    test_app = Flask(__name__)
    test_blueprint, test_method = blueprint_with_decorator(roles=protected_roles)
    configure_auth_server(flask_app=test_app, blueprint=test_blueprint)
    client = test_app.test_client()

    login_with(client, user)

    _ = client.post(
        get_address_for(
            view_function=test_method, blueprint=test_blueprint, flask_app=test_app
        )
    )

    response = client.get(
        get_address_for(
            view_function=test_method, blueprint=test_blueprint, flask_app=test_app
        )
    )
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    "user,protected_roles,expected_status_code",
    [
        (USERS["TEAMMEMBER"], {USER_ROLE.ADMIN}, HTTPStatus.FORBIDDEN),
        (USERS["ADMIN"], {USER_ROLE.TEAMMEMBER}, HTTPStatus.OK),
        (USERS["TEAMMEMBER"], {USER_ROLE.TEAMMEMBER}, HTTPStatus.OK),
        (USERS["ARCHILYSE_ONE_ADMIN"], {USER_ROLE.TEAMMEMBER}, HTTPStatus.FORBIDDEN),
        (USERS["ARCHILYSE_ONE_ADMIN"], {USER_ROLE.ARCHILYSE_ONE_ADMIN}, HTTPStatus.OK),
    ],
)
def test_verify_jwt_claims(user, protected_roles, expected_status_code):
    test_app = Flask(__name__)
    test_blueprint, test_method = blueprint_with_before_request(roles=protected_roles)
    configure_auth_server(flask_app=test_app, blueprint=test_blueprint)

    client = test_app.test_client()

    login_with(client, user)

    response = client.get(
        get_address_for(
            view_function=test_method, blueprint=test_blueprint, flask_app=test_app
        )
    )

    assert response.status_code == expected_status_code


@pytest.mark.parametrize("incorrect_role_configuration", [None, {}])
def test_access_control_decorator_misconfigured_missing_roles(
    incorrect_role_configuration,
):
    with pytest.raises(ValueError) as e:
        blueprint_with_decorator(roles=incorrect_role_configuration)
    assert (
        str(e.value)
        == "Cannot control resource access without providing protected user roles."
    )


def test_auth_login_wrong_credentials():
    context = create_user_context(USERS["ADMIN"])

    # Wrong Password
    response = make_request(
        method="post",
        view_function=Login,
        blueprint=login_app,
        json=dict(user=context["user"]["login"], password="some_bogus_credentials"),
    )
    response_dict = response.get_json()
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Wrong credentials" in response_dict["msg"]
    assert "roles" not in response_dict.keys()

    # Wrong User
    response = make_request(
        method="post",
        view_function=Login,
        blueprint=login_app,
        json=dict(user="admin123", password="XXX"),
    )
    response_dict = response.get_json()
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert "Wrong credentials" in response_dict["msg"]
    assert "roles" not in response_dict.keys()


def test_auth_login_updates_last_login(client, freezer):
    freezer.move_to("2021-07-06")

    context = create_user_context(USERS["ADMIN"])
    user = UserDBHandler.get_by(id=context["user"]["id"])
    assert not user["last_login"]

    # Login
    response = make_request(
        method="post",
        view_function=Login,
        blueprint=login_app,
        json=dict(user=context["user"]["login"], password=context["user"]["password"]),
    )

    assert response.status_code == HTTPStatus.OK
    last_login = UserDBHandler.get_by(id=context["user"]["id"])["last_login"]
    assert last_login
    # logout
    client.cookie_jar.clear_session_cookies()
    freezer.move_to("2021-07-07")  # Next day
    # Login again
    response = make_request(
        method="post",
        view_function=Login,
        blueprint=login_app,
        json=dict(user=context["user"]["login"], password=context["user"]["password"]),
    )

    assert response.status_code == HTTPStatus.OK
    new_last_login = UserDBHandler.get_by(id=context["user"]["id"])["last_login"]
    assert new_last_login > last_login
    # logout
    client.cookie_jar.clear_session_cookies()

    freezer.move_to("2021-07-08")  # Next day

    # Wrong Login now, last login does not update
    response = make_request(
        method="post",
        view_function=Login,
        blueprint=login_app,
        json=dict(user=context["user"]["login"], password="yiiiasss"),
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    same_last_login = UserDBHandler.get_by(id=context["user"]["id"])["last_login"]
    assert new_last_login == same_last_login


@login_as(USERS.keys())
def test_auth_login_right_credentials(client, login):
    """All users can login in"""
    pass
