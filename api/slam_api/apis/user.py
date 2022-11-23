import logging
from http import HTTPStatus
from typing import Dict

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint
from marshmallow import Schema, fields, validate

from common_utils.constants import DMS_PERMISSION, USER_ROLE
from common_utils.exceptions import DBNotFoundException, UserAuthorizationException
from db_models import ClientDBModel, UserDBModel
from handlers import DmsPermissionHandler, UserHandler
from handlers.db import UserDBHandler
from handlers.db.dms_permission_handler import DmsPermissionDBSchema
from handlers.db.user_handler import UserDBSchema
from slam_api.entity_ownership_validation import validate_entity_ownership
from slam_api.serialization import CapitalizedStr
from slam_api.utils import get_user_authorized, role_access_control
from tasks.mail_tasks import send_email_task
from tasks.utils.constants import EmailTypes

logger = logging.getLogger()

user_app = Blueprint("user", __name__)


class UserRoleSchema(Schema):
    role = fields.Str()


class EmailSchema(Schema):
    email = fields.Email()


# TODO: Ideally we should use `UserDBSchema`, serializing `roles` properly
class UserSchema(Schema):
    client_id = fields.Int()
    group_id = fields.Int()
    name = fields.Str()
    login = fields.Str()
    password = fields.Str()
    roles = fields.List(CapitalizedStr())
    email = fields.Email()
    email_validated = fields.Boolean()


def ensure_allowed_to_create_update_user(request_user: Dict, new_data: Dict):
    if USER_ROLE.ARCHILYSE_ONE_ADMIN in request_user["roles"]:
        if "roles" in new_data and not all(
            [
                USER_ROLE[role]
                in (USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED)
                for role in new_data["roles"]
            ]
        ):
            raise UserAuthorizationException(
                "Requesting User is not allowed to create/update a user with the provided roles"
            )

        if (
            "client_id" in new_data
            and not request_user["client_id"] == new_data["client_id"]
        ):
            raise UserAuthorizationException(
                "Requesting User is not allowed to create/update a user for this client"
            )


def fallback_client_id_requesting_user(requesting_user: Dict, **kwargs) -> Dict:
    if "client_id" not in kwargs and USER_ROLE.ADMIN not in requesting_user["roles"]:
        kwargs["client_id"] = get_user_authorized()["client_id"]

    return kwargs


@user_app.route("/")
class UserViewCollection(MethodView):
    @user_app.arguments(
        Schema.from_dict({"client_id": fields.Int(required=False)}),
        location="query",
        as_kwargs=True,
    )
    @user_app.response(schema=UserDBSchema(many=True), status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN})
    @validate_entity_ownership(
        ClientDBModel,
        lambda kwargs: {"id": kwargs["client_id"]} if "client_id" in kwargs else {},
    )
    def get(self, **kwargs):
        kwargs = fallback_client_id_requesting_user(
            requesting_user=get_user_authorized(), **kwargs
        )
        users = UserDBHandler.find(**kwargs)
        return jsonify(users)

    @user_app.arguments(UserSchema, location="json", as_kwargs=True)
    @user_app.response(schema=UserDBSchema, status_code=HTTPStatus.CREATED)
    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN})
    def post(self, **kwargs):
        ensure_allowed_to_create_update_user(
            request_user=get_user_authorized(), new_data=kwargs
        )
        new_user = UserDBHandler.add(**kwargs)
        if any(
            role in (USER_ROLE.ARCHILYSE_ONE_ADMIN.name, USER_ROLE.DMS_LIMITED.name)
            for role in kwargs["roles"]
        ):
            send_email_task.delay(
                user_id=new_user["id"], email_type=EmailTypes.ACTIVATION_EMAIL.name
            )
        return jsonify(new_user), HTTPStatus.CREATED


