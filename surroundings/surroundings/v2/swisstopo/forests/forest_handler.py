from functools import cached_property
from typing import Collection, Optional

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from surroundings.base_forest_surrounding_handler import (
    BaseForestGenerator,
    BushForestGenerator,
    OpenForestGenerator,
    StandardForestGenerator,
)
from surroundings.constants import FOREST_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import ForestGeometryTransformer
from surroundings.v2.swisstopo.constants import FOREST_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)

FOREST_GENERATORS_BY_TYPE = {
    "Wald": StandardForestGenerator,
    "Wald offen": OpenForestGenerator,
    "Gebueschwald": BushForestGenerator,
}


class SwissTopoForestGeometryProvider(SwissTopoShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        return FOREST_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["OBJEKTART"] in FOREST_GENERATORS_BY_TYPE


class SwissTopoForestGeometryTransformer(ForestGeometryTransformer):
    def get_forest_generator(self, geometry: Geometry) -> Optional[BaseForestGenerator]:
        return FOREST_GENERATORS_BY_TYPE[geometry.properties["OBJEKTART"]](
            simulation_version=SIMULATION_VERSION.PH_2022_H1
        )


class SwissTopoForestHandler(BaseSurroundingHandler):
    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return SwissTopoForestGeometryTransformer(
            elevation_handler=self.elevation_handler, ground_offset=FOREST_GROUND_OFFSET
        )

    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoForestGeometryProvider(
            bounding_box=self.bounding_box, region=self.region, clip_geometries=True
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.FOREST
