from http import HTTPStatus

import msgpack
from flask import Response, jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from common_utils.constants import USER_ROLE
from db_models import BuildingDBModel, SiteDBModel
from handlers import BuildingHandler
from handlers.db import BuildingDBHandler
from handlers.db.building_handler import BuildingDBSchema
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.serialization import MsgSchema
from slam_api.utils import ensure_site_consistency, role_access_control

building_app = Blueprint("building", __name__)

SEVEN_DAYS_SECONDS = 604800


@building_app.route("/")
class BuildingCollectionView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @building_app.arguments(
        Schema.from_dict({"site_id": fields.Int(required=True)}),
        location="query",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=SiteDBModel)
    @building_app.response(
        schema=BuildingDBSchema(many=True), status_code=HTTPStatus.OK
    )
    def get(self, site_id: int):
        buildings = BuildingDBHandler.find(site_id=site_id)
        return jsonify(buildings), HTTPStatus.OK

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @building_app.arguments(
        Schema.from_dict(BuildingDBSchema().fields)(partial=True),
        location="json",
        as_kwargs=True,
    )
    @building_app.response(schema=BuildingDBSchema, status_code=HTTPStatus.CREATED)
    def post(self, **kwargs):
        new_building = BuildingDBHandler.add(**kwargs)
        return jsonify(new_building), HTTPStatus.CREATED


@building_app.route("/<int:building_id>")
class BuildingView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @dms_limited_entity_view(db_model=BuildingDBModel)
    @building_app.response(schema=BuildingDBSchema, status_code=HTTPStatus.OK)
    def get(self, building_id: int):
        building = BuildingDBHandler.get_by(id=building_id)
        return jsonify(building)

    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @building_app.arguments(
        Schema.from_dict(BuildingDBSchema().fields)(partial=True),
        location="json",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=BuildingDBModel)
    @ensure_site_consistency()
    @building_app.response(schema=BuildingDBSchema, status_code=HTTPStatus.OK)
    def put(self, building_id: int, **kwargs):
        updated_building = BuildingDBHandler.update(
            dict(id=building_id), new_values=kwargs
        )
        return jsonify(updated_building)

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @building_app.response(schema=MsgSchema, status_code=HTTPStatus.OK)
    def delete(self, building_id: int):
        BuildingDBHandler.delete({"id": building_id})
        return dict(msg="Deleted successfully")


@building_app.route("/<int:building_id>/3d")
class BuildingTrianglesView(MethodView):
    @role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
    @dms_limited_entity_view(db_model=BuildingDBModel)
    def get(self, building_id: int):
        triangles = BuildingHandler(
            building_id=building_id
        ).get_triangles_from_gcs_lat_lon()
        return Response(
            msgpack.dumps(triangles),
            mimetype="application/msgpack",
            headers={
                "Cache-Control": f"public, max-age={SEVEN_DAYS_SECONDS}, must-revalidate"
            },
        )
