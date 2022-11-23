import datetime
import logging

from marshmallow.fields import Nested
from sqlalchemy import and_

from common_utils.constants import DMS_FILE_RETENTION_PERIOD
from db_models.db_entities import FileCommentDBModel, FileDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema
from handlers.db.user_handler import UserDBSchema

logger = logging.getLogger()


class FileCommentDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = FileCommentDBModel

    creator = Nested(UserDBSchema(only=("name",)))


class FileCommentDBHandler(BaseDBHandler):
    schema = FileCommentDBSchema()
    model = FileCommentDBModel


class FileDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = FileDBModel


class FileDBHandler(BaseDBHandler):
    schema = FileDBSchema()
    model = FileDBModel

    @classmethod
    def remove_deleted_files(cls) -> list[tuple]:
        deleted_since = datetime.datetime.utcnow() - DMS_FILE_RETENTION_PERIOD
        with cls.begin_session() as session:
            deleted_records = session.execute(
                cls.model.__table__.delete()
                .where(
                    and_(
                        cls.model.deleted.is_(True),
                        cls.model.updated <= deleted_since,
                    )
                )
                .returning(FileDBModel.checksum, FileDBModel.client_id)
            ).fetchall()
            return list(map(tuple, deleted_records))
