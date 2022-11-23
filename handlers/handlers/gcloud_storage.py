import base64
import contextlib
import hashlib
import mimetypes
import os.path
from json.decoder import JSONDecodeError
from pathlib import Path
from typing import IO, Optional, Union
from urllib.parse import unquote, urlparse

import requests
from filelock import FileLock, Timeout
from google.api_core.exceptions import NotFound, ServerError, ServiceUnavailable
from google.auth.exceptions import RefreshError, TransportError
from google.cloud import storage
from google.cloud.storage import Blob
from google.cloud.storage.bucket import Bucket
from google.cloud.storage.constants import STANDARD_STORAGE_CLASS
from google.oauth2.credentials import Credentials
from requests.exceptions import ChunkedEncodingError, ReadTimeout
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)
from urllib3 import HTTPSConnectionPool
from werkzeug.datastructures import FileStorage

from common_utils.exceptions import (
    BaseSlamException,
    GCloudMissingBucketException,
    GCloudStorageException,
    GCSLinkEmptyException,
)
from common_utils.logger import logger
from common_utils.utils import decorate_all_public_methods

GOOGLE_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
RETRY_MAX_ATTEMPTS = 5
RETRY_TIME_MULTIPLIER = 3
RETRY_MAX_TIME = 10


def get_md5_hash_from_path(file_path: Path) -> str:
    with file_path.open("rb") as f:
        return get_md5_hash(file_obj=f)


def read_in_chunks(file_object: Union[FileStorage, IO], chunk_size: int = 4096):
    """Lazy function (generator) to read a file piece by piece"""
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def get_md5_hash(file_obj: Union[FileStorage, IO]) -> str:
    """Calculate file MD5 hash in b64"""
    hash_md5 = hashlib.md5()
    for chunk in read_in_chunks(file_object=file_obj):
        if isinstance(chunk, str):
            hash_md5.update(chunk.encode("UTF-8"))
        else:
            hash_md5.update(chunk)
    return base64.b64encode(hash_md5.digest()).decode("UTF-8")


def retry_on_gcloud_common_errors(func):
    return retry(
        retry=retry_if_exception_type(
            exception_types=(
                TransportError,
                requests.exceptions.ConnectionError,
                ServiceUnavailable,
                RefreshError,
                ChunkedEncodingError,
                ServerError,
                HTTPSConnectionPool,
                JSONDecodeError,
                ReadTimeout,
            )
        ),
        wait=wait_exponential(multiplier=RETRY_TIME_MULTIPLIER, max=RETRY_MAX_TIME),
        stop=stop_after_attempt(RETRY_MAX_ATTEMPTS),
        reraise=True,
    )(func)


