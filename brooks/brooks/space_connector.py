from collections import defaultdict
from typing import Dict, List, Set, Tuple, Union

from pygeos import Geometry, from_shapely, intersects

from brooks.models import SimArea, SimLayout, SimOpening, SimSpace
from brooks.types import AreaType


class SpaceConnector:
    @classmethod
    def get_connected_spaces_using_doors(
        cls,
        doors: Set[SimOpening],
        spaces_or_areas: Union[Set[SimSpace], Set[SimArea]],
    ) -> Tuple[Dict[str, List[Dict[str, str]]], List[str]]:
        """Checks which spaces are connected to each other by a door.

        A line is drawn through the door:
         - If a space intersects with it, it is connected by this door.
         - If two spaces are connected to the same door, they are connected to each other.
         - If more than two spaces are intersecting with the line, only the two spaces which are nearest to the
         door are considered.
        """
        space_connections: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        doors_not_connected = []
        spaces_ordered_list = list(spaces_or_areas)
        pygeos_spaces = from_shapely(
            [entity.footprint for entity in spaces_ordered_list]
        )
        for door in doors:
            intersecting_spaces = cls.get_intersecting_spaces_or_areas(
                opening=door,
                spaces_or_areas_list=spaces_ordered_list,
                pygeos_spaces=pygeos_spaces,
            )
            if len(intersecting_spaces) > 1:
                space_closer_to_door_polygon_and_id = sorted(
                    [
                        (space.footprint.distance(door.footprint), space.id)
                        for space in intersecting_spaces
                    ],
                    key=lambda x: x[0],
                )
                space_connections[space_closer_to_door_polygon_and_id[0][1]].append(
                    {door.id: space_closer_to_door_polygon_and_id[1][1]}
                )
                space_connections[space_closer_to_door_polygon_and_id[1][1]].append(
                    {door.id: space_closer_to_door_polygon_and_id[0][1]}
                )
            else:
                doors_not_connected.append(door.id)

        return space_connections, doors_not_connected

    @classmethod
    def get_connected_spaces_or_areas_per_door(
        cls,
        doors: Set[SimOpening],
        spaces_or_areas: Union[Set[SimSpace], Set[SimArea]],
    ) -> Dict[str, List[str]]:
        door_space_connection: Dict[str, List[str]] = dict()
        spaces_ordered_list = list(spaces_or_areas)
        pygeos_spaces = from_shapely(
            [entity.footprint for entity in spaces_ordered_list]
        )
        for door in doors:
            entity_id_intersecting = [
                entity.id
                for entity in cls.get_intersecting_spaces_or_areas(
                    opening=door,
                    spaces_or_areas_list=spaces_ordered_list,
                    pygeos_spaces=pygeos_spaces,
                )
            ]
            door_space_connection[door.id] = entity_id_intersecting
        return door_space_connection

    @classmethod
    def get_intersecting_spaces_or_areas(
        cls,
        opening: SimOpening,
        spaces_or_areas_list: List,
        pygeos_spaces: List[Geometry],
    ) -> Set[Union[SimSpace, SimArea]]:
        reference_footprint = opening.reference_geometry()
        separator_intersects_indexes = intersects(
            from_shapely(reference_footprint),
            pygeos_spaces,
        )
        return {
            spaces_or_areas_list[index]
            for index in separator_intersects_indexes.nonzero()[0]
        }

    @staticmethod
    def shafts_nearest_space_connections(layout: SimLayout) -> List[Tuple[str, str]]:
        shaft_edges = []
        shaft_spaces = [
            sp for sp in layout.spaces if AreaType.SHAFT in {a.type for a in sp.areas}
        ]
        if non_shaft_spaces := [
            sp
            for sp in layout.spaces
            if not any(
                [
                    area_type in {a.type for a in sp.areas}
                    for area_type in (AreaType.SHAFT, AreaType.VOID)
                ]
            )
        ]:
            for shaft_space in shaft_spaces:
                closest_space = sorted(
                    non_shaft_spaces,
                    key=lambda x: x.footprint.distance(shaft_space.footprint),
                )[0]
                shaft_edges.append((closest_space.id, shaft_space.id))
        return shaft_edges
