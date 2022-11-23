from typing import Dict, List, Set

from networkx import Graph, connected_components

from brooks import SpaceConnector
from brooks.models import SimLayout, SimSpace
from brooks.types import AreaType, OpeningType


class LayoutSplitter:
    @staticmethod
    def _build_graph_connected_spaces(layout: SimLayout) -> Graph:
        door_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=layout.openings_by_type[OpeningType.DOOR],
            spaces_or_areas=layout.spaces,
        )
        edges = []
        for source_space_id, sinks in door_connections.items():
            for sink in sinks:
                for _, sink_space_id in sink.items():
                    edges.append((source_space_id, sink_space_id))

        shaft_connections = SpaceConnector.shafts_nearest_space_connections(
            layout=layout
        )
        edges.extend(shaft_connections)

        all_valid_nodes = [
            sp.id
            for sp in layout.spaces
            if not {AreaType.VOID, AreaType.OUTDOOR_VOID}.intersection(
                {area.type for area in sp.areas}
            )
        ]

        graph = Graph()
        graph.add_nodes_from(all_valid_nodes)
        graph.add_edges_from(edges)
        return graph

    @staticmethod
    def _filter_public_spaces_connecting_multiple_entrances(
        layout: SimLayout, connected_spaces: List[Set[str]]
    ) -> List[Set[str]]:
        entrance_door_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=layout.openings_by_type[OpeningType.ENTRANCE_DOOR],
            spaces_or_areas=layout.spaces,
        )
        space_id_to_scc: Dict[str, int] = {
            space_id: i for i, scc in enumerate(connected_spaces) for space_id in scc
        }
        valid_unit_sccs: List[Set[str]] = []
        for scc in connected_spaces:
            connected_sccs_via_entrance_doors = set()
            for space_id in scc:
                for sink in entrance_door_connections[space_id]:
                    connected_sccs_via_entrance_doors |= {
                        space_id_to_scc[sink_space_id]
                        for sink_space_id in sink.values()
                        if sink_space_id in space_id_to_scc
                    }

            if len(connected_sccs_via_entrance_doors) <= 1:
                valid_unit_sccs.append(scc)
        return valid_unit_sccs

    @classmethod
    def _filter_public_spaces_by_areas(
        cls, layout: SimLayout, connected_spaces: List[Set[str]]
    ) -> List[Set[str]]:
        """If a group of connected areas only contains area types of public spaces then is filtered out"""
        valid_unit_sccs: List[Set[str]] = []
        area_types_by_space_id = {
            sp_id: {a.type for a in space.areas}
            for sp_id, space in layout.spaces_by_id.items()
        }
        invalid_isolated_area_types = {
            AreaType.SHAFT,
            AreaType.VOID,
            AreaType.OUTDOOR_VOID,
            AreaType.STAIRCASE,
            AreaType.ELEVATOR,
            AreaType.CORRIDOR,
            AreaType.STOREROOM,
        }
        for scc in connected_spaces:
            area_types_in_sccs = {
                area_type
                for sp_id in scc
                for area_type in area_types_by_space_id[sp_id]
            }
            if len(scc) != len(
                area_types_in_sccs.intersection(invalid_isolated_area_types)
            ):
                valid_unit_sccs.append(scc)

        return valid_unit_sccs

    @classmethod
    def split_layout(cls, layout: SimLayout) -> List[List[SimSpace]]:
        graph = cls._build_graph_connected_spaces(layout=layout)

        # Compute connected components
        connected_spaces = [z for z in connected_components(graph)]

        # Now we remove SCCs that have entrance doors to more than one
        # other SCC (public spaces)
        valid_unit_spaces = cls._filter_public_spaces_connecting_multiple_entrances(
            layout=layout,
            connected_spaces=connected_spaces,
        )
        valid_unit_spaces = cls._filter_public_spaces_by_areas(
            layout=layout,
            connected_spaces=valid_unit_spaces,
        )
        spaces_index: Dict[str, SimSpace] = {space.id: space for space in layout.spaces}
        return [
            [spaces_index[node] for node in component_nodes]
            for component_nodes in sorted(
                valid_unit_spaces, key=lambda x: len(x), reverse=True
            )
        ]
