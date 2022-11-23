from http import HTTPStatus

from slam_api.apis.group import get_groups, group_app
from tests.flask_utils import get_address_for


def test_group_list_endpoint(client, login):
    response = client.get(
        get_address_for(method="get", blueprint=group_app, view_function=get_groups)
    )
    assert response.status_code == HTTPStatus.OK, response.text
    assert response.json
