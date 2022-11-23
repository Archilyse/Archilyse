import contextlib
import mimetypes
import urllib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from google.cloud.exceptions import NotFound
from werkzeug.datastructures import FileStorage

from common_utils.constants import DMS_FOLDER_NAME
from common_utils.exceptions import ValidationException
from db_models.db_entities import FileDBModel
from handlers import DocumentHandler
from handlers.db import FileDBHandler
from handlers.gcloud_storage import GCloudStorageHandler, get_md5_hash
from handlers.utils import get_client_bucket_name


class FileHandler(DocumentHandler):
    db_model = FileDBModel
    db_handler = FileDBHandler
    parent_key = FileDBModel.folder_id.name

    # Allowed mime type only for PNG, JPEG, PDF, and text files (IFC, DXF, etc)
    # Max file size allowed in bytes
    ALLOWED_MIME_TYPE = {
        mimetypes.types_map[".csv"]: 1024 * 1024 * 25,
        mimetypes.types_map[".png"]: 1024 * 1024 * 10,
        mimetypes.types_map[".jpeg"]: 1024 * 1024 * 10,
        mimetypes.types_map[".pdf"]: 1024 * 1024 * 10,
        mimetypes.types_map[".dxf"]: 1024 * 1024 * 10,
        mimetypes.types_map[".dwg"]: 1024 * 1024 * 10,
        mimetypes.types_map[".zip"]: 1024 * 1024 * 500,
    }
    # IFC files appear to be received as octet-stream (quite generic)
    # 120MB as IFC files can be quite big
    MAX_DEFAULT_SIZE = 1024 * 1024 * 500

    @staticmethod
    def _url_encoded_checksum(checksum: str) -> str:
        return urllib.parse.quote_plus(checksum)

    @staticmethod
    def dms_path() -> Path:
        return Path(DMS_FOLDER_NAME)

    @staticmethod
    def dms_file_path(file_checksum: str) -> Path:
        return Path(DMS_FOLDER_NAME).joinpath(file_checksum)

    @classmethod
    def get_media_link(cls, bucket: str, file_checksum: str) -> str:
        return (
            GCloudStorageHandler()
            .get_blob_check_exists(
                bucket_name=bucket,
                file_path=cls.dms_file_path(file_checksum=file_checksum),
            )
            .media_link
        )

    @classmethod
    def create(
        cls,
        file_obj: FileStorage,
        filename: str,
        client_id: int,
        user_id: Optional[int] = None,
        labels: List[str] = None,
        area_id: int = None,
        unit_id: int = None,
        floor_id: int = None,
        building_id: int = None,
        site_id: int = None,
        folder_id: int = None,
    ) -> Dict:
        checksum, fsize = cls.check_file(
            file_obj=file_obj,
        )

        encoded_checksum = cls._url_encoded_checksum(checksum=checksum)
        # 1st create the file on gcs
        GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=get_client_bucket_name(client_id=client_id),
            destination_folder=cls.dms_path(),
            #
            # NOTE: Using file checksum will allow us to not duplicate files on
            #       duplicated uploads
            #
            destination_file_name=encoded_checksum,
            contents=file_obj.read(),
            content_type=file_obj.content_type,  # type: ignore
        )
        # 2nd create the file entity
        return FileDBHandler.add(
            creator_id=user_id,
            name=filename,
            content_type=file_obj.content_type,
            size=fsize,
            checksum=encoded_checksum,
            labels=labels,
            folder_id=folder_id,
            area_id=area_id,
            unit_id=unit_id,
            floor_id=floor_id,
            building_id=building_id,
            site_id=site_id,
            client_id=client_id,
        )

    @classmethod
    def _update_database(cls, document_id: int, data: Dict, **kwargs):
        return FileDBHandler.update(item_pks={"id": document_id}, new_values=data)

    @classmethod
    def check_file(
        cls,
        file_obj: FileStorage,
    ) -> Tuple[str, int]:
        checksum, fsize = cls.calculate_checksum_and_size(file_obj=file_obj)
        if fsize > cls.ALLOWED_MIME_TYPE.get(
            getattr(file_obj, "content_type", "").lower(), cls.MAX_DEFAULT_SIZE
        ):
            # NOTE: To avoid attackers or maleficent users, let's not give then the
            #       max amounts
            raise ValidationException(f"The file is too big `{fsize/(1024*1024)}MB`")

        if fsize == 0:
            raise ValidationException("Empty file")

        return checksum, fsize

    @classmethod
    def remove(cls, file_id: int):
        # NOTE we want to avoid a situation in which
        # the file is deleted on gcs but not on the database.
        file = FileDBHandler.delete(item_pk={"id": file_id})
        cls.delete_file_from_gcs(client_id=file["client_id"], checksum=file["checksum"])

    @classmethod
    def delete_file_from_gcs(cls, client_id: int, checksum: str):
        if not FileDBHandler.exists(client_id=client_id, checksum=checksum):
            # GCP file can be safely delete
            with contextlib.suppress(NotFound):
                GCloudStorageHandler().delete_resource(
                    bucket_name=get_client_bucket_name(client_id=client_id),
                    source_folder=cls.dms_path(),
                    filename=Path(checksum),
                )

    @classmethod
    def download(cls, client_id: int, checksum: str) -> bytes:
        return GCloudStorageHandler().download_file_as_bytes(
            bucket_name=get_client_bucket_name(client_id=client_id),
            source_file_name=cls.dms_file_path(file_checksum=checksum),
        )

    @staticmethod
    def calculate_checksum_and_size(file_obj: FileStorage) -> Tuple[str, int]:
        file_obj.seek(0)

        checksum = get_md5_hash(file_obj=file_obj)
        fsize = file_obj.tell()

        file_obj.seek(0)
        return checksum, fsize

    @classmethod
    def cleanup_trash(cls):
        deleted_files = FileDBHandler.remove_deleted_files()
        for checksum, client_id in deleted_files:
            cls.delete_file_from_gcs(client_id=client_id, checksum=checksum)
