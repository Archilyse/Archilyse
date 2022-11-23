import contextlib
import mimetypes
import tempfile
from io import BytesIO, StringIO
from pathlib import Path
from shutil import copy
from unittest.mock import call

import pytest
from google.cloud.storage import blob, bucket
from requests.exceptions import ChunkedEncodingError
from tenacity import wait_none

from common_utils.constants import GOOGLE_CLOUD_BUCKET
from common_utils.exceptions import (
    BaseSlamException,
    GCloudStorageException,
    GCSLinkEmptyException,
)
from handlers import gcloud_storage as gcloud_module
from handlers.gcloud_storage import get_md5_hash


def test_upload_deletes_local_file(mocker, annotations_path: Path, tmp_path):
    mocked_blob = mocker.patch.object(blob, "Blob", autospec=True)
    mocked_blob.upload_from_filename.return_value = None

    mocked_bucket = mocker.patch.object(bucket, "Bucket", autospec=True)
    mocked_bucket.blob.return_value = mocked_blob

    mocked_client = mocker.patch.object(
        gcloud_module.GCloudStorageHandler, "client", autospec=True
    )
    mocked_client._lookup_bucket.return_value = mocked_bucket

    sample_file = "background_image_full_plan.json"
    destination_bucket_folder = Path("salpica")

    tmp_local_file_path = tmp_path.joinpath(sample_file)
    copy(annotations_path.joinpath(sample_file), tmp_local_file_path)
    gcloud_handler = gcloud_module.GCloudStorageHandler()
    gcloud_handler.upload_file_to_bucket(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        destination_folder=destination_bucket_folder,
        local_file_path=tmp_local_file_path,
        delete_local_after_upload=False,
    )
    assert tmp_local_file_path.exists()
    assert gcloud_handler._checksum_path(tmp_local_file_path).exists()

    gcloud_handler.upload_file_to_bucket(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        destination_folder=destination_bucket_folder,
        local_file_path=tmp_local_file_path,
        delete_local_after_upload=True,
    )
    assert not tmp_local_file_path.exists()


def test_gcloud_handler_retry(mocker):
    mocked_blob = mocker.patch.object(blob, blob.Blob.__name__, autospec=True)
    hash_value = "123456"
    mocked_blob.download_to_filename.side_effect = [
        ChunkedEncodingError("Exception to retry"),
        None,
    ]
    mocked_blob.md5_hash = hash_value

    mocked_bucket = mocker.patch.object(bucket, bucket.Bucket.__name__, autospec=True)
    mocked_bucket.get_blob.return_value = mocked_blob

    mocker.patch.object(
        gcloud_module.GCloudStorageHandler,
        gcloud_module.GCloudStorageHandler._get_and_check_bucket_exists.__name__,
        return_value=mocked_bucket,
    )

    # Only last one true to allow second run to finish successfully as file is not really downloaded
    mocker.patch.object(
        gcloud_module.GCloudStorageHandler,
        gcloud_module.GCloudStorageHandler.is_file_in_local_cache.__name__,
        side_effect=[False, False, True],
    )

    gcloud_module.GCloudStorageHandler.download_file.retry.wait = wait_none()
    mocker.patch(
        "handlers.gcloud_storage.get_md5_hash_from_path", return_value=hash_value
    )

    with tempfile.TemporaryDirectory() as directory:
        gcloud_module.GCloudStorageHandler().download_file(
            bucket_name="test",
            remote_file_path=Path(f"{directory}/temp"),
            local_file_name=Path(f"{directory}/temp"),
        )

    assert mocked_blob.download_to_filename.call_count == 2


def test_gcloud_handler_delete_resource(mocker):
    from handlers.gcloud_storage import GCloudStorageHandler

    mocked_client = mocker.patch.object(GCloudStorageHandler, "client", autospec=True)
    mocked_bucket = mocker.patch.object(bucket, "Bucket", autospec=True)

    mocker.patch.object(blob, "Blob", autospec=True)
    mocked_client._lookup_bucket.return_value = mocked_bucket

    filename = Path("filename")
    source_bucket = Path("any bucket")
    GCloudStorageHandler().delete_resource(
        bucket_name=GOOGLE_CLOUD_BUCKET, source_folder=source_bucket, filename=filename
    )

    mocked_client.lookup_bucket.assert_called_once_with(GOOGLE_CLOUD_BUCKET)
    mocked_client.lookup_bucket().blob.mock_calls = [
        call(source_bucket.joinpath(filename).as_posix()),
        call().delete(),
    ]


