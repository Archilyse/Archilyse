import pytest

from common_utils.constants import ManualSurroundingTypes
from common_utils.exceptions import DBValidationException
from handlers.db import ManualSurroundingsDBHandler


def test_add(site, manually_created_surroundings):
    ManualSurroundingsDBHandler.add(
        site_id=site["id"], surroundings=manually_created_surroundings
    )
    assert (
        ManualSurroundingsDBHandler.get_by(site_id=site["id"])["surroundings"]
        == manually_created_surroundings
    )


@pytest.mark.parametrize(
    "feature_properties, expected_message",
    [
        (
            {
                "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
            },
            "For surrounding type BUILDINGS height property is required.",
        ),
        (
            {
                "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
                "height": -10.0,
            },
            "Must be greater than 0.0.",
        ),
        (
            {
                "surrounding_type": "UNKNOWN_SURROUNDING_TYPE",
            },
            "Must be one of: BUILDINGS, EXCLUSION_AREA.",
        ),
    ],
)
def test_add_validates_properties(
    site, feature_properties, expected_message, manually_created_surroundings
):
    feature = manually_created_surroundings["features"][0]
    feature["properties"] = feature_properties

    with pytest.raises(DBValidationException) as e:
        ManualSurroundingsDBHandler.add(
            site_id=site["id"], surroundings=manually_created_surroundings
        )
    assert expected_message in str(e.value)
