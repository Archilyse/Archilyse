import random
from abc import abstractmethod
from functools import cached_property
from typing import Iterator

from shapely.geometry import MultiPolygon, Point, Polygon

from common_utils.constants import SIMULATION_VERSION
from surroundings.base_elevation_handler import BaseElevationHandler
from surroundings.base_tree_surrounding_handler import (
    BushGenerator,
    StandardTreeGenerator,
)


class BaseForestGenerator:
    HEIGHT = 10.0

    @property
    @abstractmethod
    def DISTANCE(self):
        pass

    def __init__(self, simulation_version: SIMULATION_VERSION):
        self.simulation_version = simulation_version

    @cached_property
    def tree_generator(self):
        raise NotImplementedError()

    def get_tree_triangles(
        self,
        location: Point,
        ground_level: float,
        building_footprints: list[MultiPolygon],
    ) -> Iterator[list[tuple[float, float, float]]]:

        yield from self.tree_generator.get_triangles(
            tree_location=location,
            ground_level=ground_level,
            tree_height=self.HEIGHT,
            building_footprints=building_footprints,
        )

    def get_forest_triangles(
        self,
        tree_shape: Polygon,
        elevation_handler: BaseElevationHandler,
        building_footprints: list[MultiPolygon],
    ) -> Iterator[list[tuple[float, float, float]]]:
        trees_locations = self.sample_points_inside_polygon(
            polygon=tree_shape,
            resolution=self.DISTANCE,
        )
        for tree_location in trees_locations:
            # By applying the elevation to the geometry we take into account if the projection required for the tree
            tree_ground_level = elevation_handler.get_elevation(point=tree_location)
            for triangle in self.get_tree_triangles(
                location=tree_location,
                ground_level=tree_ground_level,
                building_footprints=building_footprints,
            ):
                yield triangle

    @staticmethod
    def sample_points_inside_polygon(
        polygon: Polygon, resolution: int = 5, noise_range: float = 5
    ) -> list[Point]:
        """

        - method creates uniformly distributed points + adds a random noise to each of those points
        - points outside the polygon are discarded
        - if the noise point lies outside the polygon the undisturbed uniformly distributed point is added as a fallback
        """
        random.seed(a=1)
        bounds = polygon.bounds
        xrange = int((bounds[2] - bounds[0]) / resolution) + 1
        yrange = int((bounds[3] - bounds[1]) / resolution) + 1
        p0 = [bounds[0], bounds[1]]

        points = []
        for i in range(xrange):
            for j in range(yrange):
                point = Point(p0[0] + (resolution * i), p0[1] + resolution * j)

                if polygon.intersects(point):
                    point_with_noise = Point(
                        point.x + random.uniform(-1, 1) * noise_range,
                        point.y + random.uniform(-1, 1) * noise_range,
                    )
                    points.append(
                        point_with_noise
                        if polygon.contains(point_with_noise)
                        else point
                    )

        return points


class StandardForestGenerator(BaseForestGenerator):
    DISTANCE = 10.0

    @cached_property
    def tree_generator(self):
        return StandardTreeGenerator(simulation_version=self.simulation_version)


class OpenForestGenerator(StandardForestGenerator):
    DISTANCE = 20.0


class BushForestGenerator(BaseForestGenerator):
    HEIGHT = 3.0
    DISTANCE = 10.0

    @cached_property
    def tree_generator(self):
        return BushGenerator(simulation_version=self.simulation_version)
