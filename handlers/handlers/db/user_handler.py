from typing import Set

import pendulum
from marshmallow import fields

from common_utils.constants import USER_ROLE
from common_utils.exceptions import UserAuthorizationException
from db_models import UserDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema
from handlers.db.serialization.custom_fields import custom_field


class UserDBSchema(BaseDBSchema):
    password = fields.Field(load_only=True)

    class Meta(BaseDBSchema.Meta):
        model = UserDBModel
        exclude = ("group",)

    last_login = custom_field(
        field_type=fields.DateTime,
        attribute="last_login",
        load_deserialized=True,
        format="%Y-%m-%d %H:%M:%S",
    )
    email = fields.Email()


class UserDBHandler(BaseDBHandler):

    schema = UserDBSchema()
    model = UserDBModel

    @classmethod
    def register_new_login(cls, user_id):
        cls.update(
            item_pks=dict(id=user_id),
            new_values=dict(last_login=pendulum.now("UTC")),
        )

    @classmethod
    def get_user_password_verified(cls, user: str, password: str):
        with cls.begin_session(readonly=True) as session:
            slam_user = session.query(cls.model).filter_by(login=user).one_or_none()
            if slam_user and slam_user.password == password:
                return cls.schema.dump(slam_user)

    @classmethod
    def get_user_roles_verified(cls, user_id: int, required_roles: Set[USER_ROLE]):
        if not required_roles:
            raise UserAuthorizationException(
                "Cannot verify user role without providing required user roles."
            )
        with cls.begin_session(readonly=True) as session:
            slam_user = session.query(cls.model).filter_by(id=user_id).one_or_none()
            if slam_user is not None and any(
                (
                    r
                    for r in slam_user.roles
                    if r.name in required_roles or r.name == USER_ROLE.ADMIN
                )
            ):
                return cls.schema.dump(slam_user)
