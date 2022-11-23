from http import HTTPStatus

import pytest

from common_utils.constants import DMS_PERMISSION, USER_ROLE
from handlers import UserHandler
from handlers.db import ClientDBHandler, DmsPermissionDBHandler, UserDBHandler
from tasks.utils.constants import EmailTypes
from tests.constants import USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.utils import create_user_context, login_with


@pytest.fixture
def mocked_send_email_task(mocker):
    from slam_api.apis import user as api_user_module

    return mocker.patch.object(api_user_module.send_email_task, "delay")


@pytest.fixture
def user_dms_limited(client_db):
    return UserDBHandler.add(
        name="limited",
        roles=[USER_ROLE.DMS_LIMITED.name],
        email="fake@fake.com",
        login="new_user",
        password="pwd",
        client_id=client_db["id"],
    )


def get_users_from_api(client):
    from slam_api.apis.user import UserViewCollection, user_app

    return client.get(
        get_address_for(
            blueprint=user_app,
            use_external_address=False,
            view_function=UserViewCollection,
        )
    )


class TestUserViewCollection:
    @login_as([USER_ROLE.ADMIN.name])
    def test_get_users(self, client, client_db, login):
        response = get_users_from_api(client=client)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert response.json[0]["roles"] == [USER_ROLE.ADMIN.name]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_users_as_dms_admin(self, client, client_db, login):
        response = get_users_from_api(client=client)
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json == {"msg": "Access to this resource is forbidden."}

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_users_dms_admin(self, client, client_db, login):
        from slam_api.apis.user import UserViewCollection, user_app

        admin = UserDBHandler.add(
            name="admin",
            roles=[USER_ROLE.ADMIN.name],
            email="fake@fake.com",
            login="new_user",
            password="pwd",
            client_id=None,
        )
        response = client.get(
            get_address_for(
                blueprint=user_app,
                use_external_address=False,
                view_function=UserViewCollection,
            )
            + f"?client_id={client_db['id']}"
        )

        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert admin["id"] != response.json[0]["id"]

    @pytest.mark.parametrize(
        "new_role, task_triggered",
        [
            (USER_ROLE.TEAMMEMBER, False),
            (USER_ROLE.ADMIN, False),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, True),
        ],
    )
    @login_as([USER_ROLE.ADMIN.name])
    def test_post_users(
        self, client, client_db, login, new_role, task_triggered, mocked_send_email_task
    ):
        from slam_api.apis import user as api_user_module

        response = client.post(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserViewCollection,
            ),
            json={
                "name": "new_user",
                "roles": [new_role.name.lower()],
                "email": "fake@fake.com",
                "login": "new_user",
                "password": "password",
                "client_id": client_db["id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED, response.json
        new_user_id = response.json["id"]
        response = get_users_from_api(client=client)
        assert len(response.json) == 2
        roles = {role for user in response.json for role in user["roles"]}
        assert roles == {USER_ROLE.ADMIN.name, new_role.name}

        if task_triggered:
            mocked_send_email_task.assert_called_with(
                user_id=new_user_id, email_type=EmailTypes.ACTIVATION_EMAIL.name
            )
        else:
            mocked_send_email_task.assert_not_called()

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_users_dms_admin(
        self, client, client_db, login, mocked_send_email_task
    ):
        from slam_api.apis import user as api_user_module

        roles = [USER_ROLE.ARCHILYSE_ONE_ADMIN.name.lower()]
        response = client.post(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserViewCollection,
            ),
            json={
                "name": "new_user",
                "roles": roles,
                "email": "fake@fake.com",
                "login": "new_user",
                "password": "password",
                "client_id": client_db["id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED, response.json
        assert response.json["roles"] == [r.upper() for r in roles]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_users_dms_limited(
        self, client, client_db, login, mocked_send_email_task
    ):
        from slam_api.apis import user as api_user_module

        roles = [USER_ROLE.DMS_LIMITED.name.lower()]
        response = client.post(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserViewCollection,
            ),
            json={
                "name": "new_user",
                "roles": roles,
                "email": "fake@fake.com",
                "login": "new_user",
                "password": "password",
                "client_id": client_db["id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED, response.json
        assert response.json["roles"] == [r.upper() for r in roles]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_users_for_other_client_fails(
        self, client, client_db, login, mocked_send_email_task
    ):
        from slam_api.apis import user as api_user_module

        other_client = ClientDBHandler.add(name="OtherClient")

        roles = [USER_ROLE.ARCHILYSE_ONE_ADMIN.name.lower()]
        response = client.post(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserViewCollection,
            ),
            json={
                "name": "new_user",
                "roles": roles,
                "email": "fake@fake.com",
                "login": "new_user",
                "password": "password",
                "client_id": other_client["id"],
            },
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json
        assert (
            response.json["msg"]
            == "Requesting User is not allowed to create/update a user for this client"
        )

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_admin_user_with_dms_admin_rights_fails(
        self, client, client_db, login, mocked_send_email_task
    ):
        from slam_api.apis import user as api_user_module

        roles = [
            USER_ROLE.ARCHILYSE_ONE_ADMIN.name.lower(),
            USER_ROLE.ADMIN.name.lower(),
        ]
        response = client.post(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserViewCollection,
            ),
            json={
                "name": "new_user",
                "roles": roles,
                "email": "fake@fake.com",
                "login": "new_user",
                "password": "password",
                "client_id": client_db["id"],
            },
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json
        assert (
            response.json["msg"]
            == "Requesting User is not allowed to create/update a user with the provided roles"
        )


def test_put_new_password_invalid_token(mocked_send_email_task, client):
    from slam_api.apis import user as api_user_module

    user_context = create_user_context(USERS[USER_ROLE.ADMIN.name])
    new_thing = "something_new"
    old_thing = USERS[USER_ROLE.ADMIN.name]["password"]
    response = client.put(
        get_address_for(
            blueprint=api_user_module.user_app,
            use_external_address=False,
            view_function=api_user_module.UserChangePassword,
        ),
        json={"password": new_thing, "token": "invalid"},
    )
    assert response.status_code == HTTPStatus.FORBIDDEN, response.json
    assert "Token has expired or is not valid anymore" in response.json["msg"]
    mocked_send_email_task.assert_not_called()
    assert (
        UserDBHandler.get_user_password_verified(
            user=user_context["user"]["login"], password=old_thing
        )["id"]
        == user_context["user"]["id"]
    )


def test_put_new_password_valid_token(mocked_send_email_task, client):
    from slam_api.apis import user as api_user_module

    user_context = create_user_context(USERS[USER_ROLE.ADMIN.name])
    old_thing = USERS[USER_ROLE.ADMIN.name]["password"]
    new_thing = "something_new"
    response = client.put(
        get_address_for(
            blueprint=api_user_module.user_app,
            use_external_address=False,
            view_function=api_user_module.UserChangePassword,
        ),
        json={
            "password": "something_new",
            "token": UserHandler.generate_confirmation_token(
                user_id=user_context["user"]["id"]
            ),
        },
    )
    assert response.status_code == HTTPStatus.OK, response.json
    mocked_send_email_task.assert_not_called()
    assert (
        UserDBHandler.get_user_password_verified(
            user=user_context["user"]["login"], password=new_thing
        )["id"]
        == user_context["user"]["id"]
    )
    assert not UserDBHandler.get_user_password_verified(
        user=user_context["user"]["login"], password=old_thing
    )


def test_forgotten_password_existing_user_account(mocked_send_email_task, client):
    from slam_api.apis import user as api_user_module

    user_context = create_user_context(USERS[USER_ROLE.ADMIN.name])
    response = client.put(
        get_address_for(
            blueprint=api_user_module.user_app,
            use_external_address=False,
            view_function=api_user_module.UserForgottenPassword,
        ),
        json={"email": user_context["user"]["email"]},
    )
    assert response.status_code == HTTPStatus.OK, response.json
    mocked_send_email_task.assert_called_once_with(
        user_id=user_context["user"]["id"], email_type=EmailTypes.PASSWORD_RESET.name
    )


def test_forgotten_password_unknown_user_email(mocked_send_email_task, client):
    from slam_api.apis import user as api_user_module

    response = client.put(
        get_address_for(
            blueprint=api_user_module.user_app,
            use_external_address=False,
            view_function=api_user_module.UserForgottenPassword,
        ),
        json={"email": "unknown@account.com"},
    )
    assert response.status_code == HTTPStatus.OK, response.json
    mocked_send_email_task.assert_not_called()


class TestUserView:
    @pytest.mark.parametrize(
        "valid_user_id,is_admin,field,expected_status",
        [
            (True, False, "email", HTTPStatus.OK),
            (False, False, "email", HTTPStatus.FORBIDDEN),
            (True, True, "login", HTTPStatus.OK),
            (True, False, "login", HTTPStatus.OK),
        ],
    )
    def test_put_own_user(
        self, client, valid_user_id, is_admin, field, expected_status
    ):
        from slam_api.apis import user as api_user_module

        user_context = login_with(
            client,
            USERS[
                USER_ROLE.ARCHILYSE_ONE_ADMIN.name
                if not is_admin
                else USER_ROLE.ADMIN.name
            ],
        )
        response = client.put(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserView,
                user_id=user_context["user"]["id"] if valid_user_id else 0,
            ),
            json={field: "test@test.com"},
        )
        assert response.status_code == expected_status, response.json
        if expected_status == HTTPStatus.OK:
            assert (
                UserDBHandler.get_by(id=user_context["user"]["id"])[field]
                == "test@test.com"
            )

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_update_user_roles_dms(
        self, client, client_db, login, mocked_send_email_task
    ):
        from slam_api.apis import user as api_user_module

        new_user = UserDBHandler.add(
            name="new_user",
            roles=[USER_ROLE.ARCHILYSE_ONE_ADMIN.name],
            email="fake@fake.com",
            login="new_user",
            password="pwd",
            client_id=client_db["id"],
        )
        new_roles = [USER_ROLE.ARCHILYSE_ONE_ADMIN.name]
        response = client.put(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserView,
                user_id=new_user["id"],
            ),
            json={"roles": new_roles},
        )
        assert response.status_code == HTTPStatus.OK, response.json
        assert response.json["roles"] == new_roles

    @pytest.mark.parametrize(
        "new_data",
        [{"roles": [USER_ROLE.ARCHILYSE_ONE_ADMIN.name]}, {"email": "fake@fake.com"}],
    )
    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_dms_admin_can_not_update_user_from_other_clients(
        self, client, client_db, mocked_send_email_task, new_data, login
    ):
        from slam_api.apis import user as api_user_module

        other_client = ClientDBHandler.add(name="Other")
        user_other_client = UserDBHandler.add(
            name="new_user",
            roles=[USER_ROLE.ARCHILYSE_ONE_ADMIN.name],
            email="fake@fake.com",
            login="new_user",
            password="pwd",
            client_id=other_client["id"],
        )
        response = client.put(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.UserView,
                user_id=user_other_client["id"],
            ),
            json=new_data,
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json
        assert response.json["msg"] == "Access to this resource is forbidden."


class TestDMSUserViewCollection:
    @pytest.mark.parametrize(
        "userrole, expected_response_status, nbr_of_permissions",
        [
            (USER_ROLE.ADMIN, HTTPStatus.OK, 3),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, HTTPStatus.OK, 3),
            (USER_ROLE.DMS_LIMITED, HTTPStatus.FORBIDDEN, 0),
        ],
    )
    def test_get_all_access_rights(
        self,
        client,
        userrole,
        expected_response_status,
        nbr_of_permissions,
        client_db,
        site,
        make_sites,
        user_dms_limited,
    ):
        from slam_api.apis import user as api_user_module

        login_with(client, USERS[userrole.name])

        (site2,) = make_sites((client_db))
        DmsPermissionDBHandler.add(
            site_id=site["id"], user_id=user_dms_limited["id"], rights="WRITE"
        )
        DmsPermissionDBHandler.add(
            site_id=site2["id"], user_id=user_dms_limited["id"], rights="READ"
        )

        other_user = UserDBHandler.add(
            name="dummy_user",
            login="dummy_login",
            email="test@test.com",
            password="changeme",
            client_id=client_db["id"],
        )
        DmsPermissionDBHandler.add(
            user_id=other_user["id"], rights=DMS_PERMISSION.READ_ALL.name
        )

        response = client.get(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.DMSUserViewCollection,
            ),
        )
        assert response.status_code == expected_response_status, response.json
        if expected_response_status == HTTPStatus.OK:
            assert len(response.json) == nbr_of_permissions
            if nbr_of_permissions:
                assert {entity["rights"] for entity in response.json} == {
                    "READ",
                    "WRITE",
                    DMS_PERMISSION.READ_ALL.name,
                }
        else:
            assert response.json["msg"] == "Access to this resource is forbidden."


class TestDMSUserView:
    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_update_user_right(
        self, client, site, client_db, login, user_dms_limited, make_sites
    ):
        from slam_api.apis import user as api_user_module

        DmsPermissionDBHandler.add(
            site_id=site["id"], user_id=user_dms_limited["id"], rights="READ"
        )

        (new_site,) = make_sites(
            client_db,
        )

        new_access_rights = [
            {"site_id": site["id"], "rights": DMS_PERMISSION.WRITE.name},
            {"site_id": new_site["id"], "rights": DMS_PERMISSION.READ.name},
        ]

        response = client.put(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.DMSUserView,
                user_id=user_dms_limited["id"],
            ),
            json=new_access_rights,
        )
        db_access_rights = DmsPermissionDBHandler.find(
            output_columns=["user_id", "site_id", "rights"],
            user_id=user_dms_limited["id"],
        )
        assert response.status_code == HTTPStatus.OK
        assert len(db_access_rights) == len(new_access_rights)
        for i, new_access_right in enumerate(new_access_rights):
            assert new_access_right["site_id"] == db_access_rights[i]["site_id"]
            assert new_access_right["rights"] == db_access_rights[i]["rights"].name

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_update_user_right_empty(
        self, client, site, client_db, login, user_dms_limited, make_sites
    ):
        from slam_api.apis import user as api_user_module

        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=user_dms_limited["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )

        response = client.put(
            get_address_for(
                blueprint=api_user_module.user_app,
                use_external_address=False,
                view_function=api_user_module.DMSUserView,
                user_id=user_dms_limited["id"],
            ),
            json=[],
        )

        db_access_rights = DmsPermissionDBHandler.find(
            output_columns=["user_id", "site_id", "rights"],
            user_id=user_dms_limited["id"],
        )

        assert response.status_code == HTTPStatus.OK

        assert len(db_access_rights) == 0
