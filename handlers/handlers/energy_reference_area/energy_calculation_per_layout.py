from collections import defaultdict

from shapely.affinity import scale
from shapely.geometry import CAP_STYLE, JOIN_STYLE, LineString, Point, Polygon
from shapely.ops import orient, unary_union
from shapely.validation import make_valid

from brooks.classifications import UnifiedClassificationScheme
from brooks.constants import GENERIC_HEIGHTS
from brooks.models import SimArea, SimLayout
from brooks.types import AreaType, SeparatorType, SIACategory
from common_utils.constants import (
    AREA_BUFFER_FOR_WALLS_INTERSECTION_IN_M,
    AREA_BUFFER_TO_INCLUDE_WALLS_IN_M,
)
from dufresne.polygon import get_sides_as_lines_by_length
from handlers.energy_reference_area.constants import AREA_TYPE_ERA_MAPPING
from handlers.energy_reference_area.models import EnergyAreasStatsPerFloor


class EnergyAreaStatsLayout:
    @classmethod
    def energy_area_in_layout(
        cls, layout: SimLayout, area_ids_part_of_residential_units: set[int]
    ) -> EnergyAreasStatsPerFloor:
        era_areas_by_type, non_era_areas_by_type = cls._areas_by_era_and_type(
            layout=layout
        )

        walls = [separator.footprint for separator in layout.separators]
        walls_union = unary_union(walls)

        era_wall_area = cls._walls_area_part_of_era(
            walls=walls,
            era_areas=[
                area.footprint for areas in era_areas_by_type.values() for area in areas
            ],
        )

        return EnergyAreasStatsPerFloor(
            total_era_area=sum(
                [
                    area.footprint.area
                    for areas in era_areas_by_type.values()
                    for area in areas
                ]
            )
            + era_wall_area,
            total_non_era_area=sum(
                [
                    area.footprint.area
                    for areas in non_era_areas_by_type.values()
                    for area in areas
                ]
            )
            + walls_union.area
            - era_wall_area,
            era_wall_area=era_wall_area,
            era_areas={
                area_type.name: [area.footprint.area for area in areas]
                for area_type, areas in era_areas_by_type.items()
            },
            non_era_areas={
                area_type.name: [area.footprint.area for area in areas]
                for area_type, areas in non_era_areas_by_type.items()
            },
            # Default value
            floor_height=GENERIC_HEIGHTS[SeparatorType.WALL][1],
        )

    @classmethod
    def _areas_by_era_and_type(
        cls, layout: SimLayout
    ) -> tuple[
        defaultdict[AreaType, list[SimArea]], defaultdict[AreaType, list[SimArea]]
    ]:
        era_areas_by_type = defaultdict(list)
        non_era_areas_by_type = defaultdict(list)

        for area_type, areas in layout.areas_by_type.items():
            for area in areas:
                if cls._is_era_area(
                    area=area,
                ):
                    era_areas_by_type[area_type].append(area)
                else:
                    non_era_areas_by_type[area_type].append(area)
        return era_areas_by_type, non_era_areas_by_type

    @classmethod
    def _is_era_area(cls, area: SimArea):
        if area.type == AreaType.STOREROOM and area.footprint.area < 10:
            return True

        if area.type in (AreaType.VOID, AreaType.SHAFT) and area.footprint.area <= 5:
            return True

        else:
            return AREA_TYPE_ERA_MAPPING[area.type.name]

    @classmethod
    def _walls_area_part_of_era(
        cls, walls: list[Polygon], era_areas: list[Polygon]
    ) -> float:
        return (
            unary_union(walls)
            .intersection(
                unary_union(
                    [
                        cls._get_area_perimeters_offset_by_adjacent_walls(
                            area=area, walls=walls
                        )
                        for area in era_areas
                    ]
                )
            )
            .area
        )

    @classmethod
    def _get_area_perimeters_offset_by_adjacent_walls(
        cls, area: Polygon, walls: list[Polygon]
    ) -> Polygon:
        """
        0. simplify the area to avoid multiple small side segements
        1. orient the area exterior coordinates to be clockwise
        2. for each pair of coordinates (line) get the width of the adjacent wall
        3. replace line coordinates with its parallel offset by wall width
        4. return the new area perimeters
        """
        area = area.simplify(tolerance=0.01)
        area = orient(area, sign=-1.0)
        area_exterior_coords = area.exterior.coords[:]
        nbr_of_sides = len(area_exterior_coords) - 1
        area_exterior_coords.append(
            area.exterior.coords[1]
        )  # duplicating second coordinate to cover all side lines
        new_area_coords = []
        for i in range(nbr_of_sides):
            side_line_1 = LineString(
                [area_exterior_coords[i], area_exterior_coords[i + 1]]
            )
            side_line_2 = LineString(
                [area_exterior_coords[i + 1], area_exterior_coords[i + 2]]
            )

            side_line_1_offset = side_line_1.parallel_offset(
                distance=cls._get_width_of_most_intersecting_wall(
                    line=side_line_1, walls=walls
                ),
                side="left",
            )
            side_line_2_offset = side_line_2.parallel_offset(
                distance=cls._get_width_of_most_intersecting_wall(
                    line=side_line_2, walls=walls
                ),
                side="left",
            )
            intersection_point = cls._get_intersecting_point_of_offset_lines(
                line_1=side_line_1_offset, line_2=side_line_2_offset
            )
            new_area_coords.append([intersection_point.x, intersection_point.y])

        new_perimeters = Polygon(new_area_coords)
        if not new_perimeters.is_valid:
            new_perimeters = make_valid(new_perimeters)
            if not new_perimeters.is_valid:
                return area.buffer(
                    distance=AREA_BUFFER_TO_INCLUDE_WALLS_IN_M,
                    cap_style=CAP_STYLE.square,
                    join_style=JOIN_STYLE.mitre,
                )
        return new_perimeters

    @staticmethod
    def _get_intersecting_point_of_offset_lines(
        line_1: LineString, line_2: LineString
    ) -> Point:
        """
        if the lines are parallel for simplicity we return the most sharing point
        """
        intersection = scale(
            geom=line_1, xfact=100, yfact=100, origin="center"
        ).intersection(scale(geom=line_2, xfact=100, yfact=100, origin="center"))
        if not isinstance(intersection, Point):  # lines are parallel
            return Point(line_1.coords[1])
        return intersection

    @staticmethod
    def _get_width_of_most_intersecting_wall(
        line: LineString, walls: list[Polygon]
    ) -> float:
        buffered_line = line.buffer(
            distance=AREA_BUFFER_FOR_WALLS_INTERSECTION_IN_M,
            cap_style=CAP_STYLE.square,
            join_style=JOIN_STYLE.mitre,
        )
        intersecting_walls = sorted(
            [
                (wall, buffered_line.intersection(wall).area)
                for wall in walls
                if wall.intersects(buffered_line)
            ],
            key=lambda element: element[1],
            reverse=True,
        )
        if not intersecting_walls:
            return AREA_BUFFER_TO_INCLUDE_WALLS_IN_M
        return get_sides_as_lines_by_length(polygon=intersecting_walls[0][0])[0].length

    @staticmethod
    def _non_era_area_types() -> set[AreaType]:
        return {
            area_type
            for sia_category in [SIACategory.ANF, SIACategory.NNF]
            for area_type in UnifiedClassificationScheme().get_children(
                parent_type=sia_category
            )
        }
