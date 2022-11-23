import os
from http import HTTPStatus

import requests
from requests.auth import HTTPBasicAuth

from tests.celery_utils import get_flower_address


def test_flower_is_reachable():
    address = get_flower_address()
    user, password = os.environ["FLOWER_USER"], os.environ["FLOWER_PASSWORD"]
    response = requests.get(address, auth=HTTPBasicAuth(user, password))
    assert response.status_code == HTTPStatus.OK
