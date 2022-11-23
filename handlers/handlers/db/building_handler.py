from db_models import BuildingDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class BuildingDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = BuildingDBModel
        exclude = ("site", "floors", "plans")


class BuildingDBHandler(BaseDBHandler):
    schema = BuildingDBSchema()
    model = BuildingDBModel
