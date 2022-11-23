import pytest
from marshmallow import ValidationError

from slam_api.serialization import CustomValuatorResultFileDeserializer


@pytest.mark.parametrize(
    "row, expected",
    [
        (
            [
                "Salpica",
                "uNit idenTifier",
                "final predicted gross rent (EUR yearly/m2)",
                "rent caliBrator adjustment factor",
            ],
            [1, 2, 3],
        ),
        (
            [
                "   unit identifier    ",
                "\tFinal predicted gross rent (CHF yearly/m2)",
                "Rent Calibrator Adjustment Factor \t",
            ],
            [0, 1, 2],
        ),
    ],
)
def test_get_field_indices(row, expected):
    assert (
        sorted(CustomValuatorResultFileDeserializer._get_field_indices(row).values())
        == expected
    )


@pytest.mark.parametrize(
    "row",
    [
        (["Salpica", "uNit idenTifier"]),
        (
            [
                "   unit identifier    ",
                "\tFinal predicted gross rent (CHF yearly/m2)",
                "Rent Calibrator Adjustment Factor SALPICA\t",
            ]
        ),
        (
            [
                "   unit identifier    ",
                "\tFinal predicted gross rent (CHF monthly/m2)",
                "Rent Calibrator Adjustment Factor \t",
            ]
        ),
        ([]),
    ],
)
def test_get_field_indices_exception(row):
    with pytest.raises(ValidationError):
        CustomValuatorResultFileDeserializer._get_field_indices(row)
