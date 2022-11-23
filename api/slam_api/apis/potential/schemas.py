from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    validate,
    validates_schema,
)

from common_utils.constants import SIMULATION_TYPE


class ApiUserLoginSchema(Schema):
    user = fields.String(required=True)
    password = fields.String(required=True)


class ApiUserBearerSchema(Schema):
    access_token = fields.String()
    msg = fields.String()


class PotentialSimulationRequestSchema(Schema):
    sim_type = fields.String(
        required=True, validate=validate.OneOf([v.value for v in SIMULATION_TYPE])
    )
    lat = fields.Float(required=True, validate=validate.Range(min=45.80, max=47.85))
    lon = fields.Float(required=True, validate=validate.Range(min=5.95, max=10.52))
    floor_number = fields.Int(required=True, validate=validate.Range(min=0, max=20))


class SimulationAPISchema(PotentialSimulationRequestSchema):
    class Meta:
        unknown = EXCLUDE

    building_footprint = fields.String(
        required=True, metadata={"description": "Building footprint in wkt format"}
    )
    result = fields.Dict(keys=fields.Str())


class BoundingBoxSchema(Schema):
    min_lat = fields.Float()
    min_lon = fields.Float()
    max_lat = fields.Float()
    max_lon = fields.Float()

    @validates_schema
    def validate(self, data, **kwargs):
        if data and len(data) < 4:
            raise ValidationError("Invalid bounding box.")
