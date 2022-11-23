from typing import Iterator

from shapely.geometry import shape

from common_utils.constants import SurroundingType
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import SurrTrianglesType


class SwissTopoParksSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):
    """
    TRANSLATION: freizeitareal = leisure area
    Includes:
    'Campsite area', 'zoo area', 'stand area', 'sports field area',
    'swimming pool area', 'golf course area', 'leisure area', 'horse racing area'
    """

    _ENTITIES_FILE_PATH = (
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_AREALE/swissTLM3D_TLM_FREIZEITAREAL.{}"
    )

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

    def get_triangles(
        self,
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.entities():
            if entity["properties"]["OBJEKTART"] in self.TYPES_TO_REMOVE:
                continue

            park = self.valid_geometry_intersected_without_z(
                geom=shape(entity["geometry"])
            )
            if park:
                for polygon in as_multipolygon(park).geoms:
                    for (
                        triangle
                    ) in self.get_3d_triangles_from_2d_polygon_with_elevation(
                        polygon=polygon
                    ):
                        yield SurroundingType.PARKS, triangle

        logger.info(f"Parks successfully calculated for location {self.location}")
