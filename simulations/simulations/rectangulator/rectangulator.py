from typing import List

import numpy as np
from shapely import wkt
from shapely.errors import TopologicalError
from shapely.geometry import LineString, Polygon
from shapely.geometry.polygon import orient

from common_utils.exceptions import RectangleNotCalculatedException
from dufresne.points import get_points
from dufresne.polygon.polygon_angles_vectors import get_polygon_normed_vectors
from dufresne.polygon.polygon_parse_intersection import parse_intersection
from dufresne.rotation.vector_rotate_left import rotate_vec_left


class DeterministicRectangulator:
    """
    this class tries to find a big rectangle in a polygon.
    this algorithm is based on the knowledge that most of the _angles in rooms
    (where this algorithm should be used) of buildings are n*90 where n is
    an integer - in this very case, this algorithm is tends to be optimal
    (if _EPS/resolution is small)
    """

    def __init__(
        self,
        polygon: Polygon,
        distance_from_wall: float = 0.01,
        resolution: int = 25,
    ):
        """Initialisation of the class

        Args:
            polygon: a shapely polygon where the rectangle should be placed
            distance_from_wall: distance from the wall
            resolution: scatter _resolution (the )
        """
        self.polygon = orient(polygon)

        self._points = np.array(get_points(self.polygon)[0])
        self._normed_vectors = get_polygon_normed_vectors(self.polygon)
        self._solutions: List[Polygon] = []
        self._EPS = distance_from_wall
        self._resolution = resolution

    def get_biggest_rectangle(self) -> Polygon:
        """finds the biggest_rectangle rectangle

        Returns:
            rectangle (shapely.Polygon): biggest_rectangle rectangle in self._solutions
        """
        self._compute_rectangles()
        maximum = 0
        biggest = None
        for rectangle in self._solutions:
            area = rectangle.area
            if area > maximum:
                maximum = area
                biggest = rectangle
        if not biggest:
            raise RectangleNotCalculatedException(
                f"Could not calculate maximum rectangle in the polygon {wkt.dumps(self.polygon)}"
            )
        return biggest

    def get_possible_solutions(self) -> List[Polygon]:
        self._compute_rectangles()
        return self._solutions

    def _compute_rectangles(self):
        """finds the all biggest_rectangle _solutions per wall"""
        for i in range(1, len(self._points)):
            distance_wall = (
                self._normed_vectors[i] * self._EPS
                + rotate_vec_left(self._normed_vectors[i]) * self._EPS
            )
            pos = self._points[i] + distance_wall
            self._insert_rectangle(pos, self._normed_vectors[i])

    def _insert_rectangle(self, pos, vec):
        """inserts the rectangle

        starts at starting point and follows the wall until next corner
        scatters via _resolution parameter through that vector and
        evaluates the perpendicular lines from there (called tentacles)
        this evaluation is done via the lengths of those tentacles

        Args:
            pos: starting position (from the vector)
            vec: shifted vector of the wall
        """
        # perpendicular lines from vec

        extension = (
            max(
                self.polygon.bounds[3] - self.polygon.bounds[1],
                self.polygon.bounds[2] - self.polygon.bounds[0],
            )
            * 2
        )
        starting_point = pos.copy()
        tentacle = rotate_vec_left(vec) * extension
        ray = LineString([pos, pos + vec * extension])
        if not ray.is_valid:
            return
        intersection = ray.intersection(self.polygon)
        # searches for the line until the first intersection (next wall)
        line = parse_intersection(intersection)
        if not line:
            return
        # calculates every point where a tentacle starts
        end_point = np.array(line.coords[1]) - vec * self._EPS
        scatter_length = np.linalg.norm(starting_point - end_point)
        x_grid = np.linspace(0, scatter_length, self._resolution)
        # calculates the lengths - and evaluates them
        lengths = []
        for i in range(len(x_grid)):
            pos = starting_point + x_grid[i] * vec
            line = LineString([pos, pos + tentacle])
            try:
                intersection = line.intersection(self.polygon)
            except TopologicalError:
                # TODO Investigate why this would happen?
                return
            line = parse_intersection(intersection)
            if not line:
                return
            lengths.append(line.length)

        if len(x_grid) < 5:
            return
        self._evaluate_tentacles(lengths, x_grid, starting_point, vec)

    def _evaluate_tentacles(self, lengths, x_grid, hinge, vec):
        """evaluates the rectangle

        tries to fit in the biggest_rectangle rectangle via the lengths of the tentacles

        Args:
            lengths: list of lenghts
            x_grid: grid of all the starting position of the tentacles
                     (these are relative coordinates)
            vec: the direction of the xgrid axis
        """
        minima = []
        # key: value of the x_grid value: distance
        starting_points = dict()
        for i in range(1, len(lengths)):
            delta = abs(lengths[i] - lengths[i - 1])
            if delta > 0.01 and minima:
                minimum = min(minima)
                minima = []
                starting_points.update({i: minimum - self._EPS})
            minima.append(lengths[i])
        # finding the last starting_point
        if minima:
            minimum = min(minima)
            starting_points.update({i: minimum - self._EPS})

        maximum = 0
        lengths = np.array(lengths)
        for key, value in starting_points.items():
            bools = lengths > value
            # searching to the right if there is a wall
            for i in range(key, len(bools)):
                if not bools[i]:
                    break
            points = np.zeros((4, 2))
            points[1] = [x_grid[i - 1], value]
            points[0] = [x_grid[i - 1], 0]
            # searching to the left if there is a wall
            for i in range(key - 1, 0, -1):
                if not bools[i]:
                    break
            points[2] = [x_grid[i + 1], value]
            points[3] = [x_grid[i + 1], 0]
            polygon = orient(Polygon(points))
            area = polygon.area
            if area > maximum:
                biggestPoints = points
                maximum = area

        if maximum:
            #    transformation
            M = np.array([[vec[0], -vec[1]], [vec[1], vec[0]]])
            for i in range(len(biggestPoints)):
                biggestPoints[i] = np.dot(M, biggestPoints[i])
            biggestPoints += hinge
            biggestRectangle = Polygon(biggestPoints)
            self._solutions.append(biggestRectangle)
