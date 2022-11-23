import io
import mimetypes
import os
from http import HTTPStatus
from typing import Optional

from flask import jsonify, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields
from werkzeug.utils import secure_filename

from common_utils.constants import (
    FLOORPLAN_UPLOAD_DIR,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    USER_ROLE,
)
from common_utils.exceptions import DBValidationException, DXFImportException
from common_utils.logger import logger
from db_models import BuildingDBModel, FloorDBModel
from handlers.db import FloorDBHandler
from handlers.db.floor_handler import FloorDBSchema
from handlers.floor_handler import FloorHandler
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.serialization import GCSLinkArgs, MsgSchema
from slam_api.utils import ensure_site_consistency, role_access_control

floor_app = Blueprint("floor", __name__)


class FloorCollectionViewPostResponseSchema(Schema):
    building_id = fields.Int()
    floor_number = fields.Int()
    plan_id = fields.Int()


class FloorCollectionViewPostFileArgsSchema(Schema):
    floorplan = fields.Raw(required=True)


class FloorCollectionViewPostFormArgsSchema(Schema):
    building_id = fields.Int()
    floor_lower_range = fields.Int(required=True)
    floor_upper_range = fields.Int(required=False, allow_none=True, dump_default=None)


class UnitLayoutSchema(Schema):
    layout = fields.Dict()
    unit_id = fields.Int()
    unit_client_id = fields.Str()


@floor_app.route("/")
class FloorCollectionView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @floor_app.arguments(
        Schema.from_dict({"building_id": fields.Str(required=True)}),
        location="querystring",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=BuildingDBModel)
    @floor_app.response(schema=FloorDBSchema(many=True), status_code=HTTPStatus.OK)
    def get(self, building_id: int):
        return (
            jsonify(FloorDBHandler.find(building_id=building_id)),
            HTTPStatus.OK,
        )

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @floor_app.arguments(
        FloorCollectionViewPostFileArgsSchema,
        location="files",
        as_kwargs=True,
    )
    @floor_app.arguments(
        FloorCollectionViewPostFormArgsSchema,
        location="form",
        as_kwargs=True,
    )
    @floor_app.response(
        schema=FloorCollectionViewPostResponseSchema(many=True),
        status_code=HTTPStatus.CREATED,
    )
    def post(
        self,
        building_id: int,
        floorplan,
        floor_lower_range: int,
        floor_upper_range: Optional[int] = None,
    ):
        FLOORPLAN_UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
        floorplan.save(
            os.path.join(FLOORPLAN_UPLOAD_DIR, secure_filename(floorplan.filename))
        )
        try:
            requested_floor_numbers = FloorHandler.get_floor_numbers_from_floor_range(
                floor_lower_range=floor_lower_range, floor_upper_range=floor_upper_range
            )

            return FloorHandler.create_floors_from_plan_file(
                floorplan=floorplan,
                building_id=building_id,
                new_floor_numbers=requested_floor_numbers,
            )

        except DXFImportException as e:
            return (
                jsonify(msg=str(e)),
                HTTPStatus.BAD_REQUEST,
            )
        except DBValidationException as e:
            return (
                jsonify(msg=str(e)),
                HTTPStatus.BAD_REQUEST,
            )

        except Exception as ex:
            logger.exception(f"Error occurred during creation of the floor: {ex}")
            return (
                jsonify(msg=f"Failed to create record {ex}"),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )


@floor_app.route("/<int:floor_id>")
class FloorView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @dms_limited_entity_view(db_model=FloorDBModel)
    @floor_app.response(schema=FloorDBSchema, status_code=HTTPStatus.OK)
    def get(self, floor_id: int):
        return jsonify(FloorDBHandler.get_by(id=floor_id))

    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @floor_app.arguments(
        Schema.from_dict(FloorDBSchema().fields)(partial=True),
        location="json",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=FloorDBModel)
    @ensure_site_consistency()
    @floor_app.response(schema=FloorDBSchema, status_code=HTTPStatus.OK)
    def put(self, floor_id: int, **kwargs):
        return jsonify(FloorDBHandler.update(dict(id=floor_id), new_values=kwargs))

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @floor_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
    def delete(self, floor_id: int):
        FloorDBHandler.delete(item_pk={"id": floor_id})
        return dict(msg="Deleted successfully")


@floor_app.route("/<int:floor_id>/deliverable", methods=["GET"])
@floor_app.arguments(
    GCSLinkArgs,
    location="querystring",
    as_kwargs=True,
)
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
def get_bytes_of_floor_deliverable(
    floor_id: int, file_format: SUPPORTED_OUTPUT_FILES, language: SUPPORTED_LANGUAGES
):
    """Used in the DMS/PM dashboard"""
    file_content, file_name = FloorHandler.get_gcs_link_as_bytes(
        floor_id=floor_id, file_format=file_format, language=language
    )
    return send_file(
        io.BytesIO(file_content),
        mimetype=mimetypes.types_map[f".{file_format.name.lower()}"],
        as_attachment=True,
        attachment_filename=file_name,
    )
