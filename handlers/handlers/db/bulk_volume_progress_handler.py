from marshmallow_enum import EnumField

from common_utils.constants import ADMIN_SIM_STATUS
from db_models import BulkVolumeProgressDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class BulkVolumeProgressDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = BulkVolumeProgressDBModel

    state = EnumField(ADMIN_SIM_STATUS, by_value=True)


class BulkVolumeProgressDBHandler(BaseDBHandler):
    schema = BulkVolumeProgressDBSchema()
    model = BulkVolumeProgressDBModel
