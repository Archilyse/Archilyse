import pytest

from connectors.db_connector import DEFAULT_ISOLATION_LEVEL
from tests.constants import NON_DEFAULT_ISOLATION_LEVEL


class TestBaseDBHandler:
    @pytest.mark.parametrize("readonly", [True, False])
    @pytest.mark.parametrize(
        "isolation_level", [DEFAULT_ISOLATION_LEVEL, NON_DEFAULT_ISOLATION_LEVEL]
    )
    def test_begin_session_applies_db_handler_isolation_level(
        self, mocker, readonly, isolation_level
    ):
        import handlers.db.base_handler as base_handler
        from handlers.db.base_handler import BaseDBHandler

        mocker.patch.object(
            base_handler.BaseDBHandler, "ISOLATION_LEVEL", isolation_level
        )
        mocked_get_db_session_scope = mocker.patch.object(
            base_handler, "get_db_session_scope"
        )
        fake_session = mocker.MagicMock()
        mocked_get_db_session_scope.return_value.__enter__.return_value = fake_session

        with base_handler.BaseDBHandler.begin_session(readonly=readonly) as session:
            assert session is fake_session

        mocked_get_db_session_scope.assert_called_once_with(
            readonly=readonly, isolation_level=BaseDBHandler.ISOLATION_LEVEL
        )
