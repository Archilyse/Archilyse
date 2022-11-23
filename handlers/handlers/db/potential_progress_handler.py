from db_models import PotentialCHProgress
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class PotentialCHProgressDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = PotentialCHProgress


class PotentialCHProgressDBHandler(BaseDBHandler):
    schema = PotentialCHProgressDBSchema()
    model = PotentialCHProgress
