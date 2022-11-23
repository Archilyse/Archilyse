import io
from collections import defaultdict
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Tuple

from flask import jsonify, send_file
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import EXCLUDE, Schema, ValidationError, fields
from marshmallow import validate as ma_validate
from marshmallow import validates_schema
from shapely.geometry import mapping as shapely_mapping

from brooks.util.io import BrooksJSONEncoder
from brooks.util.projections import project_geometry
from common_utils.constants import REGION, USER_ROLE
from common_utils.exceptions import (
    DBValidationException,
    GCloudMissingBucketException,
    NoClassifierAvailableException,
)
from db_models import PlanDBModel
from handlers import FloorHandler, PlanHandler, PlanLayoutHandler
from handlers.create_area_splitter_for_kitchen import (
    CreateAreaSplittersFromKitchenElements,
)
from handlers.db import PlanDBHandler, SiteDBHandler, UnitAreaDBHandler, UnitDBHandler
from handlers.db.plan_handler import PlanDBSchema
from handlers.db.serialization.geojson import GeoJsonPolygonSchema, LayoutSchema
from handlers.db.unit_handler import UnitDBSchema
from handlers.editor_v2 import ReactPlannerHandler
from handlers.plan_handler import PipelineCriteriaSchema, PipelineSchema
from handlers.validators import PlanOverlapValidator
from slam_api.dms_views.entity_view import dms_limited_entity_view
from slam_api.utils import ensure_site_consistency, eventstream, role_access_control

plan_app = Blueprint("plan", __name__)


@plan_app.route("/<int:plan_id>")
class PlanView(MethodView):

    georef_args = {
        "georef_x",
        "georef_y",
        "georef_rot_angle",
    }

    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
        }
    )
    @plan_app.response(schema=PlanDBSchema(many=False), status_code=HTTPStatus.OK)
    def get(self, plan_id: int) -> Tuple[dict, HTTPStatus]:
        plan = PlanDBHandler.get_by(id=plan_id)
        return jsonify(plan)

    class PlanPatchSchema(Schema):
        georef_x = fields.Float(
            required=False,
            validate=ma_validate.Range(
                min=-180, max=180, min_inclusive=True, max_inclusive=True
            ),
        )
        georef_y = fields.Float(
            required=False,
            validate=ma_validate.Range(
                min=-90, max=90, min_inclusive=True, max_inclusive=True
            ),
        )
        georef_rot_angle = fields.Float(required=False)
        georef_scale = fields.Float(required=False)
        without_units = fields.Boolean(required=False, dump_default=False)
        is_masterplan = fields.Boolean(required=False)

        @validates_schema
        def validate_all_georef_fields_or_scale(self, data, **kwargs):
            """Raises a validation exception if only some fields for georeferencing are present.
            Scale can be passed alone"""
            if common_args := PlanView.georef_args & set(data.keys()):
                if common_args != PlanView.georef_args:
                    raise ValidationError(
                        f"Updating georeferencing should contain all the arguments: {PlanView.georef_args}"
                    )

            if not data:
                raise ValidationError("There should be at least a field defined")

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @plan_app.arguments(
        PlanPatchSchema(),
        location="json",
    )
    @plan_app.response(schema=PlanDBSchema(many=False), status_code=HTTPStatus.OK)
    def patch(self, plan_data: Dict[str, float], plan_id: int):
        return jsonify(
            PlanDBHandler.update(item_pks={"id": plan_id}, new_values=plan_data)
        )

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    def delete(self, plan_id: int):
        PlanDBHandler.delete(item_pk={"id": plan_id})
        return jsonify(), HTTPStatus.OK


