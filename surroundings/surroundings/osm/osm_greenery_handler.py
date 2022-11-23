from typing import Iterator

from shapely.geometry import MultiPolygon

from common_utils.constants import SurroundingType
from dufresne.polygon.utils import as_multipolygon
from surroundings.base_forest_surrounding_handler import (
    BushForestGenerator,
    OpenForestGenerator,
    StandardForestGenerator,
)
from surroundings.base_polygon_surrounding_handler_mixin import (
    BasePolygonSurroundingHandlerMixin,
)

from ..utils import SurrTrianglesType, Triangle
from .base_osm_surrounding_handler import BaseEntityOSMSurroundingHandler


class OSMParksHandler(
    BasePolygonSurroundingHandlerMixin, BaseEntityOSMSurroundingHandler
):
    # Provides polygons for woods and vegetation areas. They'll be flat in the ground
    _ENTITIES_FILE_PATH = "gis_osm_landuse_a_free_1.shp"

    VALID_ENTITY_TYPES = {"park", "recreation_ground"}

    surrounding_type = SurroundingType.PARKS

    def custom_entity_validity_check(self, entity: dict) -> bool:
        return entity["properties"]["fclass"] in self.VALID_ENTITY_TYPES


class OSMForestHandler(
    BasePolygonSurroundingHandlerMixin, BaseEntityOSMSurroundingHandler
):
    VALID_ENTITY_TYPES = {  # Generator
        "forest": StandardForestGenerator,
        "national_park": OpenForestGenerator,
        "nature_reserve": OpenForestGenerator,  # Not sure about this one...
        "vineyard": BushForestGenerator,
        "orchard": BushForestGenerator,
        "grass": None,
        "heath": None,
        "meadow": None,
    }

    # Provides polygons for woods and vegetation areas
    _ENTITIES_FILE_PATH = "gis_osm_landuse_a_free_1.shp"
    surrounding_type = SurroundingType.FOREST

    def custom_entity_validity_check(self, entity: dict) -> bool:
        return entity["properties"]["fclass"] in self.VALID_ENTITY_TYPES

    def triangulate_forest(
        self,
        valid_multipolygon: MultiPolygon,
        generator_class,
        building_footprints: list[MultiPolygon],
    ) -> Iterator[Triangle]:
        for forest_area in valid_multipolygon.geoms:
            for triangle in generator_class(
                simulation_version=self.simulation_version
            ).get_forest_triangles(
                tree_shape=forest_area,
                elevation_handler=self.elevation_handler,
                building_footprints=building_footprints,
            ):
                yield triangle

    def get_triangles(
        self, building_footprints: list[MultiPolygon]
    ) -> Iterator[SurrTrianglesType]:
        for entity in self.filtered_entities():
            generator_class = self.VALID_ENTITY_TYPES[entity.entity_class]
            if generator_class is None:
                for polygon in as_multipolygon(entity.geometry).geoms:
                    yield from self._triangulate_polygon(polygon=polygon)
            else:
                for triangle in self.triangulate_forest(
                    generator_class=generator_class,
                    building_footprints=building_footprints,
                    valid_multipolygon=as_multipolygon(entity.geometry),
                ):
                    yield self.surrounding_type, triangle
