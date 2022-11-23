from typing import Iterator, List

from shapely.geometry import LineString, MultiLineString, shape
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from common_utils.constants import SurroundingType
from common_utils.logger import logger
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from surroundings.constants import BOUNDING_BOX_EXTENSION_RAILROADS
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import SurrTrianglesType

DEFAULT_RAILROAD_WIDTH = 8  # meters


def intersecting_geometries(
    target: BaseGeometry, geometries: List[BaseGeometry]
) -> Iterator[BaseGeometry]:
    """
    geometries are indexed in a rtree, target is use as a predicate to whether return an
    element in the indexed tree or not (returns if intersects)
    """
    rtree = STRtree(geometries)
    return (geom for geom in rtree.query(target) if geom.intersects(target))


class SwissTopoRailroadSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):
    _ENTITIES_FILE_PATH = (
        "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_OEV/swissTLM3D_TLM_EISENBAHN.{}"
    )
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_RAILROADS

    def get_raw_geometries(self) -> Iterator[LineString]:
        for railroad_line in intersecting_geometries(
            target=self.bounding_box,
            geometries=[shape(entity["geometry"]) for entity in self.entities()],
        ):
            railroad_line = railroad_line.intersection(self.bounding_box)
            railroad_line = (
                railroad_line
                if isinstance(railroad_line, MultiLineString)
                else MultiLineString([railroad_line])
            )
            for segment in railroad_line.geoms:
                yield segment

    def get_triangles(
        self,
    ) -> Iterator[SurrTrianglesType]:
        for segment in self.get_raw_geometries():
            railroad_area = self.add_width(segment, DEFAULT_RAILROAD_WIDTH)
            for polygon in railroad_area.geoms:
                for triangle in self.format_triangles(triangulate_polygon(polygon)):
                    yield SurroundingType.RAILROADS, triangle
        logger.info(f"Railroad successfully calculated for location {self.location}")
