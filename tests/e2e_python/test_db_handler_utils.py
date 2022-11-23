import io
import time
from concurrent import futures
from threading import Lock

import pytest
from google.cloud.exceptions import NotFound
from sqlalchemy.exc import OperationalError
from tenacity import stop_after_attempt, wait_none

from common_utils.exceptions import DBNotFoundException
from connectors.db_connector import get_db_session_scope
from handlers import DMSFloorDeliverableHandler, FileHandler, GCloudStorageHandler
from handlers.db import BuildingDBHandler, FileDBHandler
from handlers.db.utils import retry_on_db_operational_error


class TestRetryOnDBOperationalError:
    def test_only_most_outer_tran_creator_is_retried(self):
        # Given
        inner_method_counter = 0
        outer_method_counter = 0

        @retry_on_db_operational_error()
        def inner_method_raising_an_operational_error():
            nonlocal inner_method_counter
            inner_method_counter += 1
            with get_db_session_scope():
                raise OperationalError(statement="buhu", params={}, orig="huhu")

        @retry_on_db_operational_error(wait=wait_none(), stop=stop_after_attempt(2))
        def outer_method_to_be_retried():
            nonlocal outer_method_counter
            outer_method_counter += 1
            with get_db_session_scope():
                inner_method_raising_an_operational_error()

        # When
        with pytest.raises(OperationalError):
            outer_method_to_be_retried()

        # Then
        # only the outer method got retried
        assert outer_method_counter == inner_method_counter == 2

    def test_nothing_gets_retried_if_most_outer_tran_creator_is_not_decorated(self):
        # Given
        inner_method_counter = 0
        outer_method_counter = 0

        @retry_on_db_operational_error()
        def inner_method_raising_an_operational_error():
            nonlocal inner_method_counter
            inner_method_counter += 1
            with get_db_session_scope():
                raise OperationalError(statement="buhu", params={}, orig="huhu")

        def nothing_to_retry_as_not_decorated():
            nonlocal outer_method_counter
            outer_method_counter += 1
            with get_db_session_scope():
                inner_method_raising_an_operational_error()

        # When
        with pytest.raises(OperationalError):
            nothing_to_retry_as_not_decorated()

        # Then
        # nothing got retried as the most outer
        # transaction's method is not decorated
        assert outer_method_counter == 1
        assert inner_method_counter == 1

    def test_retry_on_db_operational_error_real_world_case(self, building):
        # Given
        delete_counter = 0
        delete_lock = Lock()

        @retry_on_db_operational_error()
        def delete_building(building_id, wait_for):
            with delete_lock:
                nonlocal delete_counter
                delete_counter += 1

            with get_db_session_scope():
                BuildingDBHandler.delete(item_pk={"id": building_id})
                # we wait some time so that the transactions are overlapping
                time.sleep(wait_for)

        # When
        # we force an OperationalError by attempting to delete the same entity
        # from two separate threads concurrently
        with futures.ThreadPoolExecutor(max_workers=2) as executor:
            trans = [
                executor.submit(delete_building, building["id"], 1),
                executor.submit(delete_building, building["id"], 2),
            ]

        # Then
        # one transaction committed successfully
        assert not BuildingDBHandler.find(id=building["id"])

        # one transaction fails with a DBNotFoundException
        with pytest.raises(DBNotFoundException):
            for t in futures.as_completed(trans):
                t.result()

        # the delete method was called 3 times (1 retry)
        assert delete_counter == 3


def test_file_remove_effectively_remove_from_db_even_if_gcs_does_not_exist(
    mocker, client_db, site
):
    """Unfortunately an e2e test because creating an integration test that is able to handle the db context manager
    and check if the session was effectively committed within a controlled exception is too difficult"""
    mocked_gcs_delete = mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.delete_resource.__name__,
        side_effect=[NotFound(message="")],
    )
    mocker.patch.object(FileHandler, "create")

    FileDBHandler.add(
        name="this_exists",
        content_type=".txt",
        checksum="that",
        client_id=client_db["id"],
        site_id=site["id"],
    )

    DMSFloorDeliverableHandler.create_or_replace_dms_file(
        client_id=client_db["id"],
        extension=".txt",
        buff=io.BytesIO(b"random"),
        filename="this_exists",
        site_id=site["id"],
    )
    assert mocked_gcs_delete.call_count == 1
    assert not FileDBHandler.find()
