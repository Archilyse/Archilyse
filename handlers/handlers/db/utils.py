import functools

import psycopg2
import sqlalchemy.exc
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_random,
    wait_random_exponential,
)

from common_utils.utils import get_class_public_methods
from connectors.db_connector import get_session_manager

DB_WAIT_EXPONENTIAL_MULTIPLIER = 1
DB_EXPONENTIAL_MAX = 10
DB_MAX_ATTEMPTS = 5


def _operational_error(exc):
    return isinstance(exc, (psycopg2.OperationalError, sqlalchemy.exc.OperationalError))


RETRY_ON_DB_OPERATIONAL_ERROR = retry_if_exception(_operational_error)
POTENTIAL_DB_WAIT_STRATEGY = dict(
    stop=stop_after_attempt(5),
    wait=wait_random(0, 30) + wait_random_exponential(multiplier=15),
)
DEFAULT_DB_WAIT_STRATEGY = dict(
    stop=stop_after_attempt(DB_MAX_ATTEMPTS),
    wait=wait_exponential(
        multiplier=DB_WAIT_EXPONENTIAL_MULTIPLIER, max=DB_EXPONENTIAL_MAX
    ),
)


def retry_on_db_operational_error(**wait_strategy):
    wait_strategy = wait_strategy if wait_strategy else DEFAULT_DB_WAIT_STRATEGY

    def _internal(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # only the most outer transaction's decorated method is retried
            if get_session_manager().tran_count == 0:
                return retry(
                    retry=RETRY_ON_DB_OPERATIONAL_ERROR, reraise=True, **wait_strategy
                )(func)(*args, **kwargs)

            return func(*args, **kwargs)

        return wrapper

    return _internal


def apply_retry_on_operational_errors(cls, **wait_strategy):
    for name, public_method in get_class_public_methods(cls):
        setattr(
            cls, name, retry_on_db_operational_error(**wait_strategy)(public_method)
        )


def is_db_handler(cls):
    has_model = hasattr(cls, "model")
    has_schema = hasattr(cls, "schema")
    return (has_model and cls.model) and (has_schema and cls.schema)


def get_db_handlers(cls):
    def recurse(cls):
        for subcls in cls.__subclasses__():
            if is_db_handler(subcls):
                yield subcls
            yield from recurse(subcls)

    yield from recurse(cls)
