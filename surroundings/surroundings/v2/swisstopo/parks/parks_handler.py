from functools import cached_property
from typing import Collection

from common_utils.constants import SurroundingType
from surroundings.constants import PARKS_GROUND_OFFSET
from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import GroundCoveringPolygonTransformer
from surroundings.v2.swisstopo.constants import PARKS_FILE_TEMPLATES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)


class SwissTopoParksGeometryProvider(SwissTopoShapeFileGeometryProvider):
    # This will need to be reviewed as 'Parks' are not really included in this set
    TYPES_TO_REMOVE = {
        "Campingplatzareal",  # 'Campsite area'
        "Zooareal",  # 'zoo area'
        "Standplatzareal",  # 'stand area'
        # "Sportplatzareal", # 'sports field area'
        "Schwimmbadareal",  # 'swimming pool area'
        # "Golfplatzareal",  # 'golf course area'
        "Freizeitanlagenareal",  # 'leisure area'
        # "Pferderennbahnareal", # 'horse racing area'
    }  # Leaving sport and golf and horse racing

    @property
    def file_templates(self) -> Collection[str]:
        return PARKS_FILE_TEMPLATES

    def geometry_filter(self, geometry: Geometry) -> bool:
        return geometry.properties["OBJEKTART"] not in self.TYPES_TO_REMOVE


class SwissTopoParksHandler(BaseSurroundingHandler):
    @cached_property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        return GroundCoveringPolygonTransformer(
            elevation_handler=self.elevation_handler, ground_offset=PARKS_GROUND_OFFSET
        )

    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        return SwissTopoParksGeometryProvider(
            bounding_box=self.bounding_box, region=self.region
        )

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        return SurroundingType.PARKS
