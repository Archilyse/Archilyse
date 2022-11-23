from db_models import UnitSimulationDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class UnitSimulationDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = UnitSimulationDBModel


class UnitSimulationDBHandler(BaseDBHandler):
    schema = UnitSimulationDBSchema()
    model = UnitSimulationDBModel
