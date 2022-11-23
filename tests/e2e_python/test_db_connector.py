import time
from concurrent import futures

import pytest
from sqlalchemy.exc import InternalError

from connectors.db_connector import (
    DEFAULT_ISOLATION_LEVEL,
    get_db_session_scope,
    get_session_manager,
)
from db_models import SiteDBModel
from tests.constants import NON_DEFAULT_ISOLATION_LEVEL


class TestGetDbSessionScope:
    def test_nested_transactions_rollback_to_savepoint(self, site):
        session_manager = get_session_manager()
        assert session_manager.tran_count == 0

        # this begins a transaction / begin
        with get_db_session_scope() as t:
            assert t.query(SiteDBModel).first()
            assert session_manager.tran_count == 1

            with pytest.raises(
                Exception,
                match="As this exception is caught only the nested transaction is rolled back",
            ):
                # this begins a nested transaction / create savepoint
                with get_db_session_scope() as t2:
                    assert t == t2
                    assert session_manager.tran_count == 2
                    t2.delete(t2.query(SiteDBModel).first())
                    raise Exception(
                        "As this exception is caught only the nested transaction is rolled back"
                    )

            # which can raise exceptions and get rolled back
            # while keeping the outer transaction in a usable state
            assert session_manager.tran_count == 1
            assert t.query(SiteDBModel).first()

        assert session_manager.tran_count == 0

    def test_execute_set_transaction_was_called(self, mocker, building):
        from connectors.db_connector import SessionManager

        spy_execute_set_transaction = mocker.spy(
            SessionManager, "_execute_set_transaction"
        )

        # Given
        kwargs_not_requiring_set_transaction = [
            {},
            dict(readonly=False),
            dict(isolation_level=DEFAULT_ISOLATION_LEVEL),
            dict(readonly=False, isolation_level=DEFAULT_ISOLATION_LEVEL),
        ]

        for kwargs in kwargs_not_requiring_set_transaction:
            # When
            with get_db_session_scope(**kwargs) as session:
                list(session.execute("select 1"))

            # Then
            assert spy_execute_set_transaction.call_count == 0

        # Given
        kwargs_requiring_set_transaction = [
            dict(readonly=True),
            dict(readonly=True, isolation_level=DEFAULT_ISOLATION_LEVEL),
            dict(isolation_level=NON_DEFAULT_ISOLATION_LEVEL),
            dict(readonly=False, isolation_level=NON_DEFAULT_ISOLATION_LEVEL),
        ]
        for expected_call_count, kwargs in enumerate(
            kwargs_requiring_set_transaction, start=1
        ):
            # When
            with get_db_session_scope(**kwargs) as session:
                list(session.execute("select 1"))

            # Then
            assert spy_execute_set_transaction.call_count == expected_call_count

        # Given
        # Nested sessions case 1
        for expected_call_count, kwargs in enumerate(
            kwargs_requiring_set_transaction, start=5
        ):
            # When
            with get_db_session_scope(**kwargs) as session:
                list(session.execute("select 1"))
                with get_db_session_scope(**kwargs) as nested_session:
                    list(nested_session.execute("select 1"))

            # Then
            assert spy_execute_set_transaction.call_count == expected_call_count

        # Given
        # Nested sessions case 2
        for expected_call_count, kwargs in enumerate(
            kwargs_requiring_set_transaction, start=9
        ):
            # When
            with get_db_session_scope(**kwargs):
                with get_db_session_scope(**kwargs) as nested_session:
                    list(nested_session.execute("select 1"))

            # Then
            assert spy_execute_set_transaction.call_count == expected_call_count

    def test_begin_event_handler_is_thread_local(self, mocker, building):
        from connectors.db_connector import SessionManager

        spy_begin_transaction_handler = mocker.spy(
            SessionManager, "_begin_transaction_handler"
        )

        def readonly_query(wait_before, wait_after):
            with get_db_session_scope(readonly=True) as session:
                time.sleep(wait_before)
                session.execute("select 1;")
                time.sleep(wait_after)

        def readwrite_query(wait_before, wait_after):
            kwargs_forcing_set_transaction = dict(
                readonly=False, isolation_level=NON_DEFAULT_ISOLATION_LEVEL
            )
            with get_db_session_scope(**kwargs_forcing_set_transaction) as session:
                time.sleep(wait_before)
                update_sql = f"UPDATE buildings SET street = 'That Street' WHERE id = {building['id']}"
                session.execute(update_sql)
                time.sleep(wait_after)

        # When
        # We have two concurrent sessions
        with futures.ThreadPoolExecutor(max_workers=3) as executor:
            trans = [
                executor.submit(readonly_query, 0, 1),
                executor.submit(readwrite_query, 0.25, 0.25),
            ]

        for t in futures.as_completed(trans):
            t.result()

        # Then
        # We hit the begin_transaction_handler twice
        # (if the event handlers would be registered non-thread-local we would have hit it four times)
        assert spy_begin_transaction_handler.call_count == 2 != 4

    def test_readonly_transaction_raises_internal_error(self, building):
        # Given
        update_sql = (
            f"UPDATE buildings SET street = 'That Street' WHERE id = {building['id']}"
        )

        # Cannot run read write statements during a read only transaction
        with pytest.raises(
            InternalError,
            match=r".* cannot execute UPDATE in a read-only transaction.*",
        ):
            with get_db_session_scope(readonly=True) as nested_session:
                nested_session.execute(update_sql)

        # Same behavior for nested transaction case 1
        with pytest.raises(
            InternalError,
            match=r".* cannot execute UPDATE in a read-only transaction.*",
        ):
            with get_db_session_scope(readonly=True) as session:
                list(session.execute("select 1;"))
                with get_db_session_scope(readonly=False) as nested_session:
                    nested_session.execute(update_sql)

        # Same behavior for nested transaction case 2
        with pytest.raises(
            InternalError,
            match=r".* cannot execute UPDATE in a read-only transaction.*",
        ):
            with get_db_session_scope(readonly=True):
                with get_db_session_scope(readonly=False) as nested_session:
                    nested_session.execute(update_sql)

    def test_isolation_level(self):
        # Given
        show_isolation_level_sql = "SHOW TRANSACTION ISOLATION LEVEL;"

        # When we don't supply an isolation level
        with get_db_session_scope() as session:
            # Then
            # we use DEFAULT_ISOLATION_LEVEL
            isolation_level = session.execute(show_isolation_level_sql).first()
            assert (
                isolation_level.transaction_isolation.upper() == DEFAULT_ISOLATION_LEVEL
            )

            # And
            # Nested sessions share the same isolation level
            with get_db_session_scope(
                isolation_level=NON_DEFAULT_ISOLATION_LEVEL
            ) as nested_session:
                isolation_level = nested_session.execute(
                    show_isolation_level_sql
                ).first()
                assert (
                    isolation_level.transaction_isolation.upper()
                    == DEFAULT_ISOLATION_LEVEL
                )

        # When we supply a non default isolation level
        with get_db_session_scope(
            isolation_level=NON_DEFAULT_ISOLATION_LEVEL
        ) as session:
            # Then
            isolation_level = session.execute(show_isolation_level_sql).first()
            assert (
                isolation_level.transaction_isolation.upper()
                == NON_DEFAULT_ISOLATION_LEVEL
            )

            # And
            # Again nested sessions share the same isolation level as the outer session
            with get_db_session_scope() as nested_session:
                isolation_level = nested_session.execute(
                    show_isolation_level_sql
                ).first()
                assert (
                    isolation_level.transaction_isolation.upper()
                    == NON_DEFAULT_ISOLATION_LEVEL
                )
