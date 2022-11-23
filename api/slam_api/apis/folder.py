from http import HTTPStatus
from typing import Optional, Tuple

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, ValidationError, fields, validates_schema
from werkzeug.exceptions import HTTPException

from common_utils.constants import USER_ROLE
from db_models.db_entities import ClientDBModel, FolderDBModel
from handlers import FolderHandler
from handlers.db.file_handler import FileDBSchema
from handlers.db.folder_handler import FolderDBHandler, FolderDBSchema
from slam_api.dms_views.collection_view import dms_limited_collection_view
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.entity_ownership_validation import validate_entity_ownership
from slam_api.utils import (
    ensure_parent_entities,
    get_user_authorized,
    role_access_control,
)

folder_app = Blueprint("Folders", "Folders")


@folder_app.errorhandler(HTTPException)
def handle_http_exception(e):
    return jsonify(e.description), HTTPStatus(e.code)


class FolderDetailsSchema(Schema):
    name = fields.String(required=False)
    labels = fields.List(fields.String, required=False)

    client_id = fields.Integer(required=False)
    site_id = fields.Integer(required=False)
    building_id = fields.Integer(required=False)
    floor_id = fields.Integer(required=False)
    unit_id = fields.Integer(required=False)
    area_id = fields.Integer(required=False)

    parent_folder_id = fields.Integer(required=False)

    @validates_schema
    def validate_area_id(self, data, **kwargs):
        if data.get("area_id", None):
            if not data.get("unit_id", None):
                raise ValidationError(
                    "If an area id is provided, the unit id has to be provided, too"
                )


@folder_app.route("/")
class FolderViewCollection(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema(many=True), status_code=HTTPStatus.OK)
    @folder_app.arguments(
        FolderDetailsSchema(partial=True),
        location="query",
        as_kwargs=True,
    )
    @ensure_parent_entities()
    @validate_entity_ownership(
        ClientDBModel, lambda kwargs: {"id": kwargs["client_id"]}
    )
    @dms_limited_collection_view(db_model=FolderDBModel)
    def get(self, **kwargs):
        """
        returns all folders filtered by whats provided in kwargs
        subfolders are not returned
        """
        return (
            jsonify(list(FolderHandler.get(**kwargs, return_subdocuments=False))),
            HTTPStatus.OK,
        )

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema, status_code=HTTPStatus.CREATED)
    @folder_app.arguments(
        FolderDetailsSchema(partial=True),
        location="json",
        as_kwargs=True,
    )
    @ensure_parent_entities()
    @validate_entity_ownership(
        ClientDBModel, lambda kwargs: {"id": kwargs["client_id"]}
    )
    @dms_limited_collection_view(db_model=FolderDBModel)
    def post(self, **kwargs):

        return (
            jsonify(
                FolderDBHandler.add(creator_id=get_user_authorized()["id"], **kwargs)
            ),
            HTTPStatus.CREATED,
        )


@folder_app.route("/<int:folder_id>")
class FolderView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema, status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    def get(self, folder_id: int):
        return jsonify(FolderDBHandler.get_by(id=folder_id)), HTTPStatus.OK

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(status_code=HTTPStatus.NO_CONTENT)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    def delete(self, folder_id: int):
        FolderHandler.remove(folder_id=folder_id)
        return jsonify({}), HTTPStatus.NO_CONTENT

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema, status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    @folder_app.arguments(
        FolderDetailsSchema(partial=True),
        location="json",
        as_kwargs=True,
    )
    def put(self, folder_id: int, **kwargs):
        return jsonify(
            FolderHandler.update(
                document_id=folder_id,
                data=kwargs,
                requesting_user=get_user_authorized(),
            )
        )


@folder_app.route("/<int:folder_id>/files")
class FolderFileView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FileDBSchema(many=True), status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    def get(self, folder_id: int):
        """
        returns all files from folder where:
        - folder_id equals provided folder_id
        - their deletion status corresponds to that of the folder
        """
        return (
            jsonify(
                FolderHandler.get_files_of_folder(
                    folder_id=folder_id,
                    deleted=FolderDBHandler.get_by(id=folder_id)["deleted"],
                )
            ),
            HTTPStatus.OK,
        )


@folder_app.route("/<int:folder_id>/subfolders")
class FolderSubfolderView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema(many=True), status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    def get(self, folder_id: int):
        """
        returns all subfolders from folder where:
        - parent_folder_id equals provided folder_id
        - their deletion status corresponds to that of the folder
        """
        return (
            jsonify(
                FolderDBHandler.find(
                    parent_folder_id=folder_id,
                    deleted=FolderDBHandler.get_by(id=folder_id)["deleted"],
                )
            ),
            HTTPStatus.OK,
        )


@folder_app.route("/trash/<int:folder_id>")
class FolderTrashView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema, status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    def put(self, folder_id: int):
        """
        sets the provided folder and its associated files to state deleted
        """
        return (
            jsonify(
                FolderHandler.set_status_deleted_folder(
                    folder_id=folder_id, deleted=True
                )
            ),
            HTTPStatus.OK,
        )


@folder_app.route("/restore/<int:folder_id>")
class FolderRestoreView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema, status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        FolderDBModel, lambda kwargs: {"id": kwargs["folder_id"]}
    )
    @dms_limited_entity_view(db_model=FolderDBModel)
    def put(self, folder_id: int):

        return (
            jsonify(
                FolderHandler.set_status_deleted_folder(
                    folder_id=folder_id, deleted=False
                )
            ),
            HTTPStatus.OK,
        )


@folder_app.route("/trash/<int:client_id>")
class FolderTrashViewCollection(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @folder_app.response(schema=FolderDBSchema(many=True), status_code=HTTPStatus.OK)
    @validate_entity_ownership(
        ClientDBModel, lambda kwargs: {"id": kwargs["client_id"]}
    )
    @dms_limited_collection_view(db_model=FolderDBModel)
    def get(self, client_id: int, dms_limited_sql_filter: Optional[Tuple] = None):
        """
        returns all folders of a client which are in state deleted:
        - dms_limited_sql_filter: tuple of sql alchemy filter conditions
        """
        return (
            jsonify(
                FolderDBHandler.find(
                    client_id=client_id,
                    deleted=True,
                    special_filter=dms_limited_sql_filter,
                )
            ),
            HTTPStatus.OK,
        )
