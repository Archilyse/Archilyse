import pytest

from common_utils.constants import USER_ROLE
from common_utils.exceptions import (
    UnsupportedDBModelException,
    UserAuthorizationException,
)
from slam_api import entity_ownership_validation
from slam_api.entity_ownership_validation import (
    VALIDATOR_MAP,
    validate_entity_ownership,
)

DUMMY_MODEL_ID = 777
DUMMY_CLIENT_ID = 777


@pytest.fixture
def mocked_validation_success(mocker):
    return mocker.patch.object(
        entity_ownership_validation,
        entity_ownership_validation._entity_is_owned_by_client.__name__,
        return_value=True,
    )


@pytest.fixture
def mocked_validation_failure(mocker):
    return mocker.patch.object(
        entity_ownership_validation,
        entity_ownership_validation._entity_is_owned_by_client.__name__,
        return_value=False,
    )


@pytest.fixture
def dummy_model():
    class DummyModel:
        pass

    VALIDATOR_MAP[DummyModel] = None
    return DummyModel


@pytest.fixture
def dummy_model_unsupported():
    class DummyModel:
        pass

    return DummyModel


@pytest.fixture
def dummy_func_decorated(dummy_model):
    @validate_entity_ownership(dummy_model, lambda kwargs: {"id": kwargs["fake_id"]})
    def dummy_func(fake_id):
        return fake_id == DUMMY_MODEL_ID

    return dummy_func


def test_validate_entity_ownership(
    dummy_model, dummy_func_decorated, mocked_validation_success, mocker
):
    dummy_user = {"client_id": DUMMY_CLIENT_ID, "roles": []}
    mocked_get_user = mocker.patch.object(
        entity_ownership_validation,
        entity_ownership_validation.get_user_authorized.__name__,
        return_value=dummy_user,
    )

    assert dummy_func_decorated(fake_id=DUMMY_MODEL_ID)
    mocked_get_user.assert_called_once()
    mocked_validation_success.assert_called_once()
    assert mocked_validation_success.call_args[1] == {
        "db_model": dummy_model,
        "user": dummy_user,
        "keys": {"id": DUMMY_MODEL_ID},
    }


def test_validate_entity_ownership_raises_user_auth_exception(
    dummy_model, dummy_func_decorated, mocker, mocked_validation_failure
):
    dummy_user = {"client_id": DUMMY_CLIENT_ID, "roles": []}
    mocked_get_user = mocker.patch.object(
        entity_ownership_validation,
        entity_ownership_validation.get_user_authorized.__name__,
        return_value=dummy_user,
    )

    with pytest.raises(UserAuthorizationException):
        dummy_func_decorated(fake_id=DUMMY_MODEL_ID)

    mocked_get_user.assert_called_once()
    mocked_validation_failure.assert_called_once()
    assert mocked_validation_failure.call_args[1] == {
        "db_model": dummy_model,
        "user": dummy_user,
        "keys": {"id": DUMMY_MODEL_ID},
    }


def test_admin_user_got_access(dummy_func_decorated, mocker, mocked_validation_failure):
    mocked_get_user = mocker.patch.object(
        entity_ownership_validation,
        entity_ownership_validation.get_user_authorized.__name__,
        return_value={"client_id": None, "roles": [USER_ROLE.ADMIN]},
    )

    assert dummy_func_decorated(fake_id=DUMMY_MODEL_ID)

    mocked_get_user.assert_called_once()
    mocked_validation_failure.assert_not_called()


def test_unsupported_db_model_raises_error_at_decoration_time(dummy_model_unsupported):
    with pytest.raises(UnsupportedDBModelException):

        @validate_entity_ownership(
            dummy_model_unsupported, lambda kwargs: {"id": kwargs["fake_id"]}
        )
        def dummy_func(fake_id):
            return fake_id == DUMMY_MODEL_ID
