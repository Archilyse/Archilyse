from surroundings.v2.geometry import Geometry

from .constants import PEDESTRIAN_STREET_TYPES, STREETS_WO_CAR_TRAFFIC


def is_pedestrian(geometry: Geometry) -> bool:
    return (
        geometry.properties["VERKEHRSBE"] in STREETS_WO_CAR_TRAFFIC
        or geometry.properties["OBJEKTART"] in PEDESTRIAN_STREET_TYPES
    )
