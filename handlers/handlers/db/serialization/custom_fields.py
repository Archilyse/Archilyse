from datetime import datetime, timedelta
from typing import Any, Dict, Type, Union

from marshmallow import fields

TYPE_CHECK_MAP: Dict[Type[Union[fields.DateTime, fields.TimeDelta]], Any] = {
    fields.DateTime: lambda v: isinstance(v, datetime),
    fields.TimeDelta: lambda v: isinstance(v, timedelta),
}


def custom_field(
    field_type: Type[Union[fields.DateTime, fields.TimeDelta]],
    attribute: str,
    load_empty_string_as_none: bool = False,
    load_deserialized: bool = False,
    **field_kwargs
):
    class CustomField(field_type):  # type: ignore
        def _deserialize(self, value, attr, obj, **kwargs):
            if load_empty_string_as_none and value == "":
                return None
            if load_deserialized and TYPE_CHECK_MAP[field_type](value):
                return value
            return super()._deserialize(value, attr, obj, **kwargs)

    return CustomField(attribute=attribute, **field_kwargs)
