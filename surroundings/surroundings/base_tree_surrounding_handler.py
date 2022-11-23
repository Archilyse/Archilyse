from typing import Iterator, Optional

from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Point, Polygon, box

from common_utils.constants import SIMULATION_VERSION
from common_utils.logger import logger
from dufresne.polygon.polygon_extrude_triangles import (
    get_triangles_from_extruded_polygon,
)
from surroundings.utils import Triangle


class BaseTreeGenerator:
    _CROWN_HEIGHT_RATIO: float

    def __init__(
        self, simulation_version: SIMULATION_VERSION = SIMULATION_VERSION.PH_01_2021
    ):
        self.simulation_version = simulation_version

    @classmethod
    def _get_trunk_radius(
        cls, tree_height: float, simulation_version: SIMULATION_VERSION
    ) -> Optional[float]:
        return None

    @classmethod
    def _get_crown_radius(cls, tree_height: float) -> float:
        raise NotImplementedError

    @classmethod
    def _get_trunk_height(cls, tree_height: float) -> float:
        return tree_height * (1 - cls._CROWN_HEIGHT_RATIO)

    @classmethod
    def _get_footprint(cls, tree_location: Point, radius: float) -> Polygon:
        footprint = box(-radius, -radius, radius, radius)
        return translate(footprint, xoff=tree_location.x, yoff=tree_location.y)

    @classmethod
    def geometry_intersects_with_layouts(
        cls,
        polygon: Polygon,
        building_footprints: Optional[list[MultiPolygon]] = None,
    ) -> bool:
        if isinstance(building_footprints, list) and any(
            polygon.intersects(layout) for layout in building_footprints
        ):
            logger.debug(
                f"Tree at location {polygon} overlaps with building. Discarding"
            )
            return True
        return False

    def get_trunk_triangles(
        self,
        ground_level: float,
        tree_height: float,
        tree_location: Point,
        building_footprints: list[MultiPolygon | Polygon] = None,
    ) -> Iterator[Triangle]:
        trunk_height = self._get_trunk_height(tree_height=tree_height)
        trunk_radius = self._get_trunk_radius(
            tree_height=tree_height, simulation_version=self.simulation_version
        )
        trunk_footprint = self._get_footprint(
            tree_location=tree_location, radius=trunk_radius
        )
        if not self.geometry_intersects_with_layouts(
            polygon=trunk_footprint, building_footprints=building_footprints
        ):
            yield from get_triangles_from_extruded_polygon(
                polygon=trunk_footprint,
                ground_level=ground_level,
                height=ground_level + trunk_height,
            )

    def get_crown_triangles(
        self,
        ground_level: float,
        tree_height: float,
        tree_location: Point,
        building_footprints: Optional[list[MultiPolygon | Polygon]] = None,
    ) -> Iterator[Triangle]:
        crown_radius = self._get_crown_radius(tree_height=tree_height)
        crown_footprint = self._get_footprint(
            tree_location=tree_location, radius=crown_radius
        )
        trunk_height = self._get_trunk_height(tree_height=tree_height)
        if not self.geometry_intersects_with_layouts(
            polygon=crown_footprint, building_footprints=building_footprints
        ):
            yield from get_triangles_from_extruded_polygon(
                polygon=crown_footprint,
                ground_level=trunk_height + ground_level,
                height=tree_height + ground_level,
            )

    def get_triangles(
        self,
        tree_location: Point,
        ground_level: float,
        building_footprints: list[MultiPolygon | Polygon] = None,
        tree_height: float = 10.0,
    ) -> Iterator[Triangle]:
        if self._CROWN_HEIGHT_RATIO < 1.0:
            yield from self.get_trunk_triangles(
                ground_level=ground_level,
                tree_height=tree_height,
                tree_location=tree_location,
                building_footprints=building_footprints,
            )
        yield from self.get_crown_triangles(
            ground_level=ground_level,
            tree_height=tree_height,
            tree_location=tree_location,
            building_footprints=building_footprints,
        )


class StandardTreeGenerator(BaseTreeGenerator):
    _TRUNK_DIAMETER_RATIO: float = 0.05
    _CROWN_DIAMETER_RATIO: float = 0.4
    _CROWN_HEIGHT_RATIO: float = 0.5

    @classmethod
    def _get_trunk_radius(
        cls, tree_height: float, simulation_version: SIMULATION_VERSION
    ) -> float:
        if simulation_version in {
            SIMULATION_VERSION.EXPERIMENTAL,
            SIMULATION_VERSION.PH_2022_H1,
        }:
            return tree_height * cls._TRUNK_DIAMETER_RATIO / 2
        return 1.0

    @classmethod
    def _get_crown_radius(cls, tree_height: float) -> float:
        return tree_height * cls._CROWN_DIAMETER_RATIO / 2


class BushGenerator(BaseTreeGenerator):
    _CROWN_HEIGHT_RATIO: float = 1.0
    _CROWN_RADIUS: float = 0.5

    @classmethod
    def _get_crown_radius(cls, tree_height: float) -> float:
        return cls._CROWN_RADIUS