def test_media_link_not_found_when_none_link(mock_gcp_client):
    from handlers.gcloud_storage import GCloudStorageHandler

    with pytest.raises(GCSLinkEmptyException):
        GCloudStorageHandler().download_file_from_media_link(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_file=Path("Paco won't catch this"),
            source_media_link=None,
        )


def test_download_retry_hash_not_matching(mocker):
    from handlers.gcloud_storage import GCloudStorageHandler

    class FakeBlob:
        @property
        def md5_hash(self):
            return "abc"

        def download_to_filename(*args, **kwargs):
            return

    mocker.patch.object(
        gcloud_module.GCloudStorageHandler,
        gcloud_module.GCloudStorageHandler.get_blob_check_exists.__name__,
        return_value=FakeBlob(),
    )
    mocker.patch.object(
        gcloud_module, gcloud_module.get_md5_hash_from_path.__name__, return_value="cba"
    )
    with pytest.raises(GCloudStorageException):
        with tempfile.TemporaryDirectory() as directory:
            GCloudStorageHandler().download_file(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                remote_file_path=Path("trololo"),
                local_file_name=Path(directory).joinpath("salpica.jpeg"),
            )


@pytest.mark.parametrize(
    "hash_match, orig_file_exists, hash_file_exists, expected",
    [
        (True, True, True, True),
        (True, True, False, False),
        (False, False, False, False),
        (False, False, True, False),
        (True, False, True, False),
        (False, True, True, False),
        (False, True, False, False),
    ],
)
def test_is_file_in_local_cache(
    mocker, fixtures_path, hash_match, orig_file_exists, hash_file_exists, expected
):
    from handlers.gcloud_storage import GCloudStorageHandler, get_md5_hash_from_path

    mock_blob = mocker.Mock()

    with tempfile.TemporaryDirectory() as directory:
        destination_file = Path(f"{directory}/temp.txt")

        with destination_file.open("w") as f:
            f.write("SALPICA!")

        checksum = get_md5_hash_from_path(file_path=destination_file)

        if hash_file_exists:
            checksum_path = GCloudStorageHandler._checksum_path(destination_file)
            with checksum_path.open("w") as f:
                f.write(checksum)

        if hash_match:
            mock_blob.md5_hash = checksum
        else:
            mock_blob.md5_hash = "random value"

        if not orig_file_exists:
            destination_file.unlink()

        assert (
            GCloudStorageHandler().is_file_in_local_cache(
                destination_file=destination_file,
                blob=mock_blob,
            )
            is expected
        )


def test_upload_bytes_to_bucket_destination_file_name_appended_to_destination_folder(
    mocker,
):
    from handlers.gcloud_storage import GCloudStorageHandler

    mocked_blob = mocker.patch.object(blob, "Blob", autospec=True)

    mocked_bucket = mocker.patch.object(bucket, "Bucket", autospec=True)
    mocked_bucket.blob.return_value = mocked_blob

    mocker.patch.object(
        gcloud_module.GCloudStorageHandler,
        "_get_and_check_bucket_exists",
        return_value=mocked_bucket,
    )

    GCloudStorageHandler().upload_bytes_to_bucket(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        destination_folder=Path("random_folder"),
        contents="wololo",
        destination_file_name="text.txt",
    )
    expected_call_path = Path("random_folder").joinpath("text.txt").as_posix()
    mocked_bucket.blob.assert_called_once_with(expected_call_path)
    mocked_blob.upload_from_string.assert_called_once_with(
        "wololo", mimetypes.types_map[".txt"]
    )


@pytest.mark.parametrize(
    "file_obj, expected_hash",
    [
        (StringIO("some random text"), "B2caA4wOtDcj1CFpOwc8Ow=="),
        (BytesIO(b"some random text"), "B2caA4wOtDcj1CFpOwc8Ow=="),
    ],
)
def test_get_md5_hash(file_obj, expected_hash):
    results = get_md5_hash(file_obj=file_obj)
    assert results == expected_hash


@pytest.mark.parametrize(
    "bucket_name, should_be_deleted",
    [
        ("test_something", True),
        ("production_something", False),
        ("backup_something", True),
    ],
)
def test_delete_bucket(mocker, bucket_name, should_be_deleted):
    from handlers.gcloud_storage import GCloudStorageHandler

    mocked_bucket = mocker.MagicMock()
    mocker.patch.object(
        GCloudStorageHandler, "_lookup_bucket", return_value=mocked_bucket
    )
    if should_be_deleted:
        GCloudStorageHandler().delete_bucket_if_exists(bucket_name=bucket_name)
    else:
        with contextlib.suppress(BaseSlamException):
            GCloudStorageHandler().delete_bucket_if_exists(bucket_name=bucket_name)

    assert bool(mocked_bucket.delete.call_count) == should_be_deleted
