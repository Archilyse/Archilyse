from marshmallow_enum import EnumField

from db_models.db_entities import USER_ROLE, RoleDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class RoleDBSchema(BaseDBSchema):
    name = EnumField(USER_ROLE, by_value=True)

    class Meta(BaseDBSchema.Meta):
        model = RoleDBModel
        exclude = ("users",)


class RoleDBHandler(BaseDBHandler):
    schema = RoleDBSchema()
    model = RoleDBModel
