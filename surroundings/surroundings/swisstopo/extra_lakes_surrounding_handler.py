from typing import Generator, Iterator, List, Tuple, Union

from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon

from common_utils.constants import SWISSTOPO_DIR, SurroundingType
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from surroundings.constants import BOUNDING_BOX_EXTENSION_LAKES
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import download_swisstopo_if_not_exists


class SwissTopoExtraLakesSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):

    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_LAKES
    _ENTITIES_FILE_PATH = (
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/MISSING_LAKES/Brienzersee.wkt",
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/MISSING_LAKES/Vierwaldstätter See.wkt",
    )

    def load_entities(self, entities_file_path):
        download_swisstopo_if_not_exists(
            bounding_box=self.bounding_box, templates=self._ENTITIES_FILE_PATH
        )
        for filename in self._ENTITIES_FILE_PATH:
            with SWISSTOPO_DIR.joinpath(filename).open() as f:
                yield wkt.loads(f.read())

    def entities(self) -> Iterator[Union[Polygon, MultiPolygon]]:
        yield from self.load_entities(self._ENTITIES_FILE_PATH)

    def get_triangles(
        self,
    ) -> Tuple[SurroundingType, Generator[List[Tuple[float]], None, None]]:
        """
        Very few lakes are missing (incorrect data) in the swisstopo data.
        They are generated here (source OSM)
        """

        for geometry in self.entities():
            lake = self.valid_geometry_intersected_without_z(geom=geometry)

            if lake:
                for polygon in as_multipolygon(lake).geoms:
                    for (
                        triangle
                    ) in self.get_3d_triangles_from_2d_polygon_with_elevation(
                        polygon=polygon
                    ):
                        yield SurroundingType.LAKES, triangle

        logger.info(f"Lakes successfully calculated for location {self.location}")
