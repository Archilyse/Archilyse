from marshmallow import Schema, fields

from db_models import ExpectedClientDataDBModel
from handlers.db import BaseDBHandler
from handlers.db.base_handler import Float, Int, Str
from handlers.db.serialization import BaseDBSchema

INDEX_ROOM_NUMBER = "number_of_rooms"
INDEX_NET_AREA = "net_area"
INDEX_HNF_AREA = "HNF"
INDEX_ANF_AREA = "ANF"
INDEX_STREET = "street"
INDEX_CLIENT_BUILDING_ID = "client_building_id"
INDEX_FLOOR_NUMBER = "floor"

QA_COLUMN_HEADERS = {
    INDEX_ROOM_NUMBER,
    INDEX_NET_AREA,
    INDEX_HNF_AREA,
    INDEX_ANF_AREA,
    INDEX_STREET,
    INDEX_CLIENT_BUILDING_ID,
    INDEX_FLOOR_NUMBER,
}


class TrimmedString(fields.String):
    def _deserialize(self, value, *args, **kwargs):
        if hasattr(value, "strip"):
            value = value.strip()
        return super()._deserialize(value, *args, **kwargs)


class QADataValuesSchema(Schema):
    client_building_id = TrimmedString(allow_none=True, dump_default=None)
    number_of_rooms = Float(allow_none=True, dump_default=None)
    net_area = Float(allow_none=True, dump_default=None)
    HNF = Float(allow_none=True, dump_default=None)
    ANF = Float(allow_none=True, dump_default=None)
    street = Str(allow_none=True, dump_default=None)
    floor = Int(allow_none=True, dump_default=None)


class QADBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = ExpectedClientDataDBModel

    data = fields.Dict(
        keys=TrimmedString(allow_none=False),
        values=fields.Nested(
            QADataValuesSchema(partial=False), required=True, allow_none=False
        ),
        allow_none=True,
    )


class QADBHandler(BaseDBHandler):
    schema = QADBSchema()
    model = ExpectedClientDataDBModel
