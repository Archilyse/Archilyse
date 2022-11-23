from brooks.types import FeatureType

SANITARY_RADIUS = {
    FeatureType.SINK: 0.15,
    FeatureType.BATHTUB: 0.25,
    FeatureType.SHOWER: 0.15,
}

SANITARY_BUFFER = {
    FeatureType.SINK: 0.05,
    FeatureType.BATHTUB: 0.1,
    FeatureType.SHOWER: 0.1,
}
