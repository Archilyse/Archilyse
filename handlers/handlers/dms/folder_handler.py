from typing import Dict, List

from connectors.db_connector import get_db_session_scope
from db_models.db_entities import FolderDBModel
from handlers import DocumentHandler, FileHandler
from handlers.db import FileDBHandler, FolderDBHandler


class FolderHandler(DocumentHandler):
    db_model = FolderDBModel
    db_handler = FolderDBHandler
    parent_key = FolderDBModel.parent_folder_id.name

    @classmethod
    def _update_database(cls, document_id: int, data: Dict, **kwargs) -> Dict:
        with get_db_session_scope():
            return cls._update_db_recursively(
                folder_id=document_id, data=data, associations=kwargs["associations"]
            )

    @classmethod
    def _update_db_recursively(
        cls, folder_id: int, data: Dict, associations: Dict
    ) -> Dict:
        for file in FileDBHandler.find(output_columns=["id"], folder_id=folder_id):
            FileDBHandler.update(item_pks={"id": file["id"]}, new_values=associations)
        for subfolder in FolderDBHandler.find(
            output_columns=["id"], parent_folder_id=folder_id
        ):
            cls._update_db_recursively(
                folder_id=subfolder["id"], data=associations, associations=associations
            )

        return FolderDBHandler.update(item_pks={"id": folder_id}, new_values=data)

    @classmethod
    def remove(cls, folder_id: int):
        """
        removes folder, subfolders and its files permanently
        """
        client_id = FolderDBHandler.get_by(id=folder_id)["client_id"]
        files_to_delete_from_gcp = cls.files_to_delete_from_gcp(
            folder_id=folder_id, files_to_delete_from_gcp=[]
        )

        FolderDBHandler.delete(item_pk={"id": folder_id})
        for checksum in files_to_delete_from_gcp:
            FileHandler().delete_file_from_gcs(client_id=client_id, checksum=checksum)

    @classmethod
    def files_to_delete_from_gcp(
        cls, folder_id: int, files_to_delete_from_gcp: List[str]
    ) -> List[str]:
        files_to_delete_from_gcp.extend(
            file["checksum"]
            for file in FileDBHandler.find(
                output_columns=["id", "checksum"], folder_id=folder_id
            )
        )

        for subfolder in FolderDBHandler.find(
            output_columns=["id"], parent_folder_id=folder_id
        ):
            files_to_delete_from_gcp = cls.files_to_delete_from_gcp(
                folder_id=subfolder["id"],
                files_to_delete_from_gcp=files_to_delete_from_gcp,
            )
        return files_to_delete_from_gcp

    @classmethod
    def set_status_deleted_folder(cls, folder_id: int, deleted: bool):
        with get_db_session_scope():
            folder = cls.set_status_deleted_recursively(
                folder_id=folder_id, deleted=deleted
            )
        return folder

    @classmethod
    def set_status_deleted_recursively(cls, folder_id: int, deleted: bool):
        """
        sets deleted = True or False for folder, subfolders and its files
        """

        for subfolder in FolderDBHandler.find(
            output_columns=["id"], parent_folder_id=folder_id
        ):
            cls.set_status_deleted_recursively(
                folder_id=subfolder["id"], deleted=deleted
            )

        FileDBHandler.bulk_update(
            deleted={
                file["id"]: deleted
                for file in FileDBHandler.find(
                    folder_id=folder_id, output_columns=["id"]
                )
            },
        )

        folder = FolderDBHandler.update(
            item_pks={"id": folder_id}, new_values={"deleted": deleted}
        )
        return folder

    @classmethod
    def get_files_of_folder(cls, folder_id: int, deleted: bool) -> List[Dict]:
        return FileDBHandler.find(
            folder_id=folder_id,
            deleted=deleted,
        )
