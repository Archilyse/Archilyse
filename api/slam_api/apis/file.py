import io
from http import HTTPStatus
from typing import List, Optional, Tuple

from flask import jsonify, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from flask_smorest.fields import Upload
from marshmallow import Schema, ValidationError, fields, validates_schema
from sqlalchemy.orm.exc import NoResultFound

from common_utils.constants import USER_ROLE
from common_utils.exceptions import ValidationException
from db_models import ClientDBModel
from db_models.db_entities import FileDBModel
from handlers import FileHandler
from handlers.db.file_handler import FileCommentDBHandler, FileDBHandler, FileDBSchema
from slam_api.dms_views.collection_view import dms_limited_collection_view
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.entity_ownership_validation import validate_entity_ownership
from slam_api.utils import (
    ensure_parent_entities,
    get_user_authorized,
    role_access_control,
)

file_app = Blueprint("Files", "Files")


class FileUploadSchema(Schema):
    file = Upload(required=True)


class FileDetailsSchema(Schema):
    name = fields.String(required=False)

    labels = fields.List(fields.String)
    client_id = fields.Integer(required=False)
    site_id = fields.Integer(required=False)
    building_id = fields.Integer(required=False)
    floor_id = fields.Integer(required=False)
    unit_id = fields.Integer(required=False)
    area_id = fields.Integer(required=False)
    folder_id = fields.Integer(required=False)

    @validates_schema
    def validate_area_id(self, data, **kwargs):
        if data.get("area_id", None):
            if not data.get("unit_id", None):
                raise ValidationError(
                    "If an area id is provided, the unit id has to be provided, too"
                )


class FileCommentSchema(Schema):
    comment = fields.String(required=True)


class FileTrashSchema(Schema):
    deleted = fields.Boolean(required=True)


def fetch_file_db_info(file_id, with_comments=True):
    file = FileDBHandler.get_by(id=file_id)

    user = get_user_authorized()
    if USER_ROLE.ADMIN not in user["roles"] and user["client_id"] != file["client_id"]:
        # NOTE: Raising NoResultFound makes sense here instead of `wrong client_id`,
        #       as we won't give hints for a random search of files from another
        #       client won't
        raise NoResultFound()

    if with_comments:
        file["comments"] = FileCommentDBHandler.find_in(id=file["comments"])
    else:
        del file["comments"]

    return file


@file_app.route("/")
class FileViewCollection(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema(many=True), status_code=HTTPStatus.OK)
    @file_app.arguments(
        FileDetailsSchema(partial=True), location="query", as_kwargs=True
    )
    @ensure_parent_entities()
    @validate_entity_ownership(
        ClientDBModel, lambda kwargs: {"id": kwargs["client_id"]}
    )
    @dms_limited_collection_view(db_model=FileDBModel)
    def get(self, **kwargs):
        """
        returns all files filtered by whats provided in kwargs
        files inside a folder are not returned
        """

        return (
            jsonify(list(FileHandler.get(**kwargs, return_subdocuments=False))),
            HTTPStatus.OK,
        )

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema, status_code=HTTPStatus.CREATED)
    @file_app.response(schema=FileDBSchema, status_code=HTTPStatus.BAD_REQUEST)
    #
    # HACK: Due an incompatibility/lack of feature of smorest, we require 2 different
    #       argument schema. See more:
    #       https://github.com/marshmallow-code/flask-smorest/issues/46
    #
    @file_app.arguments(FileUploadSchema, location="files")
    @file_app.arguments(
        FileDetailsSchema(partial=True), location="form", as_kwargs=True
    )
    @ensure_parent_entities()
    @validate_entity_ownership(
        ClientDBModel, lambda kwargs: {"id": kwargs["client_id"]}
    )
    @dms_limited_collection_view(db_model=FileDBModel)
    def post(
        self,
        file,
        client_id: int,
        name: str = None,
        labels: List[str] = None,
        area_id: int = None,
        unit_id: int = None,
        floor_id: int = None,
        building_id: int = None,
        site_id: int = None,
        folder_id: int = None,
    ):
        try:
            return (
                jsonify(
                    FileHandler.create(
                        user_id=get_user_authorized()["id"],
                        file_obj=file["file"],
                        filename=name or file["file"].filename,
                        labels=labels or [],
                        area_id=area_id,
                        unit_id=unit_id,
                        floor_id=floor_id,
                        building_id=building_id,
                        site_id=site_id,
                        client_id=client_id,
                        folder_id=folder_id,
                    )
                ),
                HTTPStatus.CREATED,
            )

        except ValidationException as e:
            return jsonify({"message": str(e)}), HTTPStatus.BAD_REQUEST


