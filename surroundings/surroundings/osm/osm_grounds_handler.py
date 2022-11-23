from collections import defaultdict
from typing import Iterator, Optional

from shapely.geometry import MultiPolygon, Point, Polygon

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from dufresne.polygon.utils import as_multipolygon
from surroundings.constants import BOUNDING_BOX_EXTENSION_GROUNDS
from surroundings.srtm import SRTMGroundSurroundingHandler
from surroundings.swisstopo.ground_surrounding_handler import (
    SwissTopoGroundSurroundingHandler,
)

from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler


class FlatGroundHandler(BaseEntityOSMSurroundingHandler):
    """Returns a big flat box with an offset of -0.5 so 3D views doesnt look that bad"""

    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_GROUNDS
    OVERFLOW_OFFSET = -0.5

    def __init__(
        self,
        building_footprints: Optional[list[Polygon | MultiPolygon]] = None,
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)

    def get_triangles(self) -> Iterator[tuple[SurroundingType, list[tuple[float]]]]:
        pol = self.elevation_handler.apply_ground_height(
            geom=project_geometry(
                geometry=self.bounding_box,
                crs_from=REGION.LAT_LON,
                crs_to=self.region,
            ),
            offset=self.OVERFLOW_OFFSET,
        )

        yield from (
            (SurroundingType.GROUNDS, triangle)
            for polygon in as_multipolygon(pol).geoms
            for triangle in self.format_triangles(triangulate_polygon(polygon))
        )


class OSMGroundsHandler:
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_GROUNDS

    def __init__(
        self,
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        building_footprints: list[Polygon | MultiPolygon] = None,
        bounding_box_extension: int = None,
    ):
        # Init the proxied handler
        self.ground_handler = GROUND_HANDLERS_BY_REGION.get(
            region, SRTMGroundSurroundingHandler
        )
        self.ground_handler = self.ground_handler(
            location=location,
            region=region,
            bounding_box_extension=bounding_box_extension
            or self._BOUNDING_BOX_EXTENSION,
            simulation_version=simulation_version,
            building_footprints=building_footprints,
        )

    def get_triangles(self) -> Iterator[tuple[SurroundingType, list[tuple[float]]]]:
        yield from self.ground_handler.get_triangles()


GROUND_HANDLERS_BY_REGION = defaultdict(
    SRTMGroundSurroundingHandler,
    {
        REGION.CH: SwissTopoGroundSurroundingHandler,
        REGION.MC: FlatGroundHandler,
    },
)
