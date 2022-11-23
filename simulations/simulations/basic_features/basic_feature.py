from math import isclose
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple

from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimFeature, SimLayout
from brooks.types import AreaType, OpeningType, SIACategory
from common_utils.constants import SIA_DIMENSION_PREFIX, SIMULATION_VERSION
from dufresne.polygon.utils import get_biggest_polygon
from simulations.basic_features.constants import (
    PH_FEATURE_CATEGORIES,
    FurnitureCategory,
)
from simulations.rectangulator import DeterministicRectangulator


class BaseBasicFeatures:
    ROOM_CATEGORIES = {
        "BALCONIES": {AreaType.BALCONY},
        "LOGGIAS": {AreaType.LOGGIA},
        "SHAFTS": {AreaType.SHAFT},
        "KITCHENS": {AreaType.KITCHEN, AreaType.KITCHEN_DINING},
        "CORRIDORS": {AreaType.CORRIDOR},
        "ROOMS": {
            AreaType.BEDROOM,
            AreaType.DINING,
            AreaType.LIVING_DINING,
            AreaType.LIVING_ROOM,
            AreaType.ROOM,
        },
        "BATHROOMS": {AreaType.BATHROOM},
        "SUNROOMS": {AreaType.WINTERGARTEN},
        "STORAGE_ROOMS": {AreaType.STOREROOM},
        "STAIRCASES": {AreaType.STAIRCASE},
        "ELEVATORS": {AreaType.ELEVATOR},
    }

    net_area_by_sia_contributors = {
        SIACategory.HNF,
        SIACategory.NNF,
    }

    def __init__(
        self,
    ):
        self.classification_scheme = UnifiedClassificationScheme()

    def get_basic_features(
        self, unit_id_unit_layout: Dict[int, SimLayout]
    ) -> Dict[str, float]:
        result = dict(
            (
                *self.number_of_rooms(layouts=list(unit_id_unit_layout.values())),
                *self.number_of_balconies(layouts=list(unit_id_unit_layout.values())),
                *self.nbr_of_rooms_by_type(layouts=list(unit_id_unit_layout.values())),
                *self.total_area_by_room_type(
                    layouts=list(unit_id_unit_layout.values())
                ),
                *self.area_of_staircases(layouts=list(unit_id_unit_layout.values())),
                *self.rectangle_dimensions(layouts=list(unit_id_unit_layout.values())),
                *self.kitchen_window_dimensions(
                    layouts=list(unit_id_unit_layout.values())
                ),
                *self.furniture_count_dimensions(
                    layouts=list(unit_id_unit_layout.values())
                ),
            )
        )
        result.update(self.net_area(layouts=list(unit_id_unit_layout.values())))
        result.update(
            self.add_sia_dimension_prefix(
                sia_dimensions=self.sia_dimensions(
                    layouts=list(unit_id_unit_layout.values())
                )
            )
        )

        BLACKLISTED_COLUMNS = [
            "number-of-elevators",
            "number-of-staircases",
            "number-of-shafts",
        ]
        for column in BLACKLISTED_COLUMNS:
            result.pop(column, None)

        return result

    def number_of_rooms(self, layouts: Iterable[SimLayout]) -> Tuple[Tuple[str, float]]:
        return (
            (
                "number-of-rooms",
                float(
                    sum(
                        [
                            self.classification_scheme.NBR_OF_ROOMS_COUNTER[area.type]
                            for layout in layouts
                            for area in layout.areas
                        ]
                    )
                ),
            ),
        )

    def number_of_balconies(
        self, layouts: Iterable[SimLayout]
    ) -> Tuple[Tuple[str, float]]:
        """Required in the RC dashboard"""
        return (
            (
                "number-of-balconies",
                float(
                    sum(
                        [
                            1.0
                            for layout in layouts
                            for area in layout.areas
                            if area.type in self.classification_scheme.BALCONY_AREAS
                        ]
                    )
                ),
            ),
        )

    def area_of_staircases(self, layouts: Iterable[SimLayout]):
        if "STAIRCASES" not in self.ROOM_CATEGORIES:
            return []

        total_area_without_stairs = self.calc_total_area(
            areas=self.get_areas_by_area_type_groups(
                layouts=layouts, groups=self.ROOM_CATEGORIES
            )["STAIRCASES"],
            layouts=layouts,
            include_stairs_of_areas=False,
        )
        total_area_layout_stairs = sum(
            layout.stair_area_no_overlap() for layout in layouts
        )
        return (
            ("area-staircases", total_area_without_stairs + total_area_layout_stairs),
        )

    def net_area(self, layouts: Iterable[SimLayout]) -> Dict[str, float]:
        net_area_by_area_type = self.weighted_net_area_by_area_type(layouts=layouts)

        net_area_total: float = sum(net_area_by_area_type.values())
        loggia_net_area = sum(
            [
                net_area_by_area_type.get(area_type, 0.0)
                for area_type in self.ROOM_CATEGORIES["LOGGIAS"]
            ]
        )
        corridor_net_area = sum(
            [
                net_area_by_area_type.get(area_type, 0.0)
                for area_type in self.ROOM_CATEGORIES["CORRIDORS"]
            ]
        )
        return {
            "net-area-reduced-loggias": net_area_total,
            "net-area": self.net_area_by_sia(layouts=layouts),
            "net-area-no-corridors": net_area_total
            - loggia_net_area
            - corridor_net_area,
            "net-area-no-corridors-reduced-loggias": net_area_total - corridor_net_area,
        }

    def net_area_by_sia(self, layouts: Iterable[SimLayout]) -> float:
        return sum(
            [
                self.sia_dimensions(layouts=layouts)[sia_type.name]
                for sia_type in self.net_area_by_sia_contributors
            ]
        )

    def nbr_of_rooms_by_type(
        self, layouts: Iterable[SimLayout]
    ) -> Iterable[Tuple[str, float]]:
        return (
            (f"number-of-{room_category.lower().replace('_','-')}", float(len(areas)))
            for room_category, areas in self.get_areas_by_area_type_groups(
                layouts=layouts, groups=self.ROOM_CATEGORIES
            ).items()
            if room_category not in {"ROOMS", "BALCONIES"}  # they have their own method
        )

    def total_area_by_room_type(
        self, layouts: Iterable[SimLayout]
    ) -> Iterable[Tuple[str, float]]:
        for room_category, areas in self.get_areas_by_area_type_groups(
            layouts=layouts, groups=self.ROOM_CATEGORIES
        ).items():
            if room_category == "STAIRCASES":  # has its own method
                continue

            total_area = self.calc_total_area(
                areas=areas,
                layouts=layouts,
                include_stairs_of_areas=not self.classification_scheme.STAIR_AREA.isdisjoint(
                    self.ROOM_CATEGORIES[room_category]
                ),
            )
            yield f"area-{room_category.lower()}", total_area

    def calc_total_area(
        self,
        areas: List[SimArea],
        layouts: Iterable[SimLayout],
        include_stairs_of_areas: bool = False,
    ) -> float:
        total_area_without_stairs = float(sum(a.area_without_stairs for a in areas))

        if include_stairs_of_areas:
            stair_area = sum(
                layout.stair_area_no_overlap(
                    selected_areas={area for area in areas if area in layout.areas}
                )
                for layout in layouts
            )
            return total_area_without_stairs + stair_area

        return total_area_without_stairs

    def get_areas_by_area_type_groups(
        self,
        layouts: Iterable[SimLayout],
        groups: Dict[str, Set[AreaType]],
    ) -> Dict[str, List[SimArea]]:
        """
        returns a dictionary with provided categories as keys and values
        containing of all areas of key type and children of this area type
        """

        return {
            group_name: [
                area
                for area_type in area_types
                for layout in layouts
                for area in layout.areas_by_type[area_type]
            ]
            for group_name, area_types in groups.items()
        }

    def weighted_net_area_by_area_type(
        self, layouts: Iterable[SimLayout]
    ) -> Dict[AreaType, float]:
        """
        uses the net area contribution information from the provided classification scheme
        to calculate the weighted net area by area type
        """
        result = {}
        for (
            area_type,
            weight,
        ) in self.classification_scheme.NET_AREA_CONTRIBUTIONS.items():
            areas = [
                area
                for layout in layouts
                for area in layout.areas_by_type.get(area_type, {})
            ]

            total_area = self.calc_total_area(
                areas=areas,
                layouts=layouts,
                include_stairs_of_areas=not self.classification_scheme.STAIR_AREA.isdisjoint(
                    {area_type}
                ),
            )
            result[area_type] = weight * total_area
        return result

    @staticmethod
    def find_biggest_rectangles(
        layouts: Iterable[SimLayout],
        valid_area_types: Set[AreaType],
    ) -> float:
        """Finds the biggest usable area in the targeted areas by type.
        Not removable features like a kitchen and door sweeping areas are considered in the calculation
        """
        biggest_area = 0.0
        valid_areas = (
            area
            for layout in layouts
            for space in layout.spaces
            for area in space.areas
            if area.type in valid_area_types
        )
        for area in valid_areas:
            rectangle = BaseBasicFeatures.biggest_rectangle_in_area(area=area)
            if rectangle.area > biggest_area:
                biggest_area = rectangle.area
        return biggest_area

    @staticmethod
    def biggest_rectangle_in_area(
        area: SimArea,
        simulation_version: Optional[
            SIMULATION_VERSION
        ] = SIMULATION_VERSION.PH_01_2021,
        generations: int = 1000,
    ) -> Polygon:
        non_usable_areas = unary_union([feature.footprint for feature in area.features])
        remaining_area = area.footprint.difference(non_usable_areas)

        if isinstance(remaining_area, MultiPolygon):
            remaining_area = get_biggest_polygon(remaining_area)

        if isclose(remaining_area.area, 0.0, abs_tol=1e-3):
            return remaining_area

        if simulation_version in {
            SIMULATION_VERSION.EXPERIMENTAL,
            SIMULATION_VERSION.PH_2022_H1,
        }:
            from simulations.rectangulator import get_max_rectangle_in_convex_polygon

            return get_max_rectangle_in_convex_polygon(
                target_convex_polygon=remaining_area, generations=generations
            )

        distance_from_wall = 0.1 if area.type == AreaType.DINING else 0.01
        return DeterministicRectangulator(
            polygon=remaining_area, distance_from_wall=distance_from_wall
        ).get_biggest_rectangle()

    def sia_dimensions(self, layouts: Iterable[SimLayout]) -> Dict[str, float]:
        return {
            sia_category: float(sum([a.footprint.area for a in areas]))
            for sia_category, areas in self.get_areas_by_area_type_groups(
                layouts=layouts,
                groups={
                    sia_category.name: set(
                        self.classification_scheme.get_children(
                            parent_type=sia_category
                        )
                    )
                    for sia_category in self.classification_scheme.SIA_CATEGORIES
                },
            ).items()
        }

    def add_sia_dimension_prefix(self, sia_dimensions: Dict) -> Dict:
        for key in [*sia_dimensions.keys()]:
            sia_dimensions[SIA_DIMENSION_PREFIX + key] = sia_dimensions.pop(key)
        return sia_dimensions

    def rectangle_dimensions(
        self, layouts: Iterable[SimLayout]
    ) -> Tuple[Tuple[str, float], Tuple[str, float]]:
        return (
            (
                "maximum-dining-table",
                self.find_biggest_rectangles(
                    layouts=layouts,
                    valid_area_types=self.classification_scheme.DINING_AREAS,
                ),
            ),
            (
                "maximum-balcony-area",
                self.find_biggest_rectangles(
                    layouts=layouts,
                    valid_area_types=self.classification_scheme.OUTDOOR_AREAS,
                ),
            ),
        )

    def kitchen_window_dimensions(
        self, layouts: List[SimLayout]
    ) -> Tuple[Tuple[str, int]]:
        openings = {
            key: value
            for layout in layouts
            for key, value in layout.areas_openings.items()
        }
        for kitchen in self.get_areas_by_area_type_groups(
            layouts=layouts, groups=self.ROOM_CATEGORIES
        ).get("KITCHENS", []):
            for opening in openings[kitchen.id]:
                if opening.type is OpeningType.WINDOW:
                    return (("has-kitchen-window", 1),)

        return (("has-kitchen-window", 0),)

    def furniture_count_dimensions(
        self,
        layouts: List[SimLayout],
    ) -> Iterator[Tuple[str, float]]:
        return (
            (f"number-of-{category.name.lower()}", float(len(features)))
            for category, features in self.get_features_by_furniture_category(
                layouts=layouts
            ).items()
        )

    @staticmethod
    def get_features_by_furniture_category(
        layouts: Iterable[SimLayout],
    ) -> Dict[FurnitureCategory, Set[SimFeature]]:
        result = {}
        for category, feature_types in PH_FEATURE_CATEGORIES.items():
            result[category] = {
                feature
                for layout in layouts
                for feature_type in feature_types
                for feature in layout.features_by_type[feature_type]
            }

        return result
