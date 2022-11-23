import itertools
from collections import namedtuple
from functools import cached_property
from typing import Iterator, List, Tuple

import networkx
import numpy as np
from shapely.geometry import LineString, Point, Polygon

Hexagon = namedtuple("Hexagon", ["index", "centroid"])


class Hexagonizer:
    COS_30 = 0.8660254037844387  # np.cos(np.deg2rad(30))

    @classmethod
    def get_hexagons(
        cls, pol: Polygon, resolution: float, z_coord: float = 0
    ) -> Iterator[Hexagon]:
        """
        Returns: A tuple containing the i, j position of the hexagon, and the x, y, z coordinates
        """
        bounds = pol.bounds
        width = int((bounds[2] - bounds[0]) / resolution) + 1
        height = int((bounds[3] - bounds[1]) / (resolution * cls.COS_30)) + 1
        origin = [bounds[0], bounds[3]]
        for i in range(height):
            for j in range(width):
                position = (
                    cls._get_position_from_hex_index(i=i, j=j, resolution=resolution)
                    + origin
                )
                # Intersects consider both interiors and boundaries
                if pol.intersects(Point(*position)):
                    yield Hexagon(
                        index=(i, j),
                        centroid=(position[0], position[1], z_coord),
                    )

    @classmethod
    def _get_position_from_hex_index(
        cls,
        i: int,
        j: int,
        resolution: float,
    ) -> np.ndarray:
        """calculate the position from 2d array index to position

        the convention used here is a so called odd-r hex-grid
        for further documentation please consider:
        https://www.redblobgames.com/grids/hexagons/

        Args:
            i (int): first index of a 2d array (y-direction)
            j (int): second index of a 2d array (x-direction)
            resolution (float): radius of the hexagon

        Returns:
            Tuple[float, float]: position of the point
        """
        return np.array([(i % 2) / 2 + j, -i * cls.COS_30]) * resolution


class HexagonizerGraph:
    def __init__(self, polygon: Polygon, resolution: float):
        self.hexagon_grid = Hexagonizer.get_hexagons(pol=polygon, resolution=resolution)
        self.pol = polygon

    @cached_property
    def connected_graph(self) -> networkx.Graph:
        connected_graph = networkx.Graph()
        connected_graph.add_nodes_from(
            [((y, x, z), {"index": index}) for index, (x, y, z) in self.hexagon_grid]
        )
        self._add_neighbour_edges(graph=connected_graph, pol=self.pol)

        # clean unconnected nodes
        self._clean_unconnected_nodes(connected_graph)

        return connected_graph

    @property
    def obs_points(self) -> List:
        return list(self.connected_graph.nodes)

    @classmethod
    def _add_neighbour_edges(cls, graph: networkx.Graph, pol: Polygon):
        for node1, node2 in itertools.combinations(graph.nodes, 2):
            if cls._is_neighbour(graph, node1, node2) and cls._is_connected(
                node1, node2, pol
            ):
                graph.add_edge(node1, node2)

    @staticmethod
    def _is_neighbour(
        graph: networkx.Graph, node1: Tuple[float], node2: Tuple[float]
    ) -> bool:
        i1, j1 = graph.nodes[node1]["index"]
        i2, j2 = graph.nodes[node2]["index"]
        return abs(i1 - i2) <= 1 and abs(j1 - j2) <= 1

    @staticmethod
    def _is_connected(node1: Tuple[float], node2: Tuple[float], pol: Polygon) -> bool:
        connection = LineString([node1[:2][::-1], node2[:2][::-1]])  # x,y are reversed
        return connection.within(pol)

    @staticmethod
    def _clean_unconnected_nodes(connected_graph):
        connected_graph.remove_nodes_from(
            [n for n in connected_graph.nodes if not connected_graph.edges(n)]
        )
