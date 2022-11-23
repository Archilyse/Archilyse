from typing import Dict, Iterator

from shapely.geometry import Polygon

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, ManualSurroundingTypes
from surroundings.base_elevation_handler import BaseElevationHandler
from surroundings.extruded_polygon_triangulator_mixin import (
    ExtrudedPolygonTriangulatorMixin,
)
from surroundings.utils import SurrTrianglesType

from .constants import MANUAL_SURR_REGION, MANUAL_SURR_TYPE_TO_SURR_TYPE
from .utils import FeatureProviderMixin


class ManualBuildingSurroundingHandler(
    FeatureProviderMixin, ExtrudedPolygonTriangulatorMixin
):
    manual_surrounding_type = ManualSurroundingTypes.BUILDINGS
    surrounding_type = MANUAL_SURR_TYPE_TO_SURR_TYPE[manual_surrounding_type]

    def __init__(
        self, site_id: int, region: REGION, elevation_handler: BaseElevationHandler
    ):
        super().__init__(site_id, region)
        self.elevation_handler = elevation_handler

    def _get_building_footprint_local_crs(self, feature: Dict) -> Polygon:
        return project_geometry(
            Polygon(*feature["geometry"]["coordinates"]),
            crs_from=MANUAL_SURR_REGION,
            crs_to=self.region,
        )

    def get_triangles(self) -> Iterator[SurrTrianglesType]:
        for feature in self.get_features():
            footprint = self._get_building_footprint_local_crs(feature=feature)
            yield from self.extrude_and_triangulate(
                height=feature["properties"]["height"], footprint=footprint
            )
