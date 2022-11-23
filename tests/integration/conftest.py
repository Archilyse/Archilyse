import os
from contextlib import contextmanager
from copy import deepcopy

import psycopg2
import pytest
from sqlalchemy import create_engine, orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists, drop_database
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import connectors.db_connector
from common_utils.logger import logger

pytest_plugins = (
    "tests.db_fixtures",
    "tests.constant_fixtures",
    "tests.annotations_fixtures",
    "tests.file_fixtures",
    "tests.mocks_fixtures",
    "tests.helper_fixtures",
)

db_config = deepcopy(connectors.db_connector.db_config)
db_config[
    "name"
] = f"test_{db_config['name']}_{os.environ.get('PYTEST_XDIST_WORKER', 'unique')}"
db_url = "postgresql+psycopg2://{user}:{password}@{address}:{port}/{name}".format(
    **db_config
)

Base = declarative_base()
engine = create_engine(db_url, client_encoding="utf8", isolation_level="SERIALIZABLE")
DB_Session = orm.sessionmaker(bind=engine)
scoped_session = orm.scoped_session(DB_Session)


class TransactionTest:
    """Handles the creation of a test database, session management,
    patching of core DB tasks, transaction rollback after each test and
    destruction of the database after a test session."""

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=5, max=60),
        retry=retry_if_exception_type(psycopg2.OperationalError),
        reraise=True,
    )
    def __init__(self):
        # setup helpers to return our test session
        connectors.db_connector.get_db_engine(engine)
        connectors.db_connector.DB_Session = DB_Session
        logger.debug(f"Recreating db with name {db_config['name']}")
        connectors.db_connector.recreate_postgres_metadata()

    def get_session(self):
        return self.session

    def setup_session(self):
        # set up transaction and session for rollback
        self.session = scoped_session()
        self.session.begin_nested()
        connectors.db_connector.scoped_session = lambda: self.session

        @contextmanager
        def get_db_session_scope(*args, **kwargs):
            """Patched function to return the test session for the test run."""
            yield self.session
            self.session.flush()

        connectors.db_connector.get_db_session_scope = get_db_session_scope
        return self.session

    def rollback_session(self):
        self.session.rollback()
        self.session.close()


test_transaction = TransactionTest()
test_transaction.setup_session()


@pytest.fixture
def test_session():
    yield test_transaction.get_session()


def pytest_runtest_setup(*args, **kwargs):
    test_transaction.setup_session()


def pytest_runtest_teardown(*args, **kwargs):
    test_transaction.rollback_session()


def pytest_sessionfinish(*args, **kwargs):
    if database_exists(connectors.db_connector.get_db_engine().url):
        drop_database(connectors.db_connector.get_db_engine().url)


@pytest.fixture(scope="function", autouse=True)
def reset_all_sequences():
    from connectors.db_connector import get_db_session_scope
    from db_models.db_entities import BaseDBMixin

    for entity_class in BaseDBMixin.__subclasses__():
        with get_db_session_scope() as session:
            session.execute(
                f"ALTER SEQUENCE {entity_class.__tablename__}_id_seq RESTART WITH 1"
            )


def pytest_addoption(parser):
    parser.addoption("--generate-quavis-fixtures", action="store_true", default=False)
    parser.addoption("--quavis", action="store_true", default=False)


@pytest.mark.firstresult
def pytest_xdist_auto_num_workers():
    return os.cpu_count()


@pytest.fixture(autouse=True)
def requests_mock(requests_mock):
    """To make sure no requests are happening in integration tests"""
    return requests_mock