@plan_app.route("/<int:plan_id>/brooks", methods=["GET"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
@plan_app.arguments(
    Schema.from_dict(
        {
            "classified": fields.Boolean(required=False, dump_default=False),
            "validate": fields.Boolean(required=False, dump_default=False),
            "postprocessed": fields.Boolean(required=False, dump_default=False),
        }
    ),
    location="querystring",
    as_kwargs=True,
)
@plan_app.response(status_code=HTTPStatus.OK)
def get_plan_layout_unscaled_for_pipeline(
    plan_id: int,
    classified: bool = False,
    validate: bool = False,
    postprocessed: bool = False,
) -> Tuple[dict, HTTPStatus]:
    try:
        layout = PlanLayoutHandler(plan_id=plan_id).get_layout(
            validate=validate,
            classified=classified,
            scaled=False,
            postprocessed=postprocessed,
            deep_copied=False,
        )
        return jsonify(layout.asdict())
    except NoClassifierAvailableException as e:
        return jsonify(msg=str(e))


@plan_app.route("/<int:plan_id>/brooks/simple", methods=["GET"])
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
        USER_ROLE.COMPETITION_VIEWER,
        USER_ROLE.COMPETITION_ADMIN,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
@plan_app.response(schema=LayoutSchema, status_code=HTTPStatus.OK)
def get_simple_brooks_model_api(
    plan_id: int,
):
    layout = PlanLayoutHandler(plan_id=plan_id).get_layout(
        validate=False,
        scaled=True,
        classified=True,
        georeferenced=True,
        deep_copied=False,
    )
    return jsonify(
        layout.to_lat_lon_json(
            from_region=REGION[PlanHandler(plan_id=plan_id).site_info["georef_region"]]
        )
    )


@plan_app.route("/<int:plan_id>/georeferencing", methods=["PUT"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
@plan_app.arguments(
    Schema.from_dict(
        {
            "georef_rot_angle": fields.Float(required=True),
            "georef_x": fields.Float(required=True),
            "georef_y": fields.Float(required=True),
        }
    ),
    location="json",
    as_kwargs=True,
)
@plan_app.response(status_code=HTTPStatus.OK)
def save_georeferencing_data(plan_id: int, **georef_data):
    PlanHandler(plan_id=plan_id).save_georeference_data(georef_data=georef_data)
    return jsonify(HTTPStatus.OK)


@plan_app.route("/<int:plan_id>/georeferencing/footprint", methods=["GET"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
@plan_app.response(schema=GeoJsonPolygonSchema(many=False), status_code=HTTPStatus.OK)
def get_footprint_api(plan_id: int):
    footprint = PlanLayoutHandler(plan_id=plan_id).get_georeferenced_footprint()
    return shapely_mapping(
        project_geometry(
            geometry=footprint,
            crs_from=REGION[PlanHandler(plan_id=plan_id).site_info["georef_region"]],
            crs_to=REGION.LAT_LON,
        )
    )


@plan_app.route("/<int:plan_id>/georeferencing/footprints_site", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@plan_app.response(schema=GeoJsonPolygonSchema(many=True), status_code=HTTPStatus.OK)
def get_georeferenced_plans_under_same_site(plan_id: int):
    plans_georeferenced = PlanHandler(
        plan_id=plan_id
    ).get_other_georeferenced_footprints_under_same_site()
    return jsonify({"data": list(plans_georeferenced)})


@plan_app.route(
    "/<int:plan_id>/georeferencing/footprints_site/eventstream", methods=["GET"]
)
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@plan_app.response(schema=GeoJsonPolygonSchema(many=True), status_code=HTTPStatus.OK)
def get_georeferenced_plans_under_same_site_eventstream(plan_id: int):
    return eventstream(
        PlanHandler(
            plan_id=plan_id
        ).get_other_georeferenced_footprints_under_same_site()
    )


@plan_app.route("/<int:plan_id>/georeferencing/validate", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
def validate_georeferencing(plan_id: int):
    return jsonify(
        {
            "data": [
                violation.text
                for violation in PlanOverlapValidator(plan_id=plan_id).validate()
            ]
        }
    )


@plan_app.route("/<int:plan_id>/status", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@plan_app.response(schema=PipelineCriteriaSchema(many=False), status_code=HTTPStatus.OK)
def get_plan_status(plan_id: int):
    """Used to manage the user tabs in the Pipeline UI"""
    status = PlanHandler(plan_id=plan_id).pipeline_completed_criteria()
    return jsonify(status)


@plan_app.route("/<int:plan_id>/raw_image", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
def get_plan_raw_image(plan_id: int):
    """At the moment used for the pipeline background image"""
    plan_handler = PlanHandler(plan_id=plan_id)
    try:
        return send_file(
            io.BytesIO(plan_handler.get_plan_image_as_bytes()),
            mimetype=plan_handler.plan_info["image_mime_type"],
            as_attachment=True,
            attachment_filename=f"{plan_id}.{plan_handler.plan_info['image_mime_type']}",
        )
    except GCloudMissingBucketException as e:
        return jsonify(msg=str(e)), HTTPStatus.NOT_FOUND


@plan_app.route("/<int:plan_id>/pipeline", methods=["GET"])
@role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
@plan_app.response(schema=PipelineSchema(many=False), status_code=HTTPStatus.OK)
def get_plan_pipeline(plan_id: int):
    plans = [PlanDBHandler.get_by(id=plan_id)]
    site = SiteDBHandler.get_by(id=plans[0]["site_id"])
    result = PlanHandler.get_pipelines_output(plans=plans, site=site)
    return jsonify(result)


@plan_app.route("/<int:plan_id>/units")
class PlanUnitsView(MethodView):
    class PlanUnitDBSchema(UnitDBSchema):
        area_ids = fields.List(fields.Int())
        unit_usage = fields.Str(required=True)
        created = fields.Str()
        updated = fields.Str()

    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
        }
    )
    @plan_app.arguments(
        Schema.from_dict({"floor_id": fields.Int(required=False)}),
        location="querystring",
        as_kwargs=True,
    )
    @dms_limited_entity_view(db_model=PlanDBModel)
    @plan_app.response(schema=PlanUnitDBSchema(many=True), status_code=HTTPStatus.OK)
    def get(self, plan_id: int, floor_id: Optional[int] = None) -> List[Dict]:
        find_args = {"plan_id": plan_id}
        if floor_id is not None:
            find_args["floor_id"] = floor_id
        units = UnitDBHandler.find(
            **find_args,
            output_columns=[
                "id",
                "site_id",
                "floor_id",
                "client_id",
                "plan_id",
                "apartment_no",
                "gcs_de_floorplan_link",
                "unit_usage",
            ],
        )

        unit_areas = UnitAreaDBHandler.find_in(unit_id=[unit["id"] for unit in units])
        unit_areas_index = defaultdict(list)
        for unit_area in unit_areas:
            unit_areas_index[unit_area["unit_id"]].append(unit_area["area_id"])

        for unit in units:
            unit["area_ids"] = unit_areas_index[unit["id"]]

        return jsonify(units)

    class UnitIdClientIDSchema(Schema):
        id = fields.Int(required=True)
        client_id = fields.Str(required=True)
        unit_usage = fields.Str(required=True)

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @plan_app.arguments(
        UnitIdClientIDSchema(many=True, unknown=EXCLUDE),
        location="json",
    )
    @plan_app.response(
        schema=UnitIdClientIDSchema(many=True), status_code=HTTPStatus.OK
    )
    def put(self, unit_list: List[Dict[str, Any]], **kwargs) -> Tuple[Any, int]:
        from handlers.validators.linking.unit_linking_validator import (
            UnitLinkingValidator,
        )

        violations = [
            violation
            for violations in UnitLinkingValidator.violations_by_unit_client_id(
                plan_id=kwargs["plan_id"], unit_list=unit_list
            ).values()
            for violation in violations
        ]

        if violations:
            return (
                jsonify(BrooksJSONEncoder.default({"errors": violations})),
                HTTPStatus.BAD_REQUEST,
            )

        UnitDBHandler.bulk_update(
            client_id={x["id"]: x["client_id"] for x in unit_list},
            unit_usage={x["id"]: x["unit_usage"] for x in unit_list},
        )
        return unit_list, HTTPStatus.OK


class HeightsSchema(Schema):
    default_wall_height = fields.Float(
        required=True, validate=ma_validate.Range(min=0, max=10)
    )
    default_door_height = fields.Float(
        required=True, validate=ma_validate.Range(min=0, max=10)
    )
    default_window_lower_edge = fields.Float(
        required=True, validate=ma_validate.Range(min=0, max=10)
    )
    default_window_upper_edge = fields.Float(
        required=True, validate=ma_validate.Range(min=0, max=10)
    )
    default_ceiling_slab_height = fields.Float(
        required=True, validate=ma_validate.Range(min=0, max=1)
    )

    @validates_schema
    def validate_heights(self, data, **kwargs):
        if data.get("default_door_height") >= data.get("default_wall_height"):
            raise ValidationError("door height must be smaller than wall height.")

        if data.get("default_window_upper_edge") >= data.get("default_wall_height"):
            raise ValidationError("upper window edge must be smaller than wall height.")

        if data.get("default_window_upper_edge") <= data.get(
            "default_window_lower_edge"
        ):
            raise ValidationError(
                "lower window edge must be smaller than upper window edge."
            )


@plan_app.route("/<int:plan_id>/heights", methods=["PATCH"])
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
    }
)
@plan_app.arguments(
    HeightsSchema,
    location="json",
    as_kwargs=True,
)
def patch_plan_heights(plan_id: int, **heights: Dict[str, float]):
    return jsonify(PlanDBHandler.update(item_pks={"id": plan_id}, new_values=heights))


@plan_app.route("/<int:plan_id>/masterplan", methods=["PUT"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
def set_as_masterplan(plan_id: int):
    PlanHandler(plan_id=plan_id).set_as_masterplan()
    return jsonify(HTTPStatus.OK)


@plan_app.route("/<int:plan_id>/area_splitters", methods=["GET"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
def create_area_splitters(plan_id: int):
    new_data = CreateAreaSplittersFromKitchenElements.create_and_add_area_splitters_to_react_data(
        plan_id=plan_id
    )
    return jsonify(new_data), HTTPStatus.OK


@plan_app.route("/<int:plan_id>/image_transformation", methods=["GET"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
def get_image_transformation(plan_id: int):
    transformation = ReactPlannerHandler().get_image_transformation(plan_id=plan_id)
    return jsonify(transformation), HTTPStatus.OK


class FloorsRangeSchema(Schema):
    floor_lower_range = fields.Integer(required=True)
    floor_upper_range = fields.Integer(
        required=False, dump_default=None, allow_none=True
    )

    @validates_schema
    def validate_range(self, data, **kwargs):
        if "floor_upper_range" in data and int(data["floor_upper_range"]) < int(
            data["floor_lower_range"]
        ):
            raise ValidationError(
                "floor_lower_range should not be higher than floor_upper_range",
                "floor_lower_range",  # name of field to report error for
            )


@plan_app.route("/<int:plan_id>/floors")
class PlanFloorsView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @plan_app.arguments(
        FloorsRangeSchema,
        location="json",
        as_kwargs=True,
    )
    def put(self, plan_id: int, **range_data):
        requested_floor_numbers = FloorHandler.get_floor_numbers_from_floor_range(
            **range_data
        )
        try:
            final_floors = FloorHandler.upsert_floor_numbers(
                plan_id=plan_id,
                building_id=PlanDBHandler.get_by(id=plan_id)["building_id"],
                floor_numbers=requested_floor_numbers,
            )
            return jsonify(final_floors), HTTPStatus.CREATED
        except DBValidationException as e:
            return (
                jsonify(msg=str(e)),
                HTTPStatus.BAD_REQUEST,
            )
