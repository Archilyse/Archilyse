from collections import namedtuple
from itertools import groupby
from typing import Iterator, List

import numpy as np
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import unary_union

from common_utils.constants import SurroundingType
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from surroundings.constants import BOUNDING_BOX_EXTENSION_LAKES
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import SurrTrianglesType

Lake = namedtuple("Lake", ["polygon", "altitude"])


class SwissTopoLakeSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):

    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION_LAKES

    _ENTITIES_FILE_PATH = "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.{}"

    IGNORED_LAKES = {"Vierwaldstättersee"}  # ?

    def get_triangles(
        self,
    ) -> Iterator[SurrTrianglesType]:
        for lake in self.recreate_swisstopo_lakes():
            lake = self.valid_geometry_intersected_without_z(geom=lake)
            if lake:
                for polygon in as_multipolygon(lake).geoms:
                    for (
                        triangle
                    ) in self.get_3d_triangles_from_2d_polygon_with_elevation(
                        polygon=polygon
                    ):
                        yield SurroundingType.LAKES, triangle

        logger.info(f"Lakes successfully calculated for location {self.location}")

    def recreate_swisstopo_lakes(self) -> Iterator[Polygon]:
        water_bodies = []
        for entity in self.entities():
            try:
                if any(
                    ignored_lake in str(entity["properties"]["NAME"])
                    for ignored_lake in self.IGNORED_LAKES
                ):
                    continue
                water_level = float(
                    np.mean([p[2] for p in entity["geometry"]["coordinates"]])
                )
                buffered_line_string = shape(entity["geometry"]).buffer(0.001)
                water_bodies.append(
                    Lake(polygon=buffered_line_string, altitude=water_level)
                )
            except Exception as e:
                logger.warning(
                    f"Lake entity {entity['properties']['NAME']} could not be initialized. Exception: {e}"
                )
                continue

        yield from self._join_lake_segments(
            self._group_water_by_water_levels(water_bodies)
        )

    @classmethod
    def _group_water_by_water_levels(
        cls, water_bodies: List[Lake]
    ) -> Iterator[MultiPolygon]:
        """Groups shore segments according to their rounded altitude"""
        sorted_water_bodies = sorted(water_bodies, key=lambda x: round(x.altitude))
        for _, group in groupby(sorted_water_bodies, lambda x: round(x.altitude)):
            # Returns the joined polygons as MultiPolygons
            yield as_multipolygon(unary_union([lake.polygon for lake in group]))

    @classmethod
    def _join_lake_segments(cls, groups: Iterator[MultiPolygon]) -> Iterator[Polygon]:
        """Joins the collection of shore LineString to a closed Polygon representing the lake"""
        for lakes in groups:
            for polygon in lakes.geoms:
                # Makes a big box around
                bounds = polygon.bounds
                xlim = [
                    bounds[0] - 5 * abs(bounds[0] - bounds[2]),
                    bounds[2] + 5 * abs(bounds[0] - bounds[2]),
                ]
                ylim = [
                    bounds[1] - 5 * abs(bounds[1] - bounds[3]),
                    bounds[3] + 5 * abs(bounds[1] - bounds[3]),
                ]
                boundary_box = box(xlim[0], ylim[0], xlim[1], ylim[1])
                areas = boundary_box.difference(polygon)

                if isinstance(areas, MultiPolygon) and len(areas.geoms) == 2:
                    # Keep smaller area
                    yield areas.geoms[0] if areas.geoms[0].area < areas.geoms[
                        1
                    ].area else areas.geoms[1]
