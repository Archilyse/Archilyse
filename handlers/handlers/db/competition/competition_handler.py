from marshmallow import fields
from marshmallow_enum import EnumField

from common_utils.constants import CURRENCY
from db_models.db_entities import CompetitionDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema
from slam_api.apis.competition.schemas import CompetitionParameters


class CompetitionDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = CompetitionDBModel

    currency = EnumField(CURRENCY, by_value=False)
    configuration_parameters = fields.Nested(
        CompetitionParameters(partial=True),
        many=False,
        dump_default={},
        load_default={},
    )


class CompetitionDBHandler(BaseDBHandler):
    schema = CompetitionDBSchema()
    model = CompetitionDBModel
