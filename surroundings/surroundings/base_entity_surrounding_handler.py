from abc import ABC, abstractmethod
from functools import cached_property
from typing import Collection, Iterator, Optional

import numpy as np
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import transform

from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.constants import REGION, SIMULATION_VERSION
from dufresne.polygon.polygon_triangulate import _triangulate_polygon_2d
from dufresne.polygon.utils import as_multipolygon
from surroundings.base_elevation_handler import get_elevation_handler
from surroundings.constants import BOUNDING_BOX_EXTENSION, OSM_OFFSETS
from surroundings.utils import SurrTrianglesType, Triangle


class BaseEntitySurroundingHandler(ABC):
    # Default bounding box extension
    # You may override this value when extending the class
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION
    _ENTITIES_FILE_PATH = ""

    def __init__(
        self,
        location: Point,
        region: REGION,
        simulation_version: SIMULATION_VERSION,
        bounding_box_extension: Optional[float] = None,
        *args,
        **kwargs,
    ):
        self.simulation_version = simulation_version
        self.location = location
        self.region = region
        self.bounding_box_extension = (
            bounding_box_extension or self.BOUNDING_BOX_EXTENSION
        )

    @property
    def BOUNDING_BOX_EXTENSION(self) -> float:
        return self._BOUNDING_BOX_EXTENSION

    @property
    def altitude_offset(self) -> float:
        try:
            return OSM_OFFSETS.get(self.surrounding_type, 0.0)
        except (KeyError, AttributeError):
            return 0.0

    def load_entities(self, entities_file_path) -> Collection:
        raise NotImplementedError()

    def entities(self) -> Iterator[dict]:
        for entity in self.load_entities(self._ENTITIES_FILE_PATH):
            if entity["geometry"] is not None:
                yield entity

    @cached_property
    def bounding_box(self):
        return self.get_surroundings_bounding_box(
            location=self.location,
            bounding_box_extension=self.bounding_box_extension,
        )

    @cached_property
    def elevation_handler(self):
        # Using default zero elevation for uncovered regions
        return get_elevation_handler(
            region=self.region,
            location=self.location,
            bounding_box_extension=self.bounding_box_extension,
            simulation_version=self.simulation_version,
        )

    @abstractmethod
    def get_triangles(self, *args, **kwargs) -> Iterator[SurrTrianglesType]:
        raise NotImplementedError()

    @staticmethod
    def get_surroundings_bounding_box(
        location: Point, bounding_box_extension: float = BOUNDING_BOX_EXTENSION
    ) -> Polygon:
        return box(
            location.x - bounding_box_extension,
            location.y - bounding_box_extension,
            location.x + bounding_box_extension,
            location.y + bounding_box_extension,
        )

    @staticmethod
    def format_triangles(
        triangles: list[list[np.ndarray]],
    ) -> Iterator[Triangle]:
        for triangle in triangles:
            yield [tuple(point) for point in triangle]

    def get_3d_triangles_from_2d_polygon_with_elevation(
        self, polygon: Polygon
    ) -> Iterator[Triangle]:
        for triangle in _triangulate_polygon_2d(polygon=polygon):
            yield self.elevation_handler.apply_ground_height(
                geom=triangle, offset=self.altitude_offset
            ).exterior.coords[0:3]

    @staticmethod
    def remove_layouts_overlap_from_geometry(
        geometries: Polygon | MultiPolygon,
        building_footprints: list[MultiPolygon],
    ) -> MultiPolygon:
        """
        returns part of the geometry not overlapping with the layouts
        """

        layouts_as_one_multipolygon = MultiPolygon(
            [
                polygon
                for layout in building_footprints
                for polygon in as_multipolygon(layout).geoms
            ]
        )
        return as_multipolygon(
            geometries.difference(layouts_as_one_multipolygon.minimum_rotated_rectangle)
        )

    def valid_geometry_intersected_without_z(
        self, geom: MultiPolygon | Polygon | LineString | Point
    ) -> MultiPolygon | Polygon | LineString | Point | None:
        if not self.bounding_box.intersects(geom):
            return None

        intersection = self.bounding_box.intersection(geom)
        intersection_wo_z = self.drop_z_coordinate(geom=intersection)
        valid_intersection = ensure_geometry_validity(geometry=intersection_wo_z)

        if (
            isinstance(valid_intersection, LineString)
            and isinstance(geom, LineString)
            and valid_intersection.length > 0.0
        ):
            return valid_intersection
        elif (
            isinstance(valid_intersection, Point)
            and isinstance(geom, Point)
            and not valid_intersection.is_empty
        ):
            return valid_intersection
        elif (
            isinstance(valid_intersection, (Polygon, MultiPolygon))
            and isinstance(geom, (Polygon, MultiPolygon))
            and valid_intersection.area > 0.0
        ):
            return valid_intersection
        return None

    @staticmethod
    def drop_z_coordinate(geom: Polygon):
        return transform(func=lambda x, y, *z: (x, y), geom=geom)
