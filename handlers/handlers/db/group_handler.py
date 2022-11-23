from db_models.db_entities import GroupDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class GroupDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = GroupDBModel
        exclude = ("users",)


class GroupDBHandler(BaseDBHandler):

    schema = GroupDBSchema()
    model = GroupDBModel
