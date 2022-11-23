from typing import Collection

from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import RAILWAYS_FILE_TEMPLATES, SWISSTOPO_TRUE
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)
from surroundings.v2.swisstopo.utils import is_tunnel


class SwissTopoRailwayGeometryProvider(SwissTopoShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return RAILWAYS_FILE_TEMPLATES

    @staticmethod
    def is_inactive(geometry: Geometry) -> bool:
        """Returns true if the railway tracks are inactive"""
        return geometry.properties["AUSSER_BET"] in SWISSTOPO_TRUE

    def geometry_filter(self, geometry: Geometry) -> bool:
        return not self.is_inactive(geometry=geometry) and not is_tunnel(
            geometry=geometry
        )


class SwissTopoNoisyRailwayGeometryProvider(SwissTopoRailwayGeometryProvider):
    TRAIN_TYPE = "Bahn"

    @classmethod
    def is_train(cls, geometry: Geometry) -> bool:
        """To exclude trams and metros"""
        return geometry.properties["VERKEHRSMI"] == cls.TRAIN_TYPE

    def geometry_filter(self, geometry: Geometry) -> bool:
        return (
            self.is_train(geometry=geometry)
            and not self.is_inactive(geometry=geometry)
            and not is_tunnel(geometry=geometry)
        )
