from typing import TYPE_CHECKING, Dict, Iterator, Type

if TYPE_CHECKING:
    from handlers.db import BaseDBHandler
    from db_models import BaseDBModel

from common_utils.constants import USER_ROLE
from common_utils.exceptions import UserAuthorizationException
from db_models.db_entities import FolderDBModel
from slam_api.dms_views.collection_view import document_collection_post_validator
from slam_api.utils import Entities, get_entities


class DocumentHandler:
    db_model: "BaseDBModel"
    parent_key: str
    db_handler: Type["BaseDBHandler"]

    @classmethod
    def _update_database(cls, document_id: int, data: Dict, **kwargs) -> Dict:
        pass

    @classmethod
    def get(
        cls,
        deleted: bool = False,
        name: str = None,
        return_subdocuments: bool = True,
        dms_limited_sql_filter=None,
        **kwargs,
    ) -> Iterator[Dict]:
        """
        returns documents directly attached to the entity provided in the kwargs.
        possible kwargs are unit_id, floor_id, building_id, site_id, client_id
        if return_subdocument is False, documents which are children of other documents are not returned
        """

        filters = [cls.db_model.name.like(f"%{name}%")] if name else []

        if dms_limited_sql_filter:
            filters.extend(dms_limited_sql_filter)

        parent_entity_key = [key for key in Entities.keys if kwargs.get(key)][0]

        # NOTE: If an area_id is set, the entity also needs a floor_id or unit_id,
        #       since otherwise multiple units on different floors share the same
        #       files. Therefore, we always add the area_id field in the filter to get
        #       exactly the documents we are looking for.
        #
        #       If we also want subdocuments (e.g. files under an area of a unit),
        #       we do not check the area_id field.
        document_filter = {parent_entity_key: kwargs[parent_entity_key]}
        if not return_subdocuments:
            document_filter["area_id"] = kwargs.get("area_id", None)
            # Without the next filter we will be querying all files under the requested level
            lower_level_filter_exclusion = {
                key: kwargs.get(key) for key in Entities.child_keys(parent_entity_key)
            }
            document_filter.update(lower_level_filter_exclusion)

        documents = cls.db_handler.find(
            **document_filter,
            deleted=deleted,
            special_filter=filters,
        )
        for document in documents:
            if cls._document_directly_attached_to_entity(
                document=document, entity_key=parent_entity_key
            ) and (return_subdocuments or not cls._is_subdocument(document=document)):
                yield document

    @classmethod
    def update(cls, document_id: int, data: Dict, requesting_user: Dict) -> Dict:
        if cls._update_is_moving_document(data=data):
            associations = get_entities(**data)
            cls._validate_user_accessrights_new_associations(
                document_id=document_id,
                requesting_user=requesting_user,
                associations=associations,
            )
            data = cls._update_data_with_associations(
                data=data, associations=associations
            )
            return cls._update_database(
                document_id=document_id, data=data, associations=associations
            )

        return cls.db_handler.update(item_pks={"id": document_id}, new_values=data)

    @staticmethod
    def _document_directly_attached_to_entity(document: Dict, entity_key: str) -> bool:
        """
        returns true if the document is directly attached to the entity.
        e.g. for entity_key = building_id  a document which have building_id and floor_id is not directly
        attached to the building but to the floor
        """
        if all(
            [
                document[child_key] is None
                for child_key in Entities.child_keys(entity_key=entity_key)
            ]
        ):
            return True
        return False

    @classmethod
    def _is_subdocument(cls, document: Dict) -> bool:
        return True if document[cls.parent_key] else False

    @classmethod
    def _validate_user_accessrights_new_associations(
        cls, document_id: int, requesting_user: Dict, associations: Dict
    ):
        if (
            cls.db_handler.get_by(id=document_id)["client_id"]
            != associations["client_id"]
        ):
            raise UserAuthorizationException(
                "Its not allowed to move a folder to another client"
                if cls.db_model == FolderDBModel
                else "Its not allowed to move a file to another client"
            )
        if USER_ROLE.DMS_LIMITED in requesting_user["roles"]:
            document_collection_post_validator(
                exception_message="User is not allowed to move folder here"
                if cls.db_model == FolderDBModel
                else "User is not allowed to move file here"
            )(requesting_user=requesting_user, **associations)

    @classmethod
    def _update_data_with_associations(cls, data: Dict, associations: Dict) -> Dict:
        data.update(associations)
        data[cls.parent_key] = data.get(cls.parent_key, None)
        return data

    @classmethod
    def _update_is_moving_document(cls, data: Dict) -> bool:
        return any([key in data for key in {*Entities.keys, cls.parent_key}])
