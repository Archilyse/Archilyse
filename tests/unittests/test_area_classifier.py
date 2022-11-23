from brooks.area_classifier import AreaClassifier
from brooks.types import FeatureType


def test_allowed_features():
    assert AreaClassifier.ALLOWED_FEATURES() == {
        FeatureType.BATHTUB.name,
        FeatureType.BIKE_PARKING.name,
        FeatureType.BUILT_IN_FURNITURE.name,
        FeatureType.CAR_PARKING.name,
        FeatureType.ELEVATOR.name,
        FeatureType.KITCHEN.name,
        FeatureType.NOT_DEFINED.name,
        FeatureType.RAMP.name,
        FeatureType.SEAT.name,
        FeatureType.SHAFT.name,
        FeatureType.SHOWER.name,
        FeatureType.SINK.name,
        FeatureType.STAIRS.name,
        FeatureType.TOILET.name,
        FeatureType.WASHING_MACHINE.name,
    }
