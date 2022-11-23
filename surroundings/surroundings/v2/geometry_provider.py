from pathlib import Path
from typing import Collection, Iterator

import fiona
from shapely.geometry import Polygon, shape

from brooks.util.projections import project_geometry
from common_utils.constants import REGION
from surroundings.v2.base import BaseGeometryProvider
from surroundings.v2.geometry import Geometry


class ShapeFileGeometryProvider(BaseGeometryProvider):
    def __init__(
        self, bounding_box: Polygon, region: REGION, clip_geometries: bool = False
    ):
        self.clip_geometries = clip_geometries
        self.region = region
        self.bounding_box = bounding_box

    @property
    def dataset_crs(self) -> REGION:
        raise NotImplementedError

    def get_source_filenames(self) -> Collection[Path]:
        raise NotImplementedError

    def geometry_filter(self, geometry: Geometry) -> bool:
        return True

    def get_geometries(self) -> Iterator[Geometry]:
        bounds_src_crs = project_geometry(
            self.bounding_box, crs_from=self.region, crs_to=self.dataset_crs
        ).bounds

        for filename in self.get_source_filenames():
            with fiona.open(filename) as shp_file:
                for entity in shp_file.filter(bbox=bounds_src_crs):
                    geom = shape(entity["geometry"])
                    if self.dataset_crs != self.region:
                        geom = project_geometry(
                            geometry=geom,
                            crs_from=self.dataset_crs,
                            crs_to=self.region,
                        )
                        # NOTE check again if the geometry is intersecting AFTER projection into region crs
                        if not geom.intersects(self.bounding_box):
                            continue

                    geometry = Geometry(
                        properties=entity["properties"],
                        geom=(
                            geom.intersection(self.bounding_box)
                            if self.clip_geometries
                            else geom
                        ),
                    )
                    if self.geometry_filter(geometry=geometry):
                        yield geometry