@file_app.route("/<int:file_id>")
class FileView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema(), status_code=HTTPStatus.OK)
    @dms_limited_entity_view(db_model=FileDBModel)
    def get(self, file_id):
        return jsonify(fetch_file_db_info(file_id, with_comments=True))

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(status_code=HTTPStatus.NO_CONTENT)
    @dms_limited_entity_view(db_model=FileDBModel)
    def delete(self, file_id):
        # This checks that file can be deleted by this current user
        fetch_file_db_info(file_id, with_comments=False)

        FileHandler.remove(file_id=file_id)
        return jsonify({}), HTTPStatus.NO_CONTENT

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema(), status_code=HTTPStatus.OK)
    @file_app.arguments(FileDetailsSchema(partial=True), location="json")
    @dms_limited_entity_view(db_model=FileDBModel)
    def put(self, data, file_id):
        # This checks that file can be updated by this current user
        fetch_file_db_info(file_id, with_comments=False)
        return jsonify(
            FileHandler.update(
                document_id=file_id, data=data, requesting_user=get_user_authorized()
            )
        )


@file_app.route("/<int:file_id>/download")
class FileViewDownload(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @dms_limited_entity_view(db_model=FileDBModel)
    def get(self, file_id):
        file = fetch_file_db_info(file_id, with_comments=False)
        return send_file(
            io.BytesIO(
                FileHandler().download(
                    client_id=file["client_id"], checksum=file["checksum"]
                )
            ),
            mimetype=file["content_type"],
            as_attachment=True,
            attachment_filename=file["name"],
        )


@file_app.route("/<int:file_id>/comment")
class FileCommentView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema(), status_code=HTTPStatus.OK)
    @file_app.arguments(FileCommentSchema, location="json")
    @dms_limited_entity_view(db_model=FileDBModel)
    def post(self, data, file_id):
        """Post a comment to the file"""

        FileCommentDBHandler.add(
            creator_id=get_user_authorized()["id"],
            file_id=file_id,
            comment=data["comment"],
        )
        return (
            jsonify(fetch_file_db_info(file_id, with_comments=True)),
            HTTPStatus.CREATED,
        )


@file_app.route("/trash")
class FileTrashViewCollection(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema(many=True), status_code=HTTPStatus.OK)
    @dms_limited_collection_view(db_model=FileDBModel)
    def get(self, dms_limited_sql_filter: Optional[Tuple] = None):
        """
        Returns files which are marked as deleted:
        - dms_limited_sql_filter: tuple of sql alchemy filter conditions

        """
        query = {}
        user = get_user_authorized()
        if USER_ROLE.ADMIN not in user["roles"]:
            query = {"client_id": user["client_id"]}
        return (
            jsonify(
                FileDBHandler.find(
                    deleted=True, **query, special_filter=dms_limited_sql_filter
                )
            ),
            HTTPStatus.OK,
        )


@file_app.route("/trash/<int:file_id>")
class FileTrashView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @file_app.response(schema=FileDBSchema(), status_code=HTTPStatus.OK)
    @file_app.arguments(FileTrashSchema, location="json")
    @dms_limited_entity_view(db_model=FileDBModel)
    def put(self, data, file_id):
        # This checks that file can be deleted by this current user
        fetch_file_db_info(file_id, with_comments=False)

        deleted_file = FileDBHandler.update(item_pks={"id": file_id}, new_values=data)
        return jsonify(deleted_file), HTTPStatus.OK
