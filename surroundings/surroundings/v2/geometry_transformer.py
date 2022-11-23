from typing import Iterator, Optional

from shapely.geometry import Point, Polygon

from brooks.util.geometry_ops import get_line_strings, get_polygons
from common_utils.constants import SIMULATION_VERSION
from dufresne.linestring_add_width import LINESTRING_EXTENSION, add_width_to_linestring
from dufresne.polygon.polygon_extrude_triangles import (
    get_triangles_from_extruded_polygon,
)
from surroundings.base_forest_surrounding_handler import BaseForestGenerator
from surroundings.base_tree_surrounding_handler import StandardTreeGenerator
from surroundings.v2.base import BaseElevationHandler, BaseGeometryTransformer
from surroundings.v2.constants import DEFAULT_RIVER_WIDTH
from surroundings.v2.geometry import Geometry


class GroundCoveringPolygonTransformer(BaseGeometryTransformer):
    def __init__(self, elevation_handler: BaseElevationHandler, ground_offset: float):
        self.ground_offset = ground_offset
        self.elevation_handler = elevation_handler

    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        for pol in get_polygons(geometry.geom):
            yield from self.elevation_handler.project_onto_surface(
                polygon=pol, ground_offset=self.ground_offset
            )


class GroundCoveringLineStringTransformer(BaseGeometryTransformer):
    def __init__(self, elevation_handler: BaseElevationHandler, ground_offset: float):
        self.ground_offset = ground_offset
        self.elevation_handler = elevation_handler

    def get_width(self, geometry: Geometry) -> float:
        raise NotImplementedError

    def get_extension_type(self, geometry: Geometry) -> LINESTRING_EXTENSION:
        return LINESTRING_EXTENSION.SYMMETRIC

    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        width = self.get_width(geometry)
        extension_type = self.get_extension_type(geometry)
        for linestring in get_line_strings(geometry.geom):
            for polygon in get_polygons(
                add_width_to_linestring(
                    line=linestring,
                    width=width,
                    extension_type=extension_type,
                )
            ):
                yield from self.elevation_handler.project_onto_surface(
                    polygon=polygon, ground_offset=self.ground_offset
                )


class RiverLinesGeometryTransformer(GroundCoveringLineStringTransformer):
    def get_width(self, geometry: Geometry) -> float:
        return DEFAULT_RIVER_WIDTH


class NoTransformer(BaseGeometryTransformer):
    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        yield from get_polygons(geometry.geom)


class ForestGeometryTransformer(GroundCoveringPolygonTransformer):
    def get_forest_generator(self, geometry: Geometry) -> Optional[BaseForestGenerator]:
        raise NotImplementedError

    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        if forest_generator := self.get_forest_generator(geometry=geometry):
            for forest_polygon in get_polygons(geometry.geom):
                yield from map(
                    Polygon,
                    forest_generator.get_forest_triangles(
                        tree_shape=forest_polygon,
                        elevation_handler=self.elevation_handler,
                        building_footprints=[],
                    ),
                )
        else:
            yield from super(ForestGeometryTransformer, self).transform_geometry(
                geometry=geometry
            )


class TreeGeometryTransformer(BaseGeometryTransformer):
    def __init__(self, elevation_handler: BaseElevationHandler):
        self.elevation_handler = elevation_handler

    def get_height(self, geometry: Geometry):
        raise NotImplementedError

    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        ground_level = self.elevation_handler.get_elevation(geometry.geom)
        yield from map(
            Polygon,
            StandardTreeGenerator(
                simulation_version=SIMULATION_VERSION.PH_2022_H1
            ).get_triangles(
                tree_location=geometry.geom,
                ground_level=ground_level,
                tree_height=self.get_height(geometry=geometry),
                building_footprints=[],
            ),
        )


class BuildingFootprintTransformer(BaseGeometryTransformer):
    def __init__(self, elevation_handler: BaseElevationHandler):
        self.elevation_handler = elevation_handler

    def _get_min_max_ground_levels(self, geometry: Geometry) -> tuple[float, float]:
        z_values = [
            self.elevation_handler.get_elevation(Point(x, y))
            for footprint in get_polygons(geometry.geom)
            for x, y in footprint.exterior.coords
        ]
        return min(z_values), max(z_values)

    def get_height(self, geometry: Geometry) -> float:
        raise NotImplementedError

    def transform_geometry(self, geometry: Geometry) -> Iterator[Polygon]:
        min_ground_level, max_ground_level = self._get_min_max_ground_levels(
            geometry=geometry
        )
        height = max_ground_level + self.get_height(geometry=geometry)
        for polygon in get_polygons(geometry=geometry.geom):
            yield from map(
                Polygon,
                get_triangles_from_extruded_polygon(
                    polygon=polygon,
                    ground_level=min_ground_level - 2,  # 2m arbitrary underground
                    height=height,
                ),
            )
