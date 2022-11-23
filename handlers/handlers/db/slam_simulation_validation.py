from db_models import SlamSimulationValidationDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class SlamSimulationValidationDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = SlamSimulationValidationDBModel


class SlamSimulationValidationDBHandler(BaseDBHandler):

    schema = SlamSimulationValidationDBSchema()
    model = SlamSimulationValidationDBModel
