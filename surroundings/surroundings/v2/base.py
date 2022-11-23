from typing import Iterator

from shapely.geometry import Point, Polygon

from common_utils.constants import REGION, SurroundingType
from dufresne.polygon.polygon_triangulate import triangulate_polygon
from surroundings.utils import SurrTrianglesType
from surroundings.v2.geometry import Geometry


class BaseElevationHandler:
    def get_elevation(self, point: Point) -> float:
        raise NotImplementedError

    def project_onto_surface(
        self, polygon: Polygon, ground_offset: float = 0.0
    ) -> Iterator[Polygon]:
        raise NotImplementedError


class BaseGeometryProvider:
    def get_geometries(self) -> Iterator[Geometry]:
        raise NotImplementedError


class BaseGeometryTransformer:
    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        raise NotImplementedError


class BaseSurroundingHandler:
    def __init__(
        self,
        bounding_box: Polygon,
        region: REGION,
        elevation_handler: BaseElevationHandler,
    ):
        self.bounding_box = bounding_box
        self.region = region
        self.elevation_handler = elevation_handler

    @property
    def geometry_provider(self) -> BaseGeometryProvider:
        raise NotImplementedError

    @property
    def geometry_transformer(self) -> BaseGeometryTransformer:
        raise NotImplementedError

    def get_surrounding_type(self, geometry: Geometry) -> SurroundingType:
        raise NotImplementedError

    def get_triangles(self) -> Iterator[SurrTrianglesType]:
        for geom in self.geometry_provider.get_geometries():
            surrounding_type = self.get_surrounding_type(geom)
            for polygon in self.geometry_transformer.transform_geometry(geom):
                for triangle in triangulate_polygon(polygon):
                    yield surrounding_type, [tuple(point) for point in triangle]


class BaseSurroundingsMixin:
    @staticmethod
    def generate_small_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ) -> Iterator[SurrTrianglesType]:
        raise NotImplementedError

    @staticmethod
    def generate_big_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ) -> Iterator[SurrTrianglesType]:
        raise NotImplementedError
