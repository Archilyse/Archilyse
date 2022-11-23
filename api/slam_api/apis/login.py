from http import HTTPStatus

from flask import jsonify, make_response
from flask.views import MethodView
from flask_jwt_extended import create_access_token, set_access_cookies
from flask_smorest import Blueprint

from common_utils.logger import logger
from handlers import UserHandler
from handlers.db import UserDBHandler
from slam_api.apis.potential.openapi.documentation import (
    post_auth_request,
    post_auth_response,
    unprocessable_entity_response,
    wrong_credentials_response,
)

login_app = Blueprint("Auth", "Auth")


@login_app.route("/login", methods=["POST"])
class Login(MethodView):
    @login_app.response(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY, **unprocessable_entity_response
    )
    @login_app.response(
        status_code=HTTPStatus.UNAUTHORIZED, **wrong_credentials_response
    )
    @login_app.response(status_code=HTTPStatus.OK, **post_auth_response)
    @login_app.arguments(**post_auth_request)
    def post(self, credentials: dict):
        """Authenticate the user.

        Provides the bearer token on successful verification of user credentials.
        """
        user = UserDBHandler.get_user_password_verified(
            user=credentials["user"], password=credentials["password"]
        )
        if not user:
            return jsonify({"msg": "Wrong credentials"}), HTTPStatus.UNAUTHORIZED

        UserHandler.register_new_login(user_id=user["id"])

        # JWT have a public section that can be access by any JWT lib (FE or BE)
        # so we could use some of the user data in FE avoiding extra call to BE
        # also we need to be able to expire and refresh tokens
        # Use this to debug (https://jwt.io/#debugger-io)
        identity = UserHandler.get_jwt_user_fields(user)
        access_token = create_access_token(identity=identity)
        logger.info(f'User {credentials["user"]} logged successfully')
        resp = make_response(
            jsonify(
                {
                    "msg": f"Logged in as {user['name']}",
                    "access_token": access_token,
                    "roles": [r.name for r in user["roles"]],
                }
            ),
            HTTPStatus.OK,
        )
        set_access_cookies(response=resp, encoded_access_token=access_token)

        return resp
