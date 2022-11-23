from typing import Dict, Tuple

import fiona
from methodtools import lru_cache
from shapely.geometry import Point, shape
from shapely.strtree import STRtree

from brooks.util.geometry_ops import get_polygons
from brooks.util.projections import project_geometry
from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, REGION
from surroundings.base_noise_surrounding_handler import BaseNoiseLevelHandler
from surroundings.eu_noise.constants import DATASET_CONTENT_TYPE, DATASET_EPSG_REGION
from surroundings.eu_noise.utils import download_files_if_not_exists


class EUNoiseLevelHandler(BaseNoiseLevelHandler):
    def __init__(
        self,
        region: REGION,
        location: Point,
        bounding_box_extension: int,
        noise_source_type: NOISE_SOURCE_TYPE,
        noise_time_type: NOISE_TIME_TYPE,
    ):
        super().__init__(
            location=project_geometry(
                location, crs_from=region, crs_to=DATASET_EPSG_REGION
            ),
            bounding_box_extension=bounding_box_extension,
            noise_source_type=noise_source_type,
            noise_time_type=noise_time_type,
        )
        self.region = region

    @staticmethod
    def _get_noise_level(entity: Dict) -> float:
        lower_level, upper_level = (
            entity["properties"]["DB_Low"],
            entity["properties"]["DB_High"],
        )
        if not upper_level:
            return lower_level
        return (lower_level + upper_level) / 2

    @lru_cache()
    def _get_noise_areas_and_levels(self) -> Tuple[STRtree, Dict]:
        noise_levels_by_area = {}
        noise_areas = []

        for filename in download_files_if_not_exists(
            region=self.region,
            content_type=DATASET_CONTENT_TYPE.NOISE_LEVELS,
            noise_source_type=self.noise_source_type,
            noise_time=self.noise_time_type,
        ):
            with fiona.open(filename) as f:
                for entity in f:
                    for polygon in get_polygons(shape(entity["geometry"])):
                        if self.bounding_box.intersects(polygon):
                            noise_levels_by_area[polygon.wkb] = self._get_noise_level(
                                entity
                            )
                            noise_areas.append(polygon)

        return STRtree(noise_areas), noise_levels_by_area

    def get_at(self, location: Point) -> float:
        location_dataset_crs = project_geometry(
            location, crs_from=self.region, crs_to=DATASET_EPSG_REGION
        )
        noise_areas_tree, noise_levels_by_area = self._get_noise_areas_and_levels()
        # NOTE since the geometries in the shape files can be
        # touching or even overlapping we select the max noise level
        return max(
            (
                noise_levels_by_area.get(noise_area.wkb)
                for noise_area in noise_areas_tree.query(location_dataset_crs)
                if noise_area.intersects(location_dataset_crs)
            ),
            default=0,
        )
