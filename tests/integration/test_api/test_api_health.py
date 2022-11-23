from http import HTTPStatus

from slam_api.app import flask_api_check, flask_api_ping
from tests.flask_utils import make_request


def test_api_check():
    response = make_request(blueprint=None, view_function=flask_api_check, method="get")
    assert response.status_code == HTTPStatus.OK
    assert set(response.json.keys()) == {"alembic_version", "slam_version"}


def test_api_ping():
    response = make_request(blueprint=None, view_function=flask_api_ping, method="get")
    assert response.status_code == HTTPStatus.OK
