import contextlib
import os
import threading
from contextlib import contextmanager
from distutils.util import strtobool
from typing import Optional

from contexttimer import timer
from scout_apm.sqlalchemy import instrument_sqlalchemy
from sqlalchemy import create_engine, event, orm
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy_utils import create_database, force_auto_coercion
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common_utils.logger import logger

db_config = dict(
    address=os.environ["PGBOUNCER_HOST"],
    port=os.environ["PGBOUNCER_PORT"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    name=os.environ["POSTGRES_DB"],
)
db_url = (
    f'postgresql+psycopg2://{db_config["user"]}:{db_config["password"]}@'
    f'{db_config["address"]}:{db_config["port"]}/{db_config["name"]}'
)
BaseDBModel = declarative_base()
force_auto_coercion()

_engine = None
_scoped_session = None
_local_manager = threading.local()

DEFAULT_ISOLATION_LEVEL: str = "SERIALIZABLE"


def get_db_engine(engine=None):
    """Get DB engine
    Encapsulated within a function and not as global var helps to not instantiate by
    just importing this file, also helps to ensure this won't be copy on process fork
    by uwsgi
    """
    global _engine
    if engine:
        _engine = engine

    if not _engine:
        _engine = create_engine(
            db_url,
            client_encoding="utf8",
            isolation_level=DEFAULT_ISOLATION_LEVEL,
            poolclass=NullPool,  # As Pgbouncer already is the Pool
        )

        if not strtobool(os.environ.get("TEST_ENVIRONMENT", "False")):
            instrument_sqlalchemy(_engine)

    return _engine


def get_scoped_session(engine=None):
    global _scoped_session

    if not _scoped_session:
        _scoped_session = orm.scoped_session(
            orm.sessionmaker(bind=engine or get_db_engine())
        )

    return _scoped_session


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=3, max=10),
    reraise=True,
)
@timer(logger=logger)
def recreate_postgres_metadata():
    from alembic_utils.utils import alembic_downgrade_base, alembic_upgrade_head

    create_db_if_not_exists()
    alembic_downgrade_base()
    alembic_upgrade_head()


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=3, max=10),
    reraise=True,
)
def create_db_if_not_exists():
    with contextlib.suppress(ProgrammingError):
        create_database(get_db_engine().url)


@retry(
    retry=retry_if_exception_type(OperationalError),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=3, max=10),
    reraise=True,
)
def get_alembic_version():
    """Used to establish a connection with the DB"""
    with get_db_session_scope(readonly=True) as session:
        return dict(
            session.execute(
                "select version_num as alembic_version from alembic_version;"
            ).first()
        )


class SessionManager:
    def __init__(self):
        self._session = None
        self._tran_count = 0
        self._transaction_set = False
        self._unregister_required = False
        self._readonly = False
        self._isolation_level = DEFAULT_ISOLATION_LEVEL

    @property
    def tran_count(self):
        return self._tran_count

    @staticmethod
    def _set_transaction_required(readonly: bool, isolation_level: str) -> bool:
        return readonly or isolation_level != DEFAULT_ISOLATION_LEVEL

    @staticmethod
    def _set_transaction_sql_statement(readonly: bool, isolation_level: str) -> str:
        access_level = "READ ONLY" if readonly else "READ WRITE"
        return f"SET TRANSACTION ISOLATION LEVEL {isolation_level} {access_level};"

    def _execute_set_transaction(self, connection):
        connection.execute(
            self._set_transaction_sql_statement(
                readonly=self._readonly, isolation_level=self._isolation_level
            )
        )

    def _begin_transaction_handler(self, session, transaction, connection):
        """
        To enable changing the isolation and access level per transaction the first statement
        in a transaction is preceded by a "SET TRANSACTION" statement
        """
        if not self._transaction_set:
            self._execute_set_transaction(connection=connection)
            self._transaction_set = True

    def _register_begin_transaction_handler(self, session):
        event.listens_for(session, "after_begin")(self._begin_transaction_handler)
        self._unregister_required = True

    def _unregister_begin_transaction_handler(self):
        if self._unregister_required:
            event.remove(self._session, "after_begin", self._begin_transaction_handler)
            self._unregister_required = False
            self._transaction_set = False

    def _get_configured_session(self, readonly: bool, isolation_level: str):
        session = get_scoped_session()()
        if self._set_transaction_required(
            readonly=readonly, isolation_level=isolation_level
        ):
            self._readonly = readonly
            self._isolation_level = isolation_level
            self._register_begin_transaction_handler(session)
        return session

    def get_session(self, readonly: bool, isolation_level: str):
        if self._tran_count == 0:
            self._session = self._get_configured_session(
                readonly=readonly, isolation_level=isolation_level
            )
        else:
            self._session.begin_nested()
        self._tran_count += 1
        return self._session

    def close_session(self):
        self._tran_count -= 1
        if self._tran_count == 0:
            self._unregister_begin_transaction_handler()
            self._session.close()
            self._session = None


def get_session_manager():
    if not hasattr(_local_manager, "manager"):
        _local_manager.manager = SessionManager()
    return _local_manager.manager


@contextmanager
def get_db_session_scope(readonly: bool = False, isolation_level: Optional[str] = None):
    """This ensures that all methods in a call stack use the same transaction"""
    manager = get_session_manager()
    session = manager.get_session(
        readonly=readonly, isolation_level=isolation_level or DEFAULT_ISOLATION_LEVEL
    )
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        manager.close_session()
