import datetime

import pytest

from common_utils.constants import DMS_FILE_RETENTION_PERIOD
from handlers.db import FileDBHandler


class TestFileDBHandler:
    @pytest.mark.parametrize("file_is_expired", [True, False])
    @pytest.mark.parametrize("file_is_deleted", [True, False])
    def test_remove_deleted_files(self, client_db, file_is_expired, file_is_deleted):
        # Given
        file = FileDBHandler.add(
            name="some dms file",
            client_id=client_db["id"],
            checksum="Some checksum",
            content_type="some/random",
            deleted=file_is_deleted,
            updated=(
                datetime.datetime.utcnow()
                - (
                    DMS_FILE_RETENTION_PERIOD
                    if file_is_expired
                    else DMS_FILE_RETENTION_PERIOD / 2
                )
            ).isoformat(),
        )
        # When
        FileDBHandler.remove_deleted_files()
        # Then
        assert not FileDBHandler.exists(id=file["id"]) is (
            file_is_deleted and file_is_expired
        )
