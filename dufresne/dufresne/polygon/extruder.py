from typing import List, Tuple

import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

from dufresne.points import get_points
from dufresne.polygon.polygon_triangulate import triangulate_polygon


class Extruder:
    """class for building generic houses"""

    @classmethod
    def get_triangles(
        cls, polygon: Polygon, ground_level: float, height: float
    ) -> List[Tuple[float, float, float]]:
        """get the triangle

        Returns:
            List[List[float, float, float]]: list of triangles
        """
        polygon = orient(polygon)
        exterior_points = np.asanyarray(get_points(polygon)[0])[:, :2]
        triangles = []
        triangles.extend(
            cls._get_wall_triangles(
                exterior_points=exterior_points,
                height=height,
                ground_level=ground_level,
            )
        )
        triangles.extend(
            cls._get_rooftop_and_floor(
                exterior_points=exterior_points,
                height=height,
                ground_level=ground_level,
            )
        )
        return triangles

    @classmethod
    def _get_wall_triangles(
        cls, exterior_points: np.array, ground_level: float, height: float
    ) -> List[Tuple[float, float, float]]:
        """get the wall triangles

        Returns:
            List[List[float, float, float]]: list of triangles
        """
        triangles = []
        for i in range(len(exterior_points) - 1):
            p1 = np.append(exterior_points[i], ground_level).tolist()
            p2 = np.append(exterior_points[i + 1], ground_level).tolist()
            p3 = np.append(exterior_points[i + 1], height).tolist()
            p4 = np.append(exterior_points[i], height).tolist()
            triangle1 = [p1, p2, p3]
            triangles.append(triangle1)
            triangle2 = [p3, p4, p1]
            triangles.append(triangle2)
        return triangles

    @classmethod
    def _get_rooftop_and_floor(
        cls, exterior_points: np.array, ground_level: float, height: float
    ) -> List[Tuple[float, float, float]]:
        """get the rooftop triangles of a building

        Returns:
            List[List[float, float, float]]: list of triangles
        """
        polygon = Polygon(exterior_points)
        triangle_list = []
        triangles = triangulate_polygon(polygon)
        for triangle in triangles:
            points = triangle[:3]
            floor = list(map(lambda x: np.append(x, ground_level).tolist(), points))
            triangle_list.append(floor)

        for triangle in triangles:
            rooftop = list(map(lambda x: np.append(x, height).tolist(), triangle))
            triangle_list.append(rooftop)
        return triangle_list
