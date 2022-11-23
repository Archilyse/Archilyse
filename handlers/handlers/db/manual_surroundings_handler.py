from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from common_utils.constants import ManualSurroundingTypes
from db_models import ManualSurroundingsDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class GeoJsonFeatureProperties(Schema):
    surrounding_type = fields.Str(
        validate=validate.OneOf([t.name for t in ManualSurroundingTypes])
    )
    height = fields.Float(validate=validate.Range(min=0.0, min_inclusive=False))

    @validates_schema
    def validate_special_properties(self, data, **kwargs):
        if data["surrounding_type"] == ManualSurroundingTypes.BUILDINGS.name:
            if "height" not in data:
                raise ValidationError(
                    f"For surrounding type {ManualSurroundingTypes.BUILDINGS.name} height property is required."
                )


class GeoJsonGeometrySchema(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.List(fields.List(fields.Float())))


class GeoJsonFeatureSchema(Schema):
    type = fields.Str()
    properties = fields.Nested(GeoJsonFeatureProperties)
    geometry = fields.Nested(GeoJsonGeometrySchema)


class GeoJsonFeatureCollectionSchema(Schema):
    type = fields.Str()
    features = fields.Nested(GeoJsonFeatureSchema, many=True)


class ManualSurroundingsDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = ManualSurroundingsDBModel

    surroundings = fields.Nested(
        GeoJsonFeatureCollectionSchema, required=True, allow_none=False
    )


class ManualSurroundingsDBHandler(BaseDBHandler):
    schema = ManualSurroundingsDBSchema()
    model = ManualSurroundingsDBModel
