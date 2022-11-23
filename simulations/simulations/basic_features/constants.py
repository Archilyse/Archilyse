from enum import Enum

from brooks.types import FeatureType


class FurnitureCategory(Enum):
    """
    Furniture categories of basic features represent aggregations of the brooks feature types. E.g. when
    we generate the output vector the brooks features types TOILET are aggregated to a
    common category `toilets`. Generally, the output vector dimensions correspond to the
    enum names in lower case, e.g. `number-of-showers`
    """

    SHOWERS = 1
    BATHTUBS = 2
    TOILETS = 3  # TOILET


PH_FEATURE_CATEGORIES = {
    FurnitureCategory.BATHTUBS: {FeatureType.BATHTUB},
    FurnitureCategory.SHOWERS: {FeatureType.SHOWER},
    FurnitureCategory.TOILETS: {FeatureType.TOILET},
}
