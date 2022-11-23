from marshmallow import Schema, fields


class GeoJsonPolygonSchema(Schema):
    coordinates = fields.List(
        # This have to be field as sometimes is a list of floats and others
        # just floats depending if it is a Polygon or multipolygon
        fields.List(fields.List(fields.Field), required=True),
        metadata={
            "example": [
                [
                    [13.420143127441406, 52.515594085869914],
                    [13.421173095703125, 52.50535544522142],
                ]
            ],
        },
    )
    type = fields.Str(dump_default="Polygon")


class LayoutSchema(Schema):
    separators = fields.Dict(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Str(),
                values=fields.Nested(GeoJsonPolygonSchema),
            ),
        ),
        metadata={
            "example": {
                "wall": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [13.420143127441406, 52.515594085869914],
                                [13.421173095703125, 52.50535544522142],
                            ],
                        }
                    }
                ]
            },
        },
    )
    openings = fields.Dict(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Str(),
                values=fields.Dict(
                    keys=fields.Str(),
                    values=fields.Nested(GeoJsonPolygonSchema),
                ),
            ),
        )
    )
    features = fields.Dict(
        fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(
                keys=fields.Str(),
                values=fields.Dict(
                    keys=fields.Str(),
                    values=fields.Nested(GeoJsonPolygonSchema),
                ),
            ),
        )
    )
