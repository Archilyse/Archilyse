from db_models.db_entities import CompetitionClientInputDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class CompetitionClientInputDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = CompetitionClientInputDBModel


class CompetitionManualInputDBHandler(BaseDBHandler):
    schema = CompetitionClientInputDBSchema()
    model = CompetitionClientInputDBModel
