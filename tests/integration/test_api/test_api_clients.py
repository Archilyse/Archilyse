from http import HTTPStatus
from typing import Dict

import pytest

from common_utils.constants import GOOGLE_CLOUD_LOCATION, USER_ROLE
from common_utils.exceptions import DBNotFoundException
from handlers.db import ClientDBHandler
from handlers.utils import get_client_bucket_name
from slam_api.apis.client import ClientsCollectionView, ClientsView, client_app
from tests.constants import USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.utils import login_with


@pytest.fixture
def create_client(client, mocked_gcp_create_bucket):
    def _create_client(client_payload: Dict):
        return client.post(
            get_address_for(
                blueprint=client_app,
                use_external_address=False,
                view_function=ClientsCollectionView,
            ),
            json=client_payload,
        )

    return _create_client


class TestClientViewCollection:
    @login_as([USER_ROLE.ADMIN.name, USER_ROLE.TEAMMEMBER.name])
    def test_get_clients(self, client, create_client, login, make_clients):
        """When the user is created, it's associated with the first client if exists, if there is client fixture
        defined in the function, then the user is not associated with any client"""
        num_clients = 3
        make_clients(num_clients)
        response = client.get(
            get_address_for(
                blueprint=client_app,
                use_external_address=False,
                view_function=ClientsCollectionView,
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == num_clients

    @login_as([USER_ROLE.ADMIN.name, USER_ROLE.TEAMMEMBER.name])
    def test_get_associated_client_only(self, client, client_db, create_client, login):
        """When the user is created, it's associated with the first client if exists, since we are creating a
        client_db before the user is logged in, the user is associated with that client, therefore only able
        to see the client he/she belongs to"""
        for i in range(3):
            create_client(client_payload={"name": f"client {i}"})
        response = client.get(
            get_address_for(
                blueprint=client_app,
                use_external_address=False,
                view_function=ClientsCollectionView,
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert response.json[0]["id"] == login["user"]["client_id"]


class TestClientView:
    @login_as([USER_ROLE.ADMIN.name])
    def test_get_client(self, client, client_db, login):
        response = client.get(
            get_address_for(
                blueprint=client_app,
                use_external_address=False,
                view_function=ClientsView,
                client_id=client_db["id"],
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json == client_db

    @pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER])
    def test_post_client(
        self, client, client_db, create_client, mocked_gcp_create_bucket, user_role
    ):
        login_with(client, USERS[user_role.name])
        payload = {
            "name": "New Client",
            "option_dxf": False,
            "option_pdf": False,
            "option_analysis": True,
        }

        response = create_client(client_payload=payload)
        assert response.status_code == HTTPStatus.CREATED, response.json
        assert all(response.json[k] == v for k, v in payload.items())

        mocked_gcp_create_bucket.assert_called_once_with(
            location=GOOGLE_CLOUD_LOCATION,
            bucket_name=get_client_bucket_name(client_id=response.json["id"]),
            predefined_acl="private",
            predefined_default_object_acl="private",
            versioning_enabled=True,
        )

    @pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER])
    def test_put_client(self, client_db, client, user_role):
        login_with(client, USERS[user_role.name])
        payload = {
            "option_dxf": False,
            "option_pdf": False,
        }
        response = client.put(
            get_address_for(
                blueprint=client_app,
                use_external_address=False,
                view_function=ClientsView,
                client_id=client_db["id"],
            ),
            json=payload,
        )
        assert response.status_code == HTTPStatus.OK, response.json
        response_payload = response.json
        assert all(not response_payload.pop(k) for k in payload.keys())
        assert all(
            [
                client_db[k] == v
                for k, v in response_payload.items()
                if k.startswith("option_")
            ]
        )
        assert response_payload["updated"]

    def test_put_client_unknown_field(self, client_db, client, login):
        response = client.put(
            get_address_for(
                blueprint=client_app,
                use_external_address=False,
                view_function=ClientsView,
                client_id=client_db["id"],
            ),
            json={"what": "yes"},
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    @login_as([USER_ROLE.ADMIN.name])
    def test_delete_client(self, client_db, client, site, login):
        assert (
            HTTPStatus.NO_CONTENT
            == client.delete(
                get_address_for(
                    blueprint=client_app,
                    use_external_address=False,
                    view_function=ClientsView,
                    client_id=client_db["id"],
                )
            ).status_code
        )
        with pytest.raises(DBNotFoundException):
            ClientDBHandler.get_by(id=client_db["id"])
