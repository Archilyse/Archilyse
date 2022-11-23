import json
import mimetypes
import os
import urllib
from http import HTTPStatus
from typing import Set

import requests
from flask import Blueprint, Flask, jsonify, url_for
from flask.testing import FlaskClient
from flask_jwt_extended import JWTManager
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common_utils.constants import USER_ROLE
from common_utils.exceptions import UserAuthorizationException
from slam_api.apis.login import Login, login_app
from slam_api.app import app
from slam_api.utils import authenticate_request, role_access_control


@retry(stop=stop_after_attempt(2), reraise=True)
def get_address_for(
    view_function=None,
    use_external_address=True,
    blueprint=None,
    flask_app=None,
    add_api_prefix=False,
    **kwargs,
):
    """
    Helper to get urls from the app using the function/Method objects instead of
    hardcoded strings to facilitate refactoring.
    Args:
        view_function: MethodView or flask function
        use_external_address: if used in e2e tests, the external address is used,
        otherwise a relative path to make the test client work

        blueprint: blueprint to which the MethodView or function is bonded
        flask_app: instance of Flask is the default one is not being used
        **kwargs:

    Returns:

    """
    target_app = flask_app if flask_app else app

    if not blueprint:
        function_url = view_function.__name__
    else:
        if hasattr(view_function, "view_name"):
            view_name = view_function.view_name
        else:
            view_name = view_function.__name__
        function_url = "{}.{}".format(blueprint.name, view_name)

    old_server_name = target_app.config["SERVER_NAME"]

    target_app.config["SERVER_NAME"] = os.environ["SLAM_API_INTERNAL_URL"]

    with target_app.app_context():
        url = url_for(function_url, _external=use_external_address, **kwargs)
        if add_api_prefix:
            parsed_url = urllib.parse.urlparse(url)
            url = parsed_url._replace(path=f"api{parsed_url.path}").geturl()

    target_app.config["SERVER_NAME"] = old_server_name

    return url


def blueprint_with_decorator(roles: Set[USER_ROLE]):
    test_blueprint = Blueprint("test", __name__)

    @test_blueprint.route("/route", methods=["GET"])
    @role_access_control(roles=roles)
    def dummy():
        return "OK!", HTTPStatus.OK

    return test_blueprint, dummy


def blueprint_with_before_request(roles: Set[USER_ROLE]):
    test_blueprint = Blueprint("test", __name__)
    kwargs = {"roles": roles}

    @test_blueprint.before_request
    def make_sure_jwt_has_role_claims():
        authenticate_request(**kwargs)

    @test_blueprint.route("/route", methods=["GET"])
    def dummy():
        return "OK!", HTTPStatus.OK

    return test_blueprint, dummy


def configure_auth_server(flask_app, blueprint: Blueprint):
    flask_app.test_client_class = TestClient
    flask_app.testing = True

    @flask_app.errorhandler(UserAuthorizationException)
    def all_exception_handler(error):
        return jsonify(msg=str(error)), 403

    with flask_app.test_client():
        flask_app.config["JWT_SECRET_KEY"] = "secretkey"
        flask_app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60
        flask_app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
        flask_app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
        JWTManager(flask_app)
        flask_app.register_blueprint(blueprint)
        flask_app.register_blueprint(login_app, url_prefix="/auth")


def request_user_token(username: str, password: str, flask_app: Flask = app) -> str:
    response = make_request(
        method="post",
        view_function=Login,
        blueprint=login_app,
        flask_app=flask_app,
        json=dict(user=username, password=password),
    )
    access_token = response.get_json()["access_token"]
    return access_token


@retry(
    retry=retry_if_exception_type(requests.exceptions.ConnectionError),
    wait=wait_exponential(multiplier=2, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def make_request(
    method,
    view_function=None,
    flask_app=None,
    blueprint=None,
    address_kwargs=None,
    **kwargs,
):

    target_app = flask_app if flask_app else app
    address_kwargs = address_kwargs or {}

    address = get_address_for(
        blueprint=blueprint,
        view_function=view_function,
        **address_kwargs,
        use_external_address=False,
        flask_app=target_app,
    )

    method = method.lower()

    target_app.test_client_class = TestClient
    target_app.testing = True
    with target_app.test_client() as client:
        return getattr(client, method)(address, **kwargs)


class TestClient(FlaskClient):
    def open(self, *args, **kwargs):
        if "json" in kwargs:
            kwargs["data"] = json.dumps(kwargs.pop("json"))
            kwargs["content_type"] = mimetypes.types_map[".json"]
        return super(TestClient, self).open(*args, **kwargs)
