from typing import Iterator

import fiona
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from brooks.util.geometry_ops import get_line_strings
from brooks.util.projections import project_geometry
from common_utils.constants import NOISE_SOURCE_TYPE
from surroundings.base_noise_source_geometry_provider import (
    BaseNoiseSourceGeometryProvider,
)
from surroundings.eu_noise.constants import DATASET_CONTENT_TYPE, DATASET_EPSG_REGION
from surroundings.eu_noise.utils import download_files_if_not_exists


class EUNoiseSourceGeometryProvider(BaseNoiseSourceGeometryProvider):
    def get_source_geometries(
        self, noise_source_type: NOISE_SOURCE_TYPE
    ) -> Iterator[BaseGeometry]:
        bounding_box = project_geometry(
            self.bounding_box, crs_from=self.region, crs_to=DATASET_EPSG_REGION
        )
        for filename in download_files_if_not_exists(
            region=self.region,
            noise_source_type=noise_source_type,
            content_type=DATASET_CONTENT_TYPE.SOURCE_GEOMETRIES,
        ):
            with fiona.open(filename) as f:
                for entity in f:
                    if entity["geometry"]:
                        geom = shape(entity["geometry"])
                        if bounding_box.intersects(geom):
                            yield from get_line_strings(
                                project_geometry(
                                    bounding_box.intersection(geom),
                                    crs_from=DATASET_EPSG_REGION,
                                    crs_to=self.region,
                                )
                            )
