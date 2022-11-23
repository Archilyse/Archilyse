from db_models import DmsPermissionModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class DmsPermissionDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = DmsPermissionModel


class DmsPermissionDBHandler(BaseDBHandler):
    schema = DmsPermissionDBSchema()
    model = DmsPermissionModel
