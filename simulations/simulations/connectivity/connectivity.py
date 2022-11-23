from functools import partial
from typing import Callable, Iterable, Optional

import networkx
from shapely.geometry import Point, Polygon

from brooks.models import SimLayout
from brooks.types import AreaType, OpeningType
from common_utils.constants import DEFAULT_GRID_RESOLUTION
from common_utils.exceptions import ConnectivityEigenFailedConvergenceException


class ConnectivitySimulator:
    EIGEN_MAX_ITER = 300
    EIGEN_TOLERANCE = 1e-5

    def __init__(
        self,
        graph: networkx.Graph,
        area_type_filter: Optional[set[AreaType]] = None,
        resolution: float = DEFAULT_GRID_RESOLUTION,
    ):
        self.connected_graph = graph
        self.area_type_filter = area_type_filter or set()
        self.resolution = resolution

    def all_simulations(self, layout: SimLayout) -> Iterable[tuple[str, Callable]]:
        sims = (
            self.closeness_centrality,
            self.betweenness_centrality,
            self.eigen_centrality,
        )
        for sim in sims:
            yield sim.__name__, sim

        #  Now the area type distances
        area_types = {a.type for a in layout.areas}
        for area_type in area_types - self.area_type_filter:
            target_areas = [a.footprint for a in layout.areas if a.type == area_type]
            yield f"{area_type.name}_distance", partial(
                self.pois_distance2pols, pols=target_areas
            )

        target_openings = [
            o.footprint for o in layout.openings if o.type == OpeningType.ENTRANCE_DOOR
        ]
        yield f"{OpeningType.ENTRANCE_DOOR.name}_distance", partial(
            self.pois_distance2pols, pols=target_openings
        )

    # ******************************
    # ****** ALGORITHMS ************
    # ******************************
    def closeness_centrality(self) -> list[float]:
        result = networkx.closeness_centrality(self.connected_graph).values()
        min_val = min(x for x in result if x > 0.0) * 0.9
        return [x if x > min_val else min_val for x in result]

    def betweenness_centrality(self) -> list[float]:
        return list(
            networkx.betweenness_centrality(
                self.connected_graph, normalized=True
            ).values()
        )

    def eigen_centrality(self) -> list[float]:
        # Increases max allowed iterations and reduce a bit tolerance
        # to ensure convergence in most cases
        try:
            return list(
                networkx.eigenvector_centrality(
                    self.connected_graph,
                    max_iter=self.EIGEN_MAX_ITER,
                    tol=self.EIGEN_TOLERANCE,
                ).values()
            )
        except networkx.PowerIterationFailedConvergence:
            raise ConnectivityEigenFailedConvergenceException

    def pois_distance2pols(self, pols: list[Polygon]) -> list[float]:
        for buffer in (0, 0.1, 0.2, 0.3):
            target_nodes = [
                n
                for n in self.connected_graph.nodes
                if any(a.buffer(buffer).contains(Point(n[:2][::-1])) for a in pols)
            ]
            if target_nodes:
                break

        return self.pois_distance(target_nodes)

    def pois_distance(self, target_nodes: list[tuple[float]]) -> list[float]:
        if not target_nodes:
            return [
                len(self.connected_graph.nodes) * self.resolution
                for _ in self.connected_graph.nodes
            ]

        # 1st we contract all target nodes into one
        supernode = target_nodes[0]
        G_tmp = self.connected_graph
        for node in target_nodes[1:]:
            G_tmp = networkx.contracted_nodes(G_tmp, supernode, node, self_loops=False)

        # then we compute all shortest paths to this node
        shortest_distances = networkx.shortest_path_length(G_tmp, target=supernode)
        max_distance = (
            min(
                len(self.connected_graph.nodes),
                max(x for x in shortest_distances.values()),
            )
            + 1
        )

        target_node_set = set(target_nodes)
        return [
            shortest_distances.get(node, max_distance) * self.resolution
            if node not in target_node_set
            else 0
            for node in self.connected_graph.nodes
        ]
