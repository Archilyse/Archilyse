from http import HTTPStatus
from typing import List

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from brooks.unit_layout_factory import UnitLayoutFactory
from common_utils.constants import USER_ROLE
from handlers import PlanLayoutHandler
from slam_api.utils import role_access_control

features_app = Blueprint("features", __name__)


@features_app.route("/<int:site_id>/<int:plan_id>/basic")
class FeaturesView(MethodView):
    @role_access_control(roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER})
    @features_app.arguments(
        Schema.from_dict({"areas_ids": fields.List(fields.List(fields.Int()))}),
        location="json",
        as_kwargs=True,
    )
    @features_app.arguments(
        Schema.from_dict({"scaled": fields.Boolean(required=False)}),
        location="querystring",
        as_kwargs=True,
    )
    @features_app.response(status_code=HTTPStatus.OK)
    def post(
        self,
        site_id: int,
        plan_id: int,
        areas_ids: List[List[int]],
        scaled: bool = True,
    ):
        from simulations.basic_features import CustomValuatorBasicFeatures2

        plan_layout = PlanLayoutHandler(plan_id=plan_id).get_layout(
            scaled=scaled, classified=True, deep_copied=False
        )
        db_area_id_to_brooks_space = {
            area.db_area_id: space.id
            for space in plan_layout.spaces
            for area in space.areas
            if area.db_area_id is not None
        }
        result = []
        for area_ids in areas_ids:
            unit_layout = UnitLayoutFactory(plan_layout=plan_layout).create_sub_layout(
                spaces_ids={
                    db_area_id_to_brooks_space[db_area_id]
                    for db_area_id in area_ids
                    if db_area_id in db_area_id_to_brooks_space
                },
                area_db_ids=set(
                    [
                        area_id
                        for area_id in area_ids
                        if area_id in db_area_id_to_brooks_space
                    ]
                ),
            )
            basic_features_service = CustomValuatorBasicFeatures2()
            nbr_of_rooms = basic_features_service.number_of_rooms(layouts=[unit_layout])
            sia416_dimensions = basic_features_service.add_sia_dimension_prefix(
                sia_dimensions=basic_features_service.sia_dimensions(
                    layouts=[unit_layout]
                )
            )
            net_area = basic_features_service.net_area(layouts=[unit_layout])
            result.append(
                dict(
                    (
                        *nbr_of_rooms,
                        *sia416_dimensions.items(),
                        *tuple(net_area.items()),
                    )
                )
            )

        return jsonify(result)
