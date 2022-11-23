from http import HTTPStatus

from flask import jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from common_utils.constants import USER_ROLE
from common_utils.exceptions import ReactAnnotationMigrationException
from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import ReactPlannerSchema
from slam_api.utils import ensure_site_consistency, role_access_control

annotations_v2_app = Blueprint("annotations_v2", "annotations_v2")


@annotations_v2_app.errorhandler(ReactAnnotationMigrationException)
def handle_react_annotation_migration_exception(e):
    return jsonify(msg=str(e)), HTTPStatus.UNPROCESSABLE_ENTITY


class AnnotationsValidatedQuery(Schema):
    validated = fields.Boolean(required=False, dump_default=False)


class GetAnnotationsSchema(Schema):
    created = fields.DateTime()
    updated = fields.DateTime()
    data = ReactPlannerSchema()
    errors = fields.List(fields.Dict(), required=False)
    annotation_finished = fields.Boolean(required=False, dump_default=False)
    plan_id = fields.Integer()
    id = fields.Integer()


@annotations_v2_app.route("/plan/<int:plan_id>")
class PlanAnnotationV2View(MethodView):
    @role_access_control({USER_ROLE.ADMIN, USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @annotations_v2_app.arguments(
        AnnotationsValidatedQuery(), location="query", as_kwargs=True
    )
    @annotations_v2_app.response(
        schema=GetAnnotationsSchema(), status_code=HTTPStatus.OK
    )
    def get(self, plan_id: int, validated: bool = False):
        """Get annotations for plan"""
        from handlers import PlanHandler

        plan_handler = PlanHandler(plan_id=plan_id)
        react_planner_data = ReactPlannerHandler().get_plan_data_w_validation_errors(
            plan_info=plan_handler.plan_info, validated=validated
        )
        return jsonify(react_planner_data), HTTPStatus.OK

    @role_access_control({USER_ROLE.ADMIN, USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @annotations_v2_app.arguments(
        AnnotationsValidatedQuery(), location="query", as_kwargs=True
    )
    @annotations_v2_app.response(
        schema=GetAnnotationsSchema(), status_code=HTTPStatus.OK
    )
    def put(
        self,
        plan_id: int,
        validated: bool = False,
    ):
        react_planner_data = ReactPlannerHandler().store_plan_data(
            plan_id=plan_id, plan_data=request.json, validated=validated
        )
        return jsonify(react_planner_data), HTTPStatus.OK
