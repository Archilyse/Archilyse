from collections import defaultdict
from http import HTTPStatus

from flask import jsonify
from flask_smorest import Blueprint
from marshmallow import Schema, fields

from brooks.classifications import CLASSIFICATIONS, ClassificationJSONEncoder
from brooks.util.projections import get_all_crs_proj4
from common_utils.constants import USER_ROLE
from slam_api.utils import role_access_control

constants_app = Blueprint("constants", "constants", description="Fetch constants")


class ProjectionsSchema(Schema):
    fields.List(fields.Dict(keys=fields.Str(), values=fields.Str()))


@constants_app.route("/classification_schemes", methods=["GET"])
@constants_app.response(status_code=HTTPStatus.OK)
def get_classification_schemes():
    return jsonify((x.name for x in CLASSIFICATIONS))


@constants_app.route(
    "/classification_schemes/<string:verbose_scheme_name>", methods=["GET"]
)
@constants_app.response(status_code=HTTPStatus.OK)
def get_classification_scheme(verbose_scheme_name: str):
    try:
        classification = CLASSIFICATIONS[verbose_scheme_name]
    except KeyError:
        return jsonify(), HTTPStatus.NOT_FOUND

    area_tree = ClassificationJSONEncoder.default(classification.value().area_tree)
    area_tree.pop("AreaType.KITCHEN_DINING", None)
    area_tree["SIACategory.HNF"]["children"] = [
        area_type
        for area_type in area_tree["SIACategory.HNF"]["children"]
        if area_type != "AreaType.KITCHEN_DINING"
    ]
    return area_tree


@constants_app.route("/projections")
@role_access_control(
    roles={
        USER_ROLE.TEAMMEMBER,
        USER_ROLE.TEAMLEADER,
        USER_ROLE.ARCHILYSE_ONE_ADMIN,
        USER_ROLE.DMS_LIMITED,
    }
)
@constants_app.response(schema=ProjectionsSchema, status_code=HTTPStatus.OK)
def get_projections():
    projections = get_all_crs_proj4()
    return jsonify(projections)


@constants_app.route(
    "/classification_area_filters/<string:verbose_scheme_name>", methods=["GET"]
)
@constants_app.response(status_code=HTTPStatus.OK)
def area_filters(verbose_scheme_name: str):
    from brooks.types import AREA_TYPE_USAGE

    try:
        classification = CLASSIFICATIONS[verbose_scheme_name]
    except KeyError:
        return jsonify(), HTTPStatus.NOT_FOUND

    unit_usage_to_area_types = defaultdict(list)
    for area_type, unit_usages in AREA_TYPE_USAGE.items():
        if area_type not in classification.value().area_types:
            continue

        for unit_usage in unit_usages:
            unit_usage_to_area_types[unit_usage.name].append(area_type.name)

    return jsonify(unit_usage_to_area_types)