@user_app.route("/<int:user_id>")
class UserView(MethodView):
    @user_app.response(schema=UserDBSchema, status_code=HTTPStatus.OK)
    @role_access_control(
        roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN},
        allow_user_id_field="user_id",
    )
    @validate_entity_ownership(UserDBModel, lambda kwargs: {"id": kwargs["user_id"]})
    def get(self, user_id: int):
        user = UserDBHandler.get_by(id=user_id)
        return jsonify(user), HTTPStatus.OK

    @user_app.arguments(UserSchema, location="json", as_kwargs=True)
    @user_app.response(schema=UserDBSchema, status_code=HTTPStatus.OK)
    @role_access_control(
        roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN},
        allow_user_id_field="user_id",
    )
    @validate_entity_ownership(UserDBModel, lambda kwargs: {"id": kwargs["user_id"]})
    def put(self, user_id: int, **kwargs):
        user = get_user_authorized()
        if (
            USER_ROLE.ADMIN not in user["roles"]
            and USER_ROLE.ARCHILYSE_ONE_ADMIN not in user["roles"]
            and set(kwargs) - {"email", "password"}
        ):
            return (
                jsonify(msg="Trying to update read-only fields."),
                HTTPStatus.FORBIDDEN,
            )

        ensure_allowed_to_create_update_user(request_user=user, new_data=kwargs)
        updated_user = UserDBHandler.update(dict(id=user_id), new_values=kwargs)
        return jsonify(updated_user), HTTPStatus.OK

    @user_app.response(status_code=HTTPStatus.NO_CONTENT)
    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN})
    @validate_entity_ownership(UserDBModel, lambda kwargs: {"id": kwargs["user_id"]})
    def delete(self, user_id: int):
        UserDBHandler.delete({"id": user_id})


@user_app.route("/role")
class UserRolesCollection(MethodView):
    @user_app.response(schema=UserRoleSchema(many=True), status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self):
        return [{"role": r.name} for r in USER_ROLE]


class UserPasswordSchema(Schema):
    password = fields.String(load_only=True)
    token = fields.String(load_only=True)


@user_app.route("/reset_password")
class UserChangePassword(MethodView):
    @user_app.arguments(UserPasswordSchema, location="json", as_kwargs=True)
    @user_app.response(schema=UserDBSchema, status_code=HTTPStatus.OK)
    def put(self, token: str, password: str):
        """This endpoint doesn't require authorization but can only be accessed using the email token"""
        if user_id_in_token := UserHandler.confirm_token(token=token):
            user_updated = UserDBHandler.update(
                item_pks={"id": user_id_in_token},
                new_values={"password": password, "email_validated": True},
            )
            return jsonify(user_updated), HTTPStatus.OK
        else:
            return (
                jsonify(msg="Token has expired or is not valid anymore"),
                HTTPStatus.FORBIDDEN,
            )


@user_app.route("/forgot_password")
class UserForgottenPassword(MethodView):
    @user_app.arguments(EmailSchema, location="json", as_kwargs=True)
    @user_app.response(schema=UserDBSchema, status_code=HTTPStatus.OK)
    def put(self, email: str):
        """This endpoint doesn't require authorization"""
        try:
            user = UserDBHandler.get_by(email=email)
            send_email_task.delay(
                user_id=user["id"], email_type=EmailTypes.PASSWORD_RESET.name
            )
        except DBNotFoundException:
            # If the user doesn't exist we are pretending the email has been sent?
            pass
        return (
            jsonify(
                msg="Successfully sent password reset email to the provided address"
            ),
            HTTPStatus.OK,
        )


@user_app.route("/dms")
class DMSUserViewCollection(MethodView):
    @user_app.response(
        schema=DmsPermissionDBSchema(many=True), status_code=HTTPStatus.OK
    )
    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN})
    def get(self):

        permissions = DmsPermissionHandler.get_all_permissions_of_client(
            client_id=get_user_authorized()["client_id"]
        )

        return jsonify(permissions), HTTPStatus.OK


@user_app.route("/dms/<int:user_id>")
class DMSUserView(MethodView):
    @user_app.arguments(
        Schema.from_dict(
            {
                "rights": fields.Str(
                    validate=validate.OneOf([x.name for x in DMS_PERMISSION])
                ),
                "site_id": fields.Int(required=False),
            }
        )(many=True),
        location="json",
    )
    @user_app.response(schema=DmsPermissionDBSchema, status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN})
    def put(self, data: Dict, user_id: int):
        DmsPermissionHandler.put_permissions(
            user_id=user_id, data=data, requesting_user=get_user_authorized()
        )

        return jsonify(msg="successfully inserted permissions"), HTTPStatus.OK
