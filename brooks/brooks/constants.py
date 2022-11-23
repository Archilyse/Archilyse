from enum import Enum
from typing import Dict, Tuple, Union

from brooks.types import FeatureType, OpeningType, SeparatorType

PARAM_BUFFER_MERGE = 0.01

GENERIC_HEIGHTS: Dict[
    Union[SeparatorType, str, FeatureType, OpeningType], Tuple[float, float]
] = {
    SeparatorType.WALL: (0.0, 2.60),
    SeparatorType.AREA_SPLITTER: (0.0, 2.60),
    "GENERIC_SPACE_HEIGHT": (0.0, 2.60),
    FeatureType.ELEVATOR: (0.0, 2.60),
    FeatureType.BATHTUB: (0.0, 0.6),
    FeatureType.SINK: (0.6, 0.85),
    FeatureType.SHOWER: (0.0, 0.2),
    FeatureType.TOILET: (0.0, 0.4),
    FeatureType.KITCHEN: (0.0, 0.9),
    FeatureType.SHAFT: (0.0, 2.60),
    FeatureType.STAIRS: (0.0, 2.60),
    FeatureType.SEAT: (0.0, 1.20),
    FeatureType.RAMP: (0.0, 2.00),
    FeatureType.BIKE_PARKING: (0.0, 2.00),
    FeatureType.BUILT_IN_FURNITURE: (0.0, 1.50),
    FeatureType.CAR_PARKING: (0.0, 2.30),
    FeatureType.WASHING_MACHINE: (0.0, 1.30),
    FeatureType.OFFICE_DESK: (0.0, 1.20),
    OpeningType.DOOR: (0.0, 2.00),
    OpeningType.ENTRANCE_DOOR: (0.0, 2.00),
    OpeningType.WINDOW: (0.5, 2.40),
    SeparatorType.RAILING: (0.0, 1.00),
    SeparatorType.COLUMN: (0.0, 2.60),
    "CEILING_SLAB": (0, 0.3),
    "FLOOR_SLAB": (0, 0.3),
}


class BathroomSubtype(Enum):
    SHOWER = "Shower"
    WC = "WC"
    LAUNDRY = "Laundry"


class FeatureSide(Enum):
    SHORT_SIDE = "SHORT_SIDE"
    LONG_SIDE = "LONG_SIDE"


FEATURE_SIDES_ON_WALL = {
    FeatureType.STAIRS: FeatureSide.LONG_SIDE,
    FeatureType.SINK: FeatureSide.LONG_SIDE,
    FeatureType.TOILET: FeatureSide.SHORT_SIDE,
}


IMAGES_DPI = 300
THICKEST_WALL_POSSIBLE_IN_M = 0.9
THINNEST_WALL_POSSIBLE_IN_M = 0.01
ITEM_TO_SEPARATOR_SNAPPING_THRESHOLD_IN_M = 0.05
ITEM_SEPARATOR_INTERSECTING_THRESHOLD_IN_M2 = 0.0001


class SuperTypes(Enum):
    SEPARATORS = "SEPARATORS"
    ITEMS = "ITEMS"
    OPENINGS = "OPENINGS"
