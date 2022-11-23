import pytest

from tests.utils import clear_redis, recreate_db

pytest_plugins = (
    "tests.db_fixtures",
    "tests.constant_fixtures",
    "tests.annotations_fixtures",
    "tests.file_fixtures",
    "tests.helper_fixtures",
    "tests.mocks_fixtures",
    "tests.e2e_fixtures",
)


@pytest.fixture(autouse=True)
def setup_db():
    recreate_db()
    clear_redis()
