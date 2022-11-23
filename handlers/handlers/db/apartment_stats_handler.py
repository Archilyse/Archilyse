from db_models import ApartmentStatsDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class ApartmentStatsDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = ApartmentStatsDBModel


class ApartmentStatsDBHandler(BaseDBHandler):
    schema = ApartmentStatsDBSchema()
    model = ApartmentStatsDBModel
