import pytest

from common_utils.exceptions import DBNotFoundException, UserAuthorizationException
from db_models.db_entities import USER_ROLE, UserDBModel
from handlers.db import GroupDBHandler, RoleDBHandler, UserDBHandler
from tests.constants import USERS
from tests.db_fixtures import create_user_context


def test_delete_user_doesnt_delete_group():
    context = create_user_context(USERS["TEAMMEMBER"])

    user = UserDBHandler.get_by(id=context["user"]["id"])
    group = GroupDBHandler.add(name="grupo")
    UserDBHandler.update(
        item_pks={"id": user["id"]}, new_values={"group_id": group["id"]}
    )
    UserDBHandler.delete(item_pk={"id": user["id"]})

    assert GroupDBHandler.exists(name="grupo")
    assert not UserDBHandler.exists(id=user["id"])


def test_delete_user_deletes_user_and_related_USER_ROLEs():
    context = create_user_context(USERS["TEAMMEMBER"])

    # given a user with role labeler exists in the db
    user = UserDBHandler.get_by(id=context["user"]["id"])
    assert len(user["roles"]) == 1
    assert user["roles"] == [USER_ROLE.TEAMMEMBER]

    # when calling .delete
    UserDBHandler.delete(item_pk=dict(id=user["id"]))

    # then the user is deleted
    with pytest.raises(DBNotFoundException):
        UserDBHandler.get_by(id=context["user"]["id"])

    # the role is not deleted
    assert RoleDBHandler.get_by(name=USER_ROLE.TEAMMEMBER)


def test_delete_role_deletes_role_and_related_USER_ROLEs():
    create_user_context(USERS["TEAMMEMBER"])
    # when calling .delete
    RoleDBHandler.delete(item_pk=dict(name=USER_ROLE.TEAMMEMBER))

    # then the role is deleted
    with pytest.raises(DBNotFoundException):
        RoleDBHandler.get_by(name=USER_ROLE.TEAMMEMBER)

    # The role is not associated with the user anymore
    from connectors.db_connector import get_db_session_scope

    with get_db_session_scope() as session:
        user = session.query(UserDBModel).first()
        # the session still holds information of the joined tables due to the lazy joined option
        # so, we need to make sure the user is synced with the DB
        session.expire(user)
        assert not user.roles


def test_add_user_with_multiple_roles():
    context = create_user_context(USERS["TEAMLEADER"])

    # given a user with role labeler exits in the db
    user = UserDBHandler.get_by(id=context["user"]["id"])
    assert len(user["roles"]) == 2
    assert {role for role in user["roles"]} == {
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
    }


@pytest.mark.parametrize(
    "user,protected_roles,should_return_user",
    [
        (USERS["TEAMMEMBER"], {USER_ROLE.ADMIN}, False),
        (USERS["ADMIN"], {USER_ROLE.TEAMMEMBER}, True),
        (USERS["TEAMMEMBER"], {USER_ROLE.TEAMMEMBER}, True),
    ],
)
def test_get_user_roles_verified(user, protected_roles, should_return_user):
    create_user_context(user)
    user_id = UserDBHandler.get_by(login=user["login"])["id"]
    slam_user = UserDBHandler.get_user_roles_verified(
        user_id=user_id, required_roles=protected_roles
    )

    if should_return_user:
        assert slam_user == UserDBHandler.get_by(id=user_id)
    else:
        assert slam_user is None


@pytest.mark.parametrize("misconfigured_required_roles", [None, ({})])
def test_get_user_roles_verified_required_roles_missing(misconfigured_required_roles):

    with pytest.raises(UserAuthorizationException) as e:
        UserDBHandler.get_user_roles_verified(
            user_id="irrelevant", required_roles=misconfigured_required_roles
        )
    assert (
        str(e.value) == "Cannot verify user role without providing required user roles."
    )
