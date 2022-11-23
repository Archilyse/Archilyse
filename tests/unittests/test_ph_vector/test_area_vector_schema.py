from dataclasses import fields

import pytest

from handlers.ph_vector.ph2022.area_vector_schema import AreaVectorStatsSchema


@pytest.mark.parametrize(
    "prefix, expected_default_value",
    [("connectivity_", None), ("window_", 0.0), ("view_", None)],
)
def test_area_vector_stats_schema_adds_default_values_for_optional_fields(
    prefix, expected_default_value
):
    optional_fields = {
        f.name for f in fields(AreaVectorStatsSchema) if f.name.startswith(prefix)
    }
    vector_stats_data = AreaVectorStatsSchema(
        **{
            f.name: -9999.99
            for f in fields(AreaVectorStatsSchema)
            if f.name not in optional_fields
        }
    )
    assert all(
        getattr(vector_stats_data, f) == expected_default_value for f in optional_fields
    )
