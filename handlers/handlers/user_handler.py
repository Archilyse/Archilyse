from typing import Optional, Union

from itsdangerous import BadData, URLSafeTimedSerializer

from common_utils.constants import (
    PASSWORD_RESET_TOKEN_EXPIRATION_TIME,
    get_security_password_salt,
    get_slam_secret_key,
)
from handlers.db import UserDBHandler


class UserHandler:
    # TODO: Add roles here and change Admin UI to decode jwt token
    JWT_FIELDS = ("id", "name", "group_id", "client_id")

    @classmethod
    def register_new_login(cls, user_id: int):
        return UserDBHandler.register_new_login(user_id=user_id)

    @classmethod
    def get_jwt_user_fields(cls, user: dict) -> dict:
        """Return the user fields that we want to share within the JWT"""
        return {field: user[field] for field in cls.JWT_FIELDS}

    @classmethod
    def generate_confirmation_token(cls, user_id: int):
        serializer = URLSafeTimedSerializer(get_slam_secret_key())
        return serializer.dumps(user_id, salt=get_security_password_salt())

    @classmethod
    def confirm_token(
        cls,
        token: str,
        expiration: Optional[int] = PASSWORD_RESET_TOKEN_EXPIRATION_TIME,
    ) -> Union[str, bool]:
        try:
            return URLSafeTimedSerializer(get_slam_secret_key()).loads(
                token, salt=get_security_password_salt(), max_age=expiration
            )
        except BadData:
            return False
