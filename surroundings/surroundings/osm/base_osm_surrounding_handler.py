from collections import Counter
from typing import Collection, Dict, Iterator, Optional

import fiona
from shapely.geometry import Point, Polygon, shape
from shapely.strtree import STRtree

from brooks.util.geometry_ops import get_polygons
from brooks.util.projections import project_geometry
from common_utils.constants import (
    GOOGLE_CLOUD_OSM,
    REGION,
    SIMULATION_VERSION,
    SurroundingType,
)
from common_utils.logger import logger
from surroundings.base_elevation_handler import BaseElevationHandler
from surroundings.base_entity_surrounding_handler import BaseEntitySurroundingHandler
from surroundings.constants import (
    BOUNDING_BOX_EXTENSION,
    OSM_DIR,
    OSM_REGIONS_FILENAMES,
)
from surroundings.utils import FilteredPolygonEntity, download_shapefile_if_not_exists


class BaseEntityOSMSurroundingHandler(BaseEntitySurroundingHandler):
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION

    def __init__(
        self,
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        raster_grid: Optional[STRtree] = None,
        bounding_box_extension: Optional[float] = None,
        elevation_handler: BaseElevationHandler = None,
    ):
        """
        NOTE: the location HAS to be provided already projected so that it is in meters AND in xy format!
        The bounding_box_extension has to be provided (in meters).
        """
        super().__init__(
            location=location,
            bounding_box_extension=bounding_box_extension,
            region=region,
            simulation_version=simulation_version,
        )
        self.raster_grid = raster_grid
        if elevation_handler:
            self.elevation_handler = elevation_handler
        else:
            self.elevation_handler = super().elevation_handler

    @property
    def surrounding_type(self) -> SurroundingType:
        raise NotImplementedError()

    def elevation_handler(self):
        return self.elevation_handler()

    def custom_entity_validity_check(self, entity: Dict) -> bool:
        return True

    def get_surroundings_bounding_box(
        self, location: Point, bounding_box_extension: float = BOUNDING_BOX_EXTENSION
    ) -> Polygon:
        """Bounding box must be in xy"""
        bounding_box = super().get_surroundings_bounding_box(
            location=location, bounding_box_extension=bounding_box_extension
        )
        return project_geometry(
            geometry=bounding_box, crs_from=self.region, crs_to=REGION.LAT_LON
        )

    def filtered_entities(self) -> Iterator[FilteredPolygonEntity]:
        logger.info(f"Processing {self.surrounding_type.name}")
        counter = Counter()

        for entity in (
            entity
            for entity in self.entities()
            if self.custom_entity_validity_check(entity=entity)
        ):
            raw_geometry = shape(entity["geometry"])
            geometry = self.valid_geometry_intersected_without_z(geom=raw_geometry)
            if not geometry:
                continue

            projected_geometry = project_geometry(
                geometry=geometry,
                crs_from=REGION.LAT_LON,
                crs_to=self.region,
            )
            new_valid_entity = FilteredPolygonEntity(
                geometry=projected_geometry, entity=entity
            )
            counter[new_valid_entity.entity_class] += 1
            if counter[new_valid_entity.entity_class] % 25 == 0:
                logger.info(
                    f"Processed {counter[new_valid_entity.entity_class]} {new_valid_entity.entity_class} "
                    f"entities in location {self.location}"
                )
            yield new_valid_entity

        logger.info(
            f"{self.surrounding_type.name} successfully calculated for location {self.location}, stats: {counter}"
        )

    def _segment_polygon(self, polygon: Polygon) -> Iterator[Polygon]:
        if self.raster_grid:
            yield from (
                # NOTE we have to drop z if present
                Polygon(coords[:2] for coords in intersection.exterior.coords)
                for ground_triangle in self.raster_grid.query(polygon)
                if ground_triangle.intersects(polygon)
                for intersection in get_polygons(ground_triangle.intersection(polygon))
            )
        else:
            yield polygon

    def load_entities(self, entities_file_path: str) -> Collection:
        if entities_file_path:
            sub_path = OSM_REGIONS_FILENAMES[self.region].joinpath(entities_file_path)
            local_path = OSM_DIR.joinpath(sub_path)
            remote = GOOGLE_CLOUD_OSM.joinpath(sub_path)
            download_shapefile_if_not_exists(remote=remote, local=local_path)
            return fiona.open(local_path)
        return []
