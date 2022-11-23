from typing import Iterator

from shapely.geometry import MultiPolygon, shape

from common_utils.constants import SurroundingType
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from surroundings.base_forest_surrounding_handler import (
    BushForestGenerator,
    OpenForestGenerator,
    StandardForestGenerator,
)
from surroundings.swisstopo.base_swisstopo_surrounding_handler import (
    BaseEntitySwissTopoSurroundingHandler,
)
from surroundings.utils import SurrTrianglesType
from surroundings.v2.swisstopo.constants import SWISSTLM3D


class SwissTopoForestSurroundingHandler(BaseEntitySwissTopoSurroundingHandler):
    _ENTITIES_FILE_PATH = [
        f"{SWISSTLM3D}/TLM_BB/swissTLM3D_TLM_BODENBEDECKUNG_{direction}.{{}}"
        for direction in ["OST", "WEST"]
    ]

    FOREST_GENERATORS_BY_TYPE = {
        "Wald": StandardForestGenerator,
        "Wald offen": OpenForestGenerator,
        "Gebueschwald": BushForestGenerator,
    }

    def get_triangles(
        self,
        building_footprints: list[MultiPolygon],
    ) -> Iterator[SurrTrianglesType]:
        counter = 0
        for entity in self.entities():
            coverage_type = entity["properties"]["OBJEKTART"]
            if coverage_type not in self.FOREST_GENERATORS_BY_TYPE:
                continue

            generator = self.FOREST_GENERATORS_BY_TYPE[coverage_type](
                simulation_version=self.simulation_version
            )
            forest_areas = self.valid_geometry_intersected_without_z(
                geom=shape(entity["geometry"])
            )
            forest_areas = as_multipolygon(any_shape=forest_areas)

            if forest_areas:
                counter += 1
                forest_areas = self.remove_layouts_overlap_from_geometry(
                    geometries=forest_areas, building_footprints=building_footprints
                ).geoms
                for forest_area in forest_areas:
                    for triangle in generator.get_forest_triangles(
                        tree_shape=forest_area,
                        elevation_handler=self.elevation_handler,
                        building_footprints=building_footprints,
                    ):
                        yield SurroundingType.FOREST, triangle

        logger.info(
            f"{counter} Forests successfully calculated for location {self.location}"
        )
