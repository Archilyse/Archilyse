import pytest
from marshmallow import Schema, ValidationError, fields

from slam_api.serialization import UnionField


@pytest.mark.parametrize(
    "data_to_check, data_type_expected",
    [
        ({"test_field": 5.0}, float),
        ({"test_field": True}, bool),
        ({"test_field": "Payaso"}, False),
    ],
)
def test_deserialize_union_field(data_to_check, data_type_expected):
    class TestSchema(Schema):
        test_field = UnionField([fields.Number(), fields.Boolean()])

    if not data_type_expected:
        with pytest.raises(ValidationError):
            TestSchema().load(data_to_check)
    else:
        assert isinstance(
            TestSchema().load(data_to_check)["test_field"], data_type_expected
        )
