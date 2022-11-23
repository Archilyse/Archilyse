from surroundings.v2.geometry import Geometry

from .constants import (
    HIGHWAY_CONDITIONS,
    PRIMARY_CONDITIONS,
    SECONDARY_CONDITIONS,
    STREET_CLASS,
)
from .utils import is_pedestrian


class SwissTopoStreetsClassifier:
    @staticmethod
    def is_pedestrian(geometry: Geometry) -> bool:
        return is_pedestrian(geometry=geometry)

    @staticmethod
    def is_highway(geometry: Geometry) -> bool:
        return geometry.properties["VERKEHRSBD"] == HIGHWAY_CONDITIONS

    @staticmethod
    def is_primary(geometry: Geometry) -> bool:
        return geometry.properties["VERKEHRSBD"] == PRIMARY_CONDITIONS

    @staticmethod
    def is_secondary(geometry: Geometry) -> bool:
        return geometry.properties["VERKEHRSBD"] == SECONDARY_CONDITIONS

    @classmethod
    def classify(cls, geometry: Geometry) -> STREET_CLASS:
        if cls.is_highway(geometry=geometry):
            return STREET_CLASS.HIGHWAY
        elif cls.is_primary(geometry=geometry):
            return STREET_CLASS.PRIMARY_STREET
        elif cls.is_secondary(geometry=geometry):
            return STREET_CLASS.SECONDARY_STREET
        if cls.is_pedestrian(geometry=geometry):
            return STREET_CLASS.PEDESTRIAN
        else:
            return STREET_CLASS.TERTIARY_STREET
