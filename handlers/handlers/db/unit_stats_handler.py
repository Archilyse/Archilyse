from db_models import UnitStatsDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class UnitStatsDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = UnitStatsDBModel


class UnitStatsDBHandler(BaseDBHandler):
    schema = UnitStatsDBSchema()
    model = UnitStatsDBModel
