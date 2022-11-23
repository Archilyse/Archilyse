from http import HTTPStatus

from flask import jsonify, request
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema

from common_utils.constants import USER_ROLE
from db_models import ClientDBModel
from handlers.db import ClientDBHandler
from handlers.db.client_handler import ClientDBSchema
from slam_api.entity_ownership_validation import validate_entity_ownership
from slam_api.utils import get_user_authorized, role_access_control

client_app = Blueprint("client", __name__)


class ClientPutSchema(Schema.from_dict(ClientDBSchema().fields)):  # type: ignore
    pass


@client_app.route("/")
class ClientsCollectionView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
        }
    )
    @client_app.response(schema=ClientDBSchema(many=True), status_code=HTTPStatus.OK)
    def get(self):
        user = get_user_authorized()
        if client_id := user["client_id"]:
            return jsonify([ClientDBHandler.get_by(id=client_id)]), HTTPStatus.OK
        return jsonify(ClientDBHandler.find()), HTTPStatus.OK

    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER})
    @client_app.response(schema=ClientDBSchema, status_code=HTTPStatus.OK)
    def post(self):
        from handlers import ClientHandler

        values = request.get_json(force=True)
        new_client = ClientDBHandler.add(**values)
        ClientHandler().create_bucket_if_not_exists(client_id=new_client["id"])
        return jsonify(new_client), HTTPStatus.CREATED


@client_app.route("/<int:client_id>")
class ClientsView(MethodView):
    @role_access_control(
        roles={
            USER_ROLE.TEAMMEMBER,
            USER_ROLE.TEAMLEADER,
            USER_ROLE.ARCHILYSE_ONE_ADMIN,
            USER_ROLE.DMS_LIMITED,
            USER_ROLE.COMPETITION_ADMIN,
            USER_ROLE.COMPETITION_VIEWER,
        }
    )
    @validate_entity_ownership(
        ClientDBModel, lambda kwargs: {"id": kwargs["client_id"]}
    )
    @client_app.response(schema=ClientDBSchema, status_code=HTTPStatus.OK)
    def get(self, client_id: int):
        client = ClientDBHandler.get_by(id=client_id)
        return jsonify(client), HTTPStatus.OK

    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.TEAMLEADER})
    @client_app.arguments(schema=ClientPutSchema(partial=True), as_kwargs=True)
    @client_app.response(schema=ClientDBSchema(partial=True), status_code=HTTPStatus.OK)
    def put(self, client_id: int, **kwargs):
        updated_client = ClientDBHandler.update(dict(id=client_id), new_values=kwargs)
        return jsonify(updated_client), HTTPStatus.OK

    @role_access_control(roles={USER_ROLE.ADMIN})
    def delete(self, client_id: int):
        ClientDBHandler.delete({"id": client_id})
        return jsonify({}), HTTPStatus.NO_CONTENT
