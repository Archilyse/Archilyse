import io
import mimetypes
from http import HTTPStatus
from typing import Optional

from flask import jsonify, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields
from marshmallow_enum import EnumField

from common_utils.constants import (
    REGION,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    TASK_TYPE,
    USER_ROLE,
)
from db_models import FloorDBModel, UnitDBModel
from handlers import SlamSimulationHandler, UnitHandler
from handlers.db import SiteDBHandler, UnitDBHandler
from handlers.db.area_handler import UnitAreaDBHandler, UnitAreaDBSchema
from handlers.db.serialization.geojson import LayoutSchema
from handlers.db.unit_handler import UnitDBSchema
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.entity_ownership_validation import validate_entity_ownership
from slam_api.serialization import GCSLinkArgs
from slam_api.utils import ensure_site_consistency, role_access_control

unit_app = Blueprint("unit", __name__)


class UnitViewSchema(Schema):
    id = fields.Integer()
    floor_id = fields.Integer()
    client_id = fields.String()
    created = fields.Str()
    updated = fields.Str()


@unit_app.route("/<int:unit_id>/simulation_results", methods=["GET"])
@role_access_control(
    roles={
        USER_ROLE.COMPETITION_VIEWER,
        USER_ROLE.COMPETITION_ADMIN,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
@validate_entity_ownership(UnitDBModel, lambda kwargs: {"id": kwargs["unit_id"]})
@unit_app.arguments(
    Schema.from_dict(
        {
            "georeferenced": fields.Boolean(),
            "simulation_type": EnumField(TASK_TYPE, by_value=False),
        }
    ),
    location="query",
    as_kwargs=True,
)
@unit_app.response(status_code=HTTPStatus.OK)
def simulation_results(
    unit_id: int,
    simulation_type: TASK_TYPE,
    georeferenced: Optional[bool] = False,
):
    return SlamSimulationHandler.get_simulation_results_formatted(
        unit_id=unit_id, simulation_type=simulation_type, georeferenced=georeferenced
    )


@unit_app.route("/<int:unit_id>/brooks/simple", methods=["GET"])
@role_access_control(
    roles={
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
@validate_entity_ownership(UnitDBModel, lambda kwargs: {"id": kwargs["unit_id"]})
@unit_app.response(schema=LayoutSchema, status_code=HTTPStatus.OK)
def get_unit_simple_brooks_model_api(unit_id: int):
    layout = UnitHandler().get_unit_layout(
        unit_id=unit_id, georeferenced=True, postprocessed=False, deep_copied=False
    )
    unit_info = UnitDBHandler.get_by(id=unit_id, output_columns=["site_id"])
    georef_region = SiteDBHandler.get_by(
        id=unit_info["site_id"], output_columns=["georef_region"]
    )["georef_region"]
    return jsonify(layout.to_lat_lon_json(from_region=REGION[georef_region]))


@unit_app.route("/<int:unit_id>")
class UnitView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @unit_app.response(schema=UnitViewSchema, status_code=HTTPStatus.OK)
    def get(self, unit_id: int):
        full_unit = UnitDBHandler.get_by(
            id=unit_id, output_columns=["id", "floor_id", "client_id"]
        )
        return jsonify(full_unit)

    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
        }
    )
    @unit_app.response(status_code=HTTPStatus.NO_CONTENT)
    def delete(self, unit_id: int):
        UnitDBHandler.delete(item_pk={"id": unit_id})
        return jsonify(), HTTPStatus.NO_CONTENT

    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @unit_app.arguments(
        Schema.from_dict(UnitDBSchema().fields)(partial=True),
        location="json",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=UnitDBModel)
    @ensure_site_consistency()
    @unit_app.response(schema=UnitDBSchema, status_code=HTTPStatus.OK)
    def put(self, unit_id: int, **kwargs):
        return jsonify(UnitDBHandler.update(dict(id=unit_id), new_values=kwargs))


@unit_app.route("/<int:unit_id>/areas/<int:area_id>")
class PutUnitAreaView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @unit_app.arguments(
        Schema.from_dict(UnitAreaDBSchema().fields)(partial=True),
        location="json",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=UnitDBModel)
    @ensure_site_consistency()
    def put(self, unit_id: int, area_id: int, **kwargs):
        updated_area = UnitAreaDBHandler.update(
            item_pks={"area_id": area_id, "unit_id": unit_id}, new_values=kwargs
        )
        return jsonify(updated_area), HTTPStatus.OK


@unit_app.route("/")
class UnitCollectionView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @unit_app.arguments(
        Schema.from_dict({"floor_id": fields.Int(required=True)}),
        location="query",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=FloorDBModel)
    @unit_app.response(schema=UnitViewSchema(many=True), status_code=HTTPStatus.OK)
    def get(self, floor_id: int):
        units = UnitDBHandler.find(
            floor_id=floor_id,
            output_columns=[
                "id",
                "client_id",
                "floor_id",
                "created",
                "updated",
                "labels",
                "ph_final_gross_rent_annual_m2",
                "ph_final_gross_rent_adj_factor",
            ],
        )
        return jsonify(units), HTTPStatus.OK


@unit_app.route("/<int:unit_id>/deliverable", methods=["GET"])
@unit_app.arguments(
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
def get_bytes_of_unit_deliverable(
    unit_id: int, file_format: SUPPORTED_OUTPUT_FILES, language: SUPPORTED_LANGUAGES
):
    """Used in the DMS/PM dashboard"""
    file_content, file_name = UnitHandler.get_gcs_link_as_bytes(
        unit_id=unit_id, file_format=file_format, language=language
    )
    return send_file(
        io.BytesIO(file_content),
        mimetype=mimetypes.types_map[f".{file_format.name.lower()}"],
        as_attachment=True,
        attachment_filename=file_name,
    )
