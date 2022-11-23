from http import HTTPStatus
from typing import Dict, Tuple

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from brooks.types import AllAreaTypes, AreaType
from brooks.util.io import BrooksJSONEncoder
from common_utils.constants import USER_ROLE
from handlers import AreaHandler
from handlers.db.area_handler import AreaDBHandler, AreaDBSchema
from slam_api.utils import ensure_site_consistency, role_access_control

areas_app = Blueprint("Area", __name__)

PutAreasSchema = Schema.from_dict(
    {
        "areas": fields.Dict(
            keys=fields.Int(),
            values=fields.Str(validate=validate.OneOf([x.name for x in AllAreaTypes])),
            validate=validate.Length(min=1),
            required=True,
            metadata={"example": {1: AreaType.ROOM.name, 2: AreaType.KITCHEN.name}},
        )
    }
)


@areas_app.route("/areas/")
@areas_app.arguments(
    Schema.from_dict({"unit_id": fields.Int(required=True)}),
    location="query",
    as_kwargs=True,
)
@role_access_control(roles={USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED})
@areas_app.response(schema=AreaDBSchema(many=False), status_code=HTTPStatus.OK)
def get_areas_by_unit_id(unit_id: int):
    return jsonify(AreaHandler.get_unit_areas(unit_id=unit_id))


@areas_app.route("/plan/<int:plan_id>/areas/autoclassified")
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@areas_app.response(schema=AreaDBSchema(many=False), status_code=HTTPStatus.OK)
def get_areas_autoclassified(plan_id: int):
    return jsonify(
        AreaHandler.get_auto_classified_plan_areas_where_not_defined(plan_id=plan_id)
    )


@areas_app.route("/plan/<int:plan_id>/areas/validate", methods=["POST"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@areas_app.arguments(
    PutAreasSchema,
    location="json",
    as_kwargs=True,
)
def validate_classifications(plan_id: int, areas: Dict[int, str]) -> Tuple[dict, int]:
    """Validate the areas of a layout and return brooks structure with errors"""
    violations = AreaHandler.validate_plan_classifications(
        plan_id=plan_id,
        area_id_to_area_type=areas,
        only_blocking=False,
    )

    return (
        jsonify(BrooksJSONEncoder.default({"errors": violations})),
        HTTPStatus.ACCEPTED,
    )


@areas_app.route("/plan/<int:plan_id>/areas")
class AreasView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @areas_app.response(schema=AreaDBSchema(many=True), status_code=HTTPStatus.OK)
    def get(self, plan_id: int):
        """Reads from the DB the areas classified for a given plan_id"""
        return jsonify(AreaDBHandler.find(plan_id=plan_id))

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @areas_app.arguments(
        PutAreasSchema,
        location="json",
        as_kwargs=True,
    )
    @areas_app.response(status_code=HTTPStatus.ACCEPTED)
    def put(self, plan_id: int, areas: Dict[int, str]):
        """Updates all the area types of a plan. Used in the classification tab of
        the pipeline.
        """
        violations = AreaHandler.put_new_classifications(
            plan_id=plan_id, areas_type_from_user=areas
        )
        return (
            jsonify(BrooksJSONEncoder.default({"errors": violations})),
            HTTPStatus.ACCEPTED,
        )
