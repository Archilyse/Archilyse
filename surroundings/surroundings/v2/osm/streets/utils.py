from common_utils.constants import SurroundingType
from surroundings.v2.osm.streets.constants import STREET_TYPE_MAPPING


def is_pedestrian(properties: dict) -> bool:
    raw_street_type = properties.get("fclass")
    return STREET_TYPE_MAPPING.get(raw_street_type) == SurroundingType.PEDESTRIAN
