from typing import Union

from methodtools import lru_cache

from common_utils.constants import GOOGLE_CLOUD_CLIENT_LOGOS, GOOGLE_CLOUD_LOCATION
from handlers.db import ClientDBHandler
from handlers.gcloud_storage import GCloudStorageHandler
from handlers.utils import get_client_bucket_name


class ClientHandler:
    @lru_cache()
    @classmethod
    def get_logo_content(cls, client_id: int) -> Union[bytes, None]:
        client_info = ClientDBHandler.get_by(id=client_id)
        if client_info["logo_gcs_link"]:
            return GCloudStorageHandler().download_bytes_from_media_link(
                source_media_link=client_info["logo_gcs_link"],
                bucket_name=get_client_bucket_name(client_id=client_id),
            )
        return None

    @classmethod
    def upload_logo(cls, client_id: int, logo_content: bytes) -> str:
        uploaded_link = GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=get_client_bucket_name(client_id=client_id),
            destination_folder=GOOGLE_CLOUD_CLIENT_LOGOS,
            destination_file_name=f"{client_id}.jpeg",
            contents=logo_content,
        )

        ClientDBHandler.update(
            item_pks={"id": client_id}, new_values={"logo_gcs_link": uploaded_link}
        )
        return uploaded_link

    def create_bucket_if_not_exists(self, client_id: int):
        GCloudStorageHandler().create_bucket_if_not_exists(
            location=GOOGLE_CLOUD_LOCATION,
            bucket_name=get_client_bucket_name(client_id=client_id),
            predefined_acl="private",
            predefined_default_object_acl="private",
            versioning_enabled=True,
        )
