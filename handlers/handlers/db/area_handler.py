from marshmallow import fields
from marshmallow_enum import EnumField

from brooks.types import AllAreaTypes
from db_models import AreaDBModel, UnitsAreasDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class AreaDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = AreaDBModel
        exclude = ("plan", "units")

    area_type = EnumField(AllAreaTypes, metadata={"by_name": True})
    coord_x = fields.Float()
    coord_y = fields.Float()


class AreaDBHandler(BaseDBHandler):
    schema = AreaDBSchema()
    model = AreaDBModel


class UnitAreaDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = UnitsAreasDBModel


class UnitAreaDBHandler(BaseDBHandler):
    schema = UnitAreaDBSchema()
    model = UnitsAreasDBModel
