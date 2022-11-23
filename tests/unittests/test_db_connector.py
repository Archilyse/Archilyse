import pytest

from connectors.db_connector import DEFAULT_ISOLATION_LEVEL, SessionManager
from tests.constants import NON_DEFAULT_ISOLATION_LEVEL


class TestSessionManager:
    @pytest.mark.parametrize(
        "readonly, isolation_level, expected_result",
        [
            (True, DEFAULT_ISOLATION_LEVEL, True),
            (False, DEFAULT_ISOLATION_LEVEL, False),
            (True, NON_DEFAULT_ISOLATION_LEVEL, True),
            (False, NON_DEFAULT_ISOLATION_LEVEL, True),
        ],
    )
    def test_set_transaction_required(self, readonly, isolation_level, expected_result):
        assert (
            SessionManager._set_transaction_required(
                readonly=readonly, isolation_level=isolation_level
            )
            is expected_result
        )

    @pytest.mark.parametrize("readonly", [True, False])
    @pytest.mark.parametrize(
        "isolation_level", [DEFAULT_ISOLATION_LEVEL, NON_DEFAULT_ISOLATION_LEVEL]
    )
    def test_set_transaction_sql_statement(self, readonly, isolation_level):
        assert (
            SessionManager._set_transaction_sql_statement(
                readonly=readonly, isolation_level=isolation_level
            )
            == f"SET TRANSACTION ISOLATION LEVEL {isolation_level} READ {'ONLY' if readonly else 'WRITE'};"
        )

    @pytest.mark.parametrize("readonly", [True, False])
    @pytest.mark.parametrize(
        "isolation_level", [DEFAULT_ISOLATION_LEVEL, NON_DEFAULT_ISOLATION_LEVEL]
    )
    @pytest.mark.parametrize("transaction_set", [True, False])
    def test_begin_transaction_handler(
        self, mocker, readonly, isolation_level, transaction_set
    ):
        from connectors.db_connector import SessionManager

        spy_set_transaction_sql_statement = mocker.spy(
            SessionManager, "_set_transaction_sql_statement"
        )

        mocked_connection = mocker.MagicMock()

        session_manager = SessionManager()
        session_manager._readonly = readonly
        session_manager._isolation_level = isolation_level
        session_manager._transaction_set = transaction_set

        session_manager._begin_transaction_handler(
            session=mocker.ANY, transaction=mocker.ANY, connection=mocked_connection
        )

        if transaction_set:
            mocked_connection.execute.assert_not_called()
        else:
            spy_set_transaction_sql_statement.assert_called_once_with(
                readonly=readonly, isolation_level=isolation_level
            )
            mocked_connection.execute.assert_called_once_with(
                spy_set_transaction_sql_statement.spy_return
            )

        assert session_manager._transaction_set is True

    def test_register_begin_transaction_handler(self, mocker):
        from connectors.db_connector import SessionManager, event

        mocked_listens_for = mocker.patch.object(event, "listens_for")

        session_manager = SessionManager()
        session_manager._register_begin_transaction_handler(session=mocker.ANY)

        mocked_listens_for.assert_called_once()
        assert session_manager._unregister_required is True

    @pytest.mark.parametrize("unregister_required", [True, False])
    def test_unregister_begin_transaction_handler(self, mocker, unregister_required):
        from connectors.db_connector import SessionManager, event

        mocked_remove = mocker.patch.object(event, "remove")

        session_manager = SessionManager()
        session_manager._unregister_required = unregister_required
        session_manager._transaction_set = unregister_required

        session_manager._unregister_begin_transaction_handler()

        if unregister_required:
            mocked_remove.assert_called_once()
        else:
            mocked_remove.assert_not_called()
        assert session_manager._unregister_required is False
        assert session_manager._transaction_set is False

    @pytest.mark.parametrize("set_transaction_required", [True, False])
    def test_get_configured_session(self, mocker, set_transaction_required):
        mocked_set_transaction_required = mocker.patch.object(
            SessionManager,
            "_set_transaction_required",
            return_value=set_transaction_required,
        )
        mocked_register_begin_transaction_handler = mocker.patch.object(
            SessionManager, "_register_begin_transaction_handler"
        )

        readonly = True
        isolation_level = NON_DEFAULT_ISOLATION_LEVEL

        session_manager = SessionManager()
        session_manager._get_configured_session(
            readonly=True, isolation_level=isolation_level
        )

        mocked_set_transaction_required.assert_called_once_with(
            readonly=readonly, isolation_level=isolation_level
        )
        if set_transaction_required:
            mocked_register_begin_transaction_handler.assert_called_once()
            assert session_manager._readonly is readonly
            assert session_manager._isolation_level is isolation_level
        else:
            mocked_register_begin_transaction_handler.assert_not_called()
            assert session_manager._readonly is not readonly
            assert session_manager._isolation_level != isolation_level

    @pytest.mark.parametrize("readonly", [True, False])
    @pytest.mark.parametrize(
        "isolation_level", [DEFAULT_ISOLATION_LEVEL, NON_DEFAULT_ISOLATION_LEVEL]
    )
    def test_get_session(self, mocker, readonly, isolation_level):
        from connectors.db_connector import SessionManager

        fake_session = mocker.MagicMock()
        mocked_configure_session = mocker.patch.object(
            SessionManager, "_get_configured_session", return_value=fake_session
        )

        session_manager = SessionManager()

        # When
        session = session_manager.get_session(
            readonly=readonly, isolation_level=isolation_level
        )

        # Then
        mocked_configure_session.assert_called_once_with(
            readonly=readonly, isolation_level=isolation_level
        )
        assert session_manager.tran_count == 1
        assert session is fake_session

        # When
        # Making a second call to get_session
        kwargs_without_effect = dict(
            readonly=False if readonly else True,
            isolation_level="SOME OTHER ISOLATION LEVEL",
        )
        nested_session = session_manager.get_session(**kwargs_without_effect)

        # Then
        mocked_configure_session.assert_called_once()
        fake_session.begin_nested.assert_called_once()
        assert session_manager.tran_count == 2
        assert nested_session is fake_session

    @pytest.mark.parametrize("tran_count", [3, 2, 1])
    def test_close_session(self, mocker, tran_count):
        fake_session = mocker.MagicMock()
        mocked_unregister_begin_transaction_handler = mocker.patch.object(
            SessionManager, "_unregister_begin_transaction_handler"
        )

        session_manager = SessionManager()
        session_manager._session = fake_session
        session_manager._tran_count = tran_count

        # When
        session_manager.close_session()

        # Then
        assert session_manager._tran_count == tran_count - 1
        if tran_count == 1:
            fake_session.close.assert_called_once()
            mocked_unregister_begin_transaction_handler.assert_called_once()
            assert session_manager._session is None
        else:
            fake_session.close.assert_not_called()
            mocked_unregister_begin_transaction_handler.assert_not_called()
            assert session_manager._session is fake_session
