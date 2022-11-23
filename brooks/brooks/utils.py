from typing import Dict, Optional, Tuple, Union

from .constants import GENERIC_HEIGHTS
from .types import FeatureType, OpeningType, SeparatorType


def get_default_element_upper_edge(
    element_type: Union[SeparatorType, OpeningType, FeatureType, str],
    default: Optional[Dict] = None,
) -> float:
    if default is not None:
        return default[element_type][1]

    return GENERIC_HEIGHTS[element_type][1]


def get_default_element_lower_edge(
    element_type: Union[SeparatorType, OpeningType, FeatureType, str],
    default: Optional[Dict] = None,
) -> float:
    if default is not None:
        return default[element_type][0]

    return GENERIC_HEIGHTS[element_type][0]


def get_default_element_height(
    element_type: Union[SeparatorType, OpeningType, FeatureType, str],
    default: Optional[Dict] = None,
) -> float:
    return get_default_element_upper_edge(
        element_type=element_type, default=default
    ) - get_default_element_lower_edge(element_type=element_type, default=default)


def get_default_element_height_range(
    element_type: Union[SeparatorType, OpeningType, FeatureType, str],
    default: Optional[Dict] = None,
) -> Tuple[float, float]:
    return (
        get_default_element_lower_edge(element_type=element_type, default=default),
        get_default_element_upper_edge(element_type=element_type, default=default),
    )


def get_floor_height(default: Optional[Dict] = None):
    return get_default_element_height(
        SeparatorType.WALL, default=default
    ) + get_default_element_height("CEILING_SLAB", default=default)
