import psycopg2
import pytest
from sqlalchemy.exc import OperationalError
from tenacity import stop_after_attempt, wait_none

from handlers.db.utils import (
    DEFAULT_DB_WAIT_STRATEGY,
    POTENTIAL_DB_WAIT_STRATEGY,
    RETRY_ON_DB_OPERATIONAL_ERROR,
    retry_on_db_operational_error,
)


@pytest.fixture
def mocked_retry_decorator(mocker):
    import handlers.db.utils

    return mocker.patch.object(
        handlers.db.utils,
        "retry",
        return_value=lambda func: lambda *args, **kwargs: None,
    )


class TestRetryOnDbOperationalError:
    @pytest.fixture
    def mocked_session_manager(self, mocker):
        class FakeSessionManager:
            def __init__(self, tran_count):
                self.tran_count = tran_count

        def _internal(tran_count):
            import handlers.db.utils

            return mocker.patch.object(
                handlers.db.utils,
                "get_session_manager",
                return_value=FakeSessionManager(tran_count=tran_count),
            )

        return _internal

    @pytest.mark.parametrize(
        "tran_count, number_of_attempts, expected_attempts",
        [
            (0, 2, 2),
            (0, 3, 3),
            (1, 1, 1),
            (1, 2, 1),
            (1, 3, 1),
        ],
    )
    def test_retry_on_db_operational_error_expected_retries(
        self, mocked_session_manager, tran_count, number_of_attempts, expected_attempts
    ):
        # Given
        mocked_session_manager(tran_count=tran_count)
        method_counter = 0

        @retry_on_db_operational_error(stop=stop_after_attempt(number_of_attempts))
        def method_raising_an_operational_error():
            nonlocal method_counter
            method_counter += 1
            raise OperationalError(statement="buhu", params={}, orig="huhu")

        # When
        with pytest.raises(OperationalError):
            method_raising_an_operational_error()

        # Then
        assert method_counter == expected_attempts

    @pytest.mark.parametrize(
        "tran_count, retry_decorator_call_expected", [(0, True), (1, False)]
    )
    def test_retry_on_db_operational_error_calls_retry_decorator(
        self, mocker, mocked_session_manager, tran_count, retry_decorator_call_expected
    ):
        # Given
        mocked_session_manager(tran_count=tran_count)

        import handlers.db.utils

        spy_retry_decorator = mocker.spy(handlers.db.utils, "retry")

        @retry_on_db_operational_error(stop=stop_after_attempt(1))
        def method_raising_an_operational_error():
            raise OperationalError(statement="buhu", params={}, orig="huhu")

        # When
        with pytest.raises(OperationalError):
            method_raising_an_operational_error()

        # Then
        assert spy_retry_decorator.call_count == retry_decorator_call_expected

    @pytest.mark.parametrize(
        "wait_strategy",
        [
            dict(),
            dict(stop=stop_after_attempt(1)),
            dict(wait=wait_none()),
            dict(wait=wait_none(), stop=stop_after_attempt(1)),
        ],
    )
    def test_retry_on_db_operational_error_applies_wait_strategy(
        self, mocked_session_manager, mocked_retry_decorator, wait_strategy
    ):
        # Given
        mocked_session_manager(tran_count=0)

        @retry_on_db_operational_error(**wait_strategy)
        def decorated_method():
            pass

        # When
        decorated_method()

        # Then
        mocked_retry_decorator.assert_called_once_with(
            retry=RETRY_ON_DB_OPERATIONAL_ERROR,
            reraise=True,
            **wait_strategy or DEFAULT_DB_WAIT_STRATEGY
        )

    @pytest.mark.parametrize("tran_count", [0, 1])
    def test_retry_on_db_operational_error_returns_expected_value(
        self, mocked_session_manager, tran_count
    ):
        mocked_session_manager(tran_count=tran_count)

        # Given
        @retry_on_db_operational_error(stop=stop_after_attempt(1))
        def decorated_method():
            return 1

        # When
        assert decorated_method() == 1

    @pytest.mark.parametrize("tran_count", [0, 1])
    def test_do_not_retry_on_non_operational_errors(
        self, mocked_session_manager, tran_count
    ):
        """Run a decorated method that will raise a non-operational error
        and then assert that the method was not retried. The
        retry should only work on OperationalErrors.
        """
        # Given
        mocked_session_manager(tran_count=tran_count)
        method_counter = 0

        @retry_on_db_operational_error(stop=stop_after_attempt(3))
        def method_raising_a_non_operational_error():
            nonlocal method_counter
            method_counter += 1
            raise Exception

        # When
        with pytest.raises(Exception):
            method_raising_a_non_operational_error()

        # Then
        # Nothing got retried
        assert method_counter == 1

    @pytest.mark.parametrize(
        "exception",
        [
            OperationalError(statement="buhu", params={}, orig="huhu"),
            psycopg2.OperationalError(),
        ],
    )
    def test_retry_on_operational_errors_retries_on_expected_exception(
        self, mocked_session_manager, exception
    ):
        # Given
        mocked_session_manager(tran_count=0)
        method_counter = 0

        @retry_on_db_operational_error(stop=stop_after_attempt(3))
        def method_raising_an_operational_error():
            nonlocal method_counter
            method_counter += 1
            raise exception

        # When
        with pytest.raises(type(exception)):
            method_raising_an_operational_error()

        # Then
        assert method_counter == 3


def test_db_handlers_using_db_wait_strategy(mocked_retry_decorator):
    from handlers.db import BaseDBHandler, PotentialSimulationDBHandler
    from handlers.db.utils import get_db_handlers

    # When
    for handler in get_db_handlers(BaseDBHandler):
        if handler != PotentialSimulationDBHandler:
            handler.get_by(id=1)

    # Then
    mocked_retry_decorator.assert_called_with(
        retry=RETRY_ON_DB_OPERATIONAL_ERROR, reraise=True, **DEFAULT_DB_WAIT_STRATEGY
    )
    with pytest.raises(AssertionError):
        mocked_retry_decorator.assert_called_with(
            retry=RETRY_ON_DB_OPERATIONAL_ERROR,
            reraise=True,
            **POTENTIAL_DB_WAIT_STRATEGY
        )

    # When
    PotentialSimulationDBHandler.get_by(id=1)
    # Then
    mocked_retry_decorator.assert_called_with(
        retry=RETRY_ON_DB_OPERATIONAL_ERROR, reraise=True, **POTENTIAL_DB_WAIT_STRATEGY
    )