@decorate_all_public_methods(retry_on_gcloud_common_errors)
class GCloudStorageHandler:
    project_id = os.environ["GCLOUD_STORAGE_PROJECT_ID"]
    client_id = os.environ["GCLOUD_STORAGE_CLIENT_ID"]
    client_secret = os.environ["GCLOUD_STORAGE_CLIENT_SECRET"]
    refresh_token = os.environ["GCLOUD_STORAGE_REFRESH_TOKEN"]

    def __init__(
        self, project_id=None, client_id=None, client_secret=None, refresh_token=None
    ):
        self._client = None
        self.project_id = project_id or self.project_id
        self.client_id = client_id or self.client_id
        self.client_secret = client_secret or self.client_secret
        self.refresh_token = refresh_token or self.refresh_token

    @property
    def client(self):
        if not self._client:
            self._client = storage.Client(
                project=self.project_id,
                credentials=Credentials(
                    token=None,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    refresh_token=self.refresh_token,
                    token_uri=GOOGLE_TOKEN_URL,
                ),
            )
        return self._client

    def _lookup_bucket(self, bucket_name: str) -> Bucket:
        return self.client.lookup_bucket(bucket_name)

    def _get_and_check_bucket_exists(self, bucket_name: str):
        bucket = self._lookup_bucket(bucket_name=bucket_name)
        if bucket is None:
            raise GCloudMissingBucketException(f"Bucket {bucket_name} does not exist.")
        return bucket

    def delete_bucket_if_exists(self, bucket_name: str):
        # TODO: Here to avoid accidental deletion but the real problem is that we are using the same GCP account
        #  for testing and production, we should move this to the dev environment
        if not bucket_name.startswith("test_") and not bucket_name.startswith(
            "backup_"
        ):
            raise BaseSlamException("Trying to delete non test/backup bucket")
        logger.debug(f"Deleting bucket {bucket_name}")
        existing_bucket = self._lookup_bucket(bucket_name=bucket_name)
        if existing_bucket is not None:
            with contextlib.suppress(NotFound):
                return existing_bucket.delete(force=True)
        logger.debug(f"Deleted bucket {bucket_name}")

    def delete_resource(self, bucket_name: str, source_folder: Path, filename: Path):
        existing_bucket = self._lookup_bucket(bucket_name=bucket_name)
        if existing_bucket is not None:
            blob = existing_bucket.blob(
                source_folder.joinpath(filename.name).as_posix()
            )
            blob.delete()

    def create_bucket_if_not_exists(
        self,
        bucket_name: str,
        location: str,
        predefined_acl: str = "private",
        predefined_default_object_acl: str = "private",
        versioning_enabled=False,
    ) -> Bucket:
        if exising_bucket := self._lookup_bucket(bucket_name=bucket_name):
            return exising_bucket
        bucket = Bucket(
            client=self.client, name=bucket_name, user_project=self.project_id
        )
        bucket.storage_class = STANDARD_STORAGE_CLASS
        if versioning_enabled:
            # Default config to keep 2 versions (live and previous) and delete after 14 days
            bucket.versioning_enabled = True
            bucket.add_lifecycle_delete_rule(number_of_newer_versions=2, is_live=False)
            bucket.add_lifecycle_delete_rule(days_since_noncurrent_time=14)

        return self.client.create_bucket(
            bucket,
            location=location,
            predefined_acl=predefined_acl,
            predefined_default_object_acl=predefined_default_object_acl,
        )

    def upload_file_to_bucket(
        self,
        bucket_name: str,
        destination_folder: Path,
        local_file_path: Path,
        delete_local_after_upload: bool = False,
        destination_file_name: Optional[str] = None,
    ) -> str:
        bucket = self._get_and_check_bucket_exists(bucket_name=bucket_name)

        if destination_file_name:
            destination_full_path = destination_folder.joinpath(
                destination_file_name
            ).as_posix()
        else:
            destination_full_path = destination_folder.joinpath(
                local_file_path.name
            ).as_posix()

        logger.debug(f"Uploading {local_file_path} to {destination_full_path}")
        blob = bucket.blob(destination_full_path)
        blob.upload_from_filename(local_file_path.as_posix())
        logger.debug(f"Uploaded {local_file_path} to {destination_folder.as_posix()}")

        if delete_local_after_upload:
            logger.debug(f"Deleting local file {local_file_path}")
            local_file_path.unlink()
        else:
            # Save checksum file
            checksum_path = self._checksum_path(local_file_path)
            with checksum_path.open("w") as f:
                md5_hash = get_md5_hash_from_path(file_path=local_file_path)
                f.write(md5_hash)

        return blob.media_link

    def upload_bytes_to_bucket(
        self,
        bucket_name: str,
        destination_folder: Path,
        contents: Union[bytes, str],
        destination_file_name: str,
        content_type: str = mimetypes.types_map[".txt"],
    ) -> str:
        bucket = self._get_and_check_bucket_exists(bucket_name=bucket_name)
        destination_full_path = destination_folder.joinpath(
            destination_file_name
        ).as_posix()

        logger.debug(f"Uploading bytes to {destination_full_path}")
        blob = bucket.blob(destination_full_path)
        blob.upload_from_string(contents, content_type)
        logger.debug(f"Uploaded bytes to {destination_folder.as_posix()}")

        return blob.media_link

    @staticmethod
    def _convert_media_link_to_file_in_gcp(media_link: str) -> Path:
        if not media_link:
            raise GCSLinkEmptyException("GCS link given is empty %s", media_link)
        try:
            return Path(
                Path("/".join(Path(unquote(urlparse(media_link).path)).parts))
                .as_posix()
                .split("/o/")[-1]
            )
        except TypeError as e:
            raise GCSLinkEmptyException(
                "GCS link given is empty or malformed %s", media_link
            ) from e

    def download_bytes_from_media_link(
        self, bucket_name: str, source_media_link: str
    ) -> bytes:
        return self.download_file_as_bytes(
            bucket_name=bucket_name,
            source_file_name=self._convert_media_link_to_file_in_gcp(
                media_link=source_media_link
            ),
        )

    def download_file_from_media_link(
        self, bucket_name: str, source_media_link: str, destination_file: Path
    ):
        return self.download_file(
            bucket_name=bucket_name,
            remote_file_path=self._convert_media_link_to_file_in_gcp(
                media_link=source_media_link
            ),
            local_file_name=destination_file,
        )

    @retry(
        retry=retry_if_exception_type((GCloudStorageException, Timeout)),
        stop=stop_after_attempt(5),
        wait=wait_random_exponential(multiplier=3, min=2, max=15),
        reraise=True,
    )
    def download_file(
        self, bucket_name: str, remote_file_path: Path, local_file_name: Path
    ):
        blob = self.get_blob_check_exists(
            bucket_name=bucket_name,
            file_path=remote_file_path,
        )

        local_file_name.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(local_file_name.as_posix() + ".lock", timeout=180):
            # Check file checksum
            if self.is_file_in_local_cache(destination_file=local_file_name, blob=blob):
                logger.debug(
                    f"Using local cache for {remote_file_path.as_posix()} to "
                    f"{local_file_name.as_posix()}"
                )
                return

            logger.debug(
                f"Downloading {remote_file_path.as_posix()} to {local_file_name.as_posix()}"
            )
            blob.download_to_filename(local_file_name.as_posix())

            self._store_checksum(local_file_name)

        # Ensure file downloaded correctly
        if not self.is_file_in_local_cache(destination_file=local_file_name, blob=blob):
            raise GCloudStorageException(
                f"{remote_file_path.as_posix()} download file from bucket {bucket_name} hash doesn't match"
            )

        logger.debug(
            f"Downloaded {remote_file_path.as_posix()} to {local_file_name.as_posix()}"
        )

    @staticmethod
    def _checksum_path(destination_file: Path) -> Path:
        return Path(f"{destination_file.as_posix()}.checksum")

    def _store_checksum(self, destination_file: Path) -> str:
        checksum_path = self._checksum_path(destination_file)
        with checksum_path.open("w") as f:
            md5_hash = get_md5_hash_from_path(file_path=destination_file)
            f.write(md5_hash)
        return md5_hash

    def is_file_in_local_cache(self, destination_file: Path, blob: Blob) -> bool:
        """Reads the checksum file looking for a match between the md5hash of the blob file and the file content"""
        checksum_path = self._checksum_path(destination_file)
        if destination_file.exists() and checksum_path.exists():
            with checksum_path.open("r") as f:
                md5_hash = f.read()
            if blob.md5_hash == md5_hash:
                return True
        return False

    def get_blob_check_exists(self, bucket_name: str, file_path: Path) -> Blob:
        bucket = self._get_and_check_bucket_exists(bucket_name=bucket_name)
        blob = bucket.get_blob(file_path.as_posix())

        if not blob:
            raise GCSLinkEmptyException(f"{file_path} does not exist")
        return blob

    def check_prefix_exists(self, bucket_name: str, prefix: str) -> bool:
        """Checks if the specified prefix is present. This works for files and folders"""
        return bool(
            list(
                self.client.list_blobs(
                    bucket_or_name=bucket_name, prefix=prefix, max_results=1
                )
            )
        )

    def download_file_as_bytes(self, bucket_name: str, source_file_name: Path) -> bytes:
        logger.debug(f"Downloading {source_file_name} to string")
        bucket = self._get_and_check_bucket_exists(bucket_name=bucket_name)

        blob = bucket.blob(source_file_name.as_posix())
        bytes_object = blob.download_as_bytes()
        logger.debug(f"Downloaded {source_file_name} to bytes")
        return bytes_object

    def copy_file_to_another_bucket(
        self,
        source_bucket_name: str,
        media_link: str,
        destination_bucket_name: str,
        new_name: Optional[str] = None,
    ):
        file_name = self._convert_media_link_to_file_in_gcp(media_link=media_link)
        source_bucket = self._get_and_check_bucket_exists(
            bucket_name=source_bucket_name
        )
        destination_bucket = self._get_and_check_bucket_exists(
            bucket_name=destination_bucket_name
        )
        blob = source_bucket.blob(file_name.as_posix())
        blob_copy = source_bucket.copy_blob(
            blob=blob, destination_bucket=destination_bucket, new_name=new_name
        )
        return blob_copy.media_link

    def rename_file(
        self, bucket_name: str, source_file_path: Path, new_file_name: Path
    ):
        """Source and new file name have to contain the full path inside of the bucket"""
        blob = self.get_blob_check_exists(
            bucket_name=bucket_name, file_path=source_file_path
        )
        bucket = self._get_and_check_bucket_exists(bucket_name=bucket_name)
        bucket.rename_blob(blob=blob, new_name=new_file_name.as_posix())
