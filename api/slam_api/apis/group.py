from http import HTTPStatus

from flask import jsonify
from flask_smorest import Blueprint

from common_utils.constants import USER_ROLE
from handlers.db import GroupDBHandler
from handlers.db.group_handler import GroupDBSchema
from slam_api.utils import role_access_control

group_app = Blueprint("groups", __name__)


@group_app.route("/", methods=["GET"])
@role_access_control(
    roles={USER_ROLE.TEAMMEMBER, USER_ROLE.TEAMLEADER, USER_ROLE.ARCHILYSE_ONE_ADMIN}
)
@group_app.response(schema=GroupDBSchema(many=True), status_code=HTTPStatus.OK)
def get_groups():
    return jsonify(GroupDBHandler.find())
