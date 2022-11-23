from db_models.db_entities import FolderDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class FolderDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = FolderDBModel


class FolderDBHandler(BaseDBHandler):
    schema = FolderDBSchema()
    model = FolderDBModel
