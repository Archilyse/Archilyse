import pytest

from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.streets.constants import (
    HIGHWAY_CONDITIONS,
    PEDESTRIAN_STREET_TYPES,
    PRIMARY_CONDITIONS,
    SECONDARY_CONDITIONS,
    STREET_CLASS,
    STREETS_WO_CAR_TRAFFIC,
)
from surroundings.v2.swisstopo.streets.street_classifier import (
    SwissTopoStreetsClassifier,
)


class TestSwissTopoStreetClassifier:
    @pytest.mark.parametrize(
        "properties, expected_street_type",
        [
            (
                {
                    "VERKEHRSBD": HIGHWAY_CONDITIONS,
                },
                STREET_CLASS.HIGHWAY,
            ),
            (
                {
                    "VERKEHRSBD": PRIMARY_CONDITIONS,
                },
                STREET_CLASS.PRIMARY_STREET,
            ),
            (
                {
                    "VERKEHRSBD": SECONDARY_CONDITIONS,
                },
                STREET_CLASS.SECONDARY_STREET,
            ),
            (
                {},
                STREET_CLASS.TERTIARY_STREET,
            ),
            *[
                (
                    {
                        "VERKEHRSBE": no_car_traffic,
                    },
                    STREET_CLASS.PEDESTRIAN,
                )
                for no_car_traffic in STREETS_WO_CAR_TRAFFIC
            ],
            *[
                (
                    {
                        "OBJEKTART": pedestrian_type,
                    },
                    STREET_CLASS.PEDESTRIAN,
                )
                for pedestrian_type in PEDESTRIAN_STREET_TYPES
            ],
        ],
    )
    def test_classify(self, properties, expected_street_type, mocker):
        geometry = Geometry(
            geom=mocker.ANY,
            properties={
                "OBJEKTART": "ANY",
                "VERKEHRSBE": "ANY",
                "VERKEHRSBD": "ANY",
                **properties,
            },
        )
        assert (
            SwissTopoStreetsClassifier.classify(geometry=geometry)
            == expected_street_type
        )
