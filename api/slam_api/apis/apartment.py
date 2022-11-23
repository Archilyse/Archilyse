from http import HTTPStatus
from typing import List, Optional

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, ValidationError, fields, validate

from brooks.util.io import BrooksJSONEncoder
from common_utils.constants import USER_ROLE
from connectors.db_connector import get_db_session_scope
from handlers import PlanHandler, UnitHandler
from handlers.area_handler import AreaHandler
from handlers.db import (
    AreaDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from handlers.db.unit_handler import UnitDBSchema
from slam_api.utils import ensure_site_consistency, role_access_control

apartments_app = Blueprint("apartments", __name__)


@apartments_app.route("/plan/<int:plan_id>/apartment")
class ApartmentViewCollection(MethodView):
    @apartments_app.response(schema=UnitDBSchema(many=True), status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    def get(self, plan_id: int):
        apartments = UnitDBHandler.find(
            plan_id=plan_id,
            output_columns=[
                "id",
                "plan_id",
                "site_id",
                "floor_id",
                "apartment_no",
                "unit_type",
            ],
        )
        if not apartments:
            return jsonify(), HTTPStatus.NOT_FOUND

        unit_areas = list(
            UnitAreaDBHandler.find_in(
                unit_id=[apartment["id"] for apartment in apartments]
            )
        )
        for apartment in apartments:
            apartment["area_ids"] = [
                unit_area["area_id"]
                for unit_area in unit_areas
                if unit_area["unit_id"] == apartment["id"]
            ]

        return jsonify(apartments)


@apartments_app.route("/plan/<int:plan_id>/autosplit")
class ApartmentSplitViewCollection(MethodView):
    @role_access_control({USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @apartments_app.response(schema=UnitDBSchema(many=True), status_code=HTTPStatus.OK)
    def get(self, plan_id: int):
        plan = PlanDBHandler.get_by(id=plan_id)
        floors = FloorDBHandler.find(plan_id=plan_id)
        units = UnitDBHandler.find(
            plan_id=plan_id,
            output_columns=["id", "site_id", "plan_id", "floor_id", "apartment_no"],
        )

        units_by_floor_id_and_apartment_no = {
            (unit["floor_id"], unit["apartment_no"]): unit for unit in units
        }

        new_apartments, synced_apartments = UnitHandler.get_synced_apartments(
            plan_id=plan_id, apartment_area_ids=PlanHandler(plan_id=plan_id).autosplit()
        )

        new_units = [
            {
                "site_id": plan["site_id"],
                "plan_id": floor["plan_id"],
                "floor_id": floor["id"],
                "apartment_no": apartment_no,
                "area_ids": area_ids,
            }
            for apartment_no, area_ids in new_apartments.items()
            for floor in floors
        ]

        synced_units = [
            {
                **units_by_floor_id_and_apartment_no[(floor["id"], apartment_no)],
                "area_ids": area_ids,
            }
            for apartment_no, area_ids in synced_apartments.items()
            for floor in floors
        ]

        return jsonify(new_units + synced_units)


def areas_must_exist_in_db(area_ids: List[int]):
    db_area_ids = {
        area["id"] for area in AreaDBHandler.find_in(id=area_ids, output_columns=["id"])
    }
    if not set(area_ids).issubset(db_area_ids):
        raise ValidationError("Area ids selected do not exist anymore")


@apartments_app.route("/plan/<int:plan_id>/apartment/<int:apartment_no>")
class ApartmentView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @apartments_app.response(schema=UnitDBSchema(many=True), status_code=HTTPStatus.OK)
    def get(self, plan_id: int, apartment_no: int):
        return jsonify(
            UnitDBHandler.find(
                plan_id=plan_id,
                apartment_no=apartment_no,
                output_columns=["id", "plan_id", "site_id", "floor_id", "apartment_no"],
            )
        )

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @apartments_app.response(status_code=HTTPStatus.CREATED)
    def delete(self, plan_id: int, apartment_no: int):
        units = UnitDBHandler.find(plan_id=plan_id, apartment_no=apartment_no)
        for unit in units:
            UnitDBHandler.delete(item_pk=dict(id=unit["id"]))
        return jsonify(), HTTPStatus.ACCEPTED

    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @ensure_site_consistency()
    @apartments_app.arguments(
        Schema.from_dict(
            {
                "area_ids": fields.List(
                    fields.Int(),
                    required=True,
                    validate=[validate.Length(min=1), areas_must_exist_in_db],
                ),
                "unit_type": fields.String(allow_none=True),
            }
        ),
        location="json",
        as_kwargs=True,
    )
    @apartments_app.response(
        schema=Schema.from_dict({"data": fields.Nested(UnitDBSchema, many=True)}),
        status_code=HTTPStatus.ACCEPTED,
    )
    def put(
        self,
        plan_id: int,
        apartment_no: int,
        area_ids: List[int],
        unit_type: Optional[str] = None,
    ):
        """Creates the units based on a selection of area ids for every floor linked to the plan.
        If apartment_no already exists for this plan, it is overridden.
        """
        unit_handler = UnitHandler()
        # TODO: move the apartment accessible check to the annotation validations once the automatic splitting
        #  is working

        violations = unit_handler.validate_unit_given_area_ids(
            plan_id=plan_id, new_area_ids=area_ids, apartment_no=apartment_no
        )
        if violations:
            return (
                jsonify(BrooksJSONEncoder.default({"errors": violations})),
                HTTPStatus.BAD_REQUEST,
            )

        with get_db_session_scope():
            units = unit_handler.bulk_upsert_units(
                plan_id=plan_id,
                apartment_no=apartment_no,
                unit_type=unit_type,
            )
            AreaHandler.update_relationship_with_units(
                plan_id=plan_id,
                apartment_no=apartment_no,
                area_ids=area_ids,
            )
        return jsonify(data=[units]), HTTPStatus.ACCEPTED


@apartments_app.route("/floor/<int:floor_id>/autolinking")
class ApartmentLinkingViewCollection(MethodView):
    @role_access_control({USER_ROLE.ADMIN})
    @apartments_app.response(
        schema=Schema.from_dict(
            {
                "unit_id": fields.Int(required=True),
                "unit_client_id": fields.Str(required=True),
            }
        )(many=True),
        status_code=HTTPStatus.OK,
    )
    def get(self, floor_id: int):
        from handlers import AutoUnitLinkingHandler

        floor = FloorDBHandler.get_by(id=floor_id)
        return AutoUnitLinkingHandler(building_id=floor["building_id"]).unit_linking(
            floor_id=floor_id
        )
