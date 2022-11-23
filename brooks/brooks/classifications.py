from collections import Counter
from enum import Enum
from functools import cached_property
from typing import Dict, Set, Union

from brooks.types import AreaType, FeatureType, SIACategory


class AreaTreeLevel(Enum):
    """
    Enumeration to list the levels in an Area Tree.
    Parents always must have a smaller enum value than their children
    """

    pass


def rgb_from_name(color_name: str) -> str:
    from matplotlib import colors
    from PIL.ImageColor import getrgb

    return f"rgb{getrgb(colors.get_named_colors_mapping()[color_name])}"


class ArchilyseAreaTreeLevel(AreaTreeLevel):
    SIA_LEVEL = 0
    BASE_AREA_TYPE_LEVEL = 1


class BaseClassificationScheme:
    AREA_TYPE_LEVELS = AreaTreeLevel

    @property
    def AREA_TYPES_WITH_WATER_SUPPLY(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def _NET_AREA_CONTRIBUTIONS(self):
        raise NotImplementedError

    @property
    def _AREA_TREE(self):
        raise NotImplementedError

    @property
    def VOID_SORT_ORDER(self):
        raise NotImplementedError

    @property
    def LIGHTWELL_SORT_ORDER(self):
        raise NotImplementedError

    @property
    def DEFAULT_SHAFT_AREA(self) -> AreaType:
        raise NotImplementedError

    @property
    def DEFAULT_ELEVATOR_AREA(self) -> AreaType:
        raise NotImplementedError

    @property
    def DEFAULT_STAIR_AREA(self) -> AreaType:
        raise NotImplementedError

    @property
    def DEFAULT_WATER_CONNECTION_AREA(self) -> AreaType:
        """
        default area type mapping for areas containing features toilets, sinks, bathtubs etc
        """
        raise NotImplementedError

    @property
    def AREA_TYPES_FEATURE_MAPPING(
        self,
    ) -> Dict[FeatureType, Set[AreaType]]:
        raise NotImplementedError

    @property
    def AREA_TYPES_ACCEPTING_SHAFTS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def NET_AREA_CONTRIBUTIONS(self) -> Dict[AreaType, float]:
        self._NET_AREA_CONTRIBUTIONS[AreaType.VOID] = 0
        self._NET_AREA_CONTRIBUTIONS[AreaType.LIGHTWELL] = 0
        self._NET_AREA_CONTRIBUTIONS[AreaType.OUTDOOR_VOID] = 0
        return self._NET_AREA_CONTRIBUTIONS

    @property
    def SIA_CATEGORIES(self):
        raise NotImplementedError

    @property
    def NBR_OF_ROOMS_COUNTER(self) -> Counter:
        raise NotImplementedError

    @property
    def DXF_SIA_LAYERS(self):
        raise NotImplementedError

    @property
    def AREAS_WITHOUT_CEILINGS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def AREAS_WITHOUT_FLOORS(
        self,
    ) -> Set[AreaType]:
        return {AreaType.VOID, AreaType.LIGHTWELL, AreaType.OUTDOOR_VOID}

    @property
    def STAIR_AREA(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def BALCONY_AREAS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def OUTDOOR_AREAS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def DINING_AREAS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def RESIDENTIAL_KITCHEN_AREAS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def LIVING_AND_BEDROOMS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def STOREROOM_AREAS(
        self,
    ) -> Set[AreaType]:
        raise NotImplementedError

    @property
    def CIRCULATION_AREAS(
        self,
    ) -> Set[AreaType]:
        """Used in the competition tool"""
        raise NotImplementedError

    @property
    def AREAS_WINDOW_REQUIRED(
        self,
    ) -> Set[AreaType]:
        """
        used in qa analysis to detect missing windows for areas which are
        supposed to have a window (or a glass door to a balcony)
        """
        raise NotImplementedError

    @property
    def ROOM_VECTOR_NAMING(
        self,
    ) -> Dict[AreaType, str]:
        """
        Provides the naming for the area type of the classifications in the room vector files.
        This can be relevant especially if CustomValuator is using the room vector files afterwards.
        """
        raise NotImplementedError

    @property
    def area_tree(self):
        self._AREA_TREE[AreaType.VOID] = {
            "level": self.AREA_TYPE_LEVELS(1),
            "color_code": rgb_from_name("palegreen"),
            "sort_order": self.VOID_SORT_ORDER,
            "children": set(),
        }
        self._AREA_TREE[AreaType.OUTDOOR_VOID] = {
            "level": self.AREA_TYPE_LEVELS(1),
            "color_code": rgb_from_name("palegreen"),
            "sort_order": self.VOID_SORT_ORDER,
            "children": set(),
        }
        self._AREA_TREE[AreaType.LIGHTWELL] = {
            "level": self.AREA_TYPE_LEVELS(1),
            "color_code": rgb_from_name("palegreen"),
            "sort_order": self.LIGHTWELL_SORT_ORDER,
            "children": set(),
        }
        return self._AREA_TREE

    CONNECTIVITY_UNWANTED_AREA_TYPES = {
        AreaType.SHAFT,
        AreaType.NOT_DEFINED,
    }

    @property
    def area_types(
        self,
    ) -> Set[AreaType]:
        return {area_type for area_type, metadata in self.area_tree.items()}

    def get_children(self, parent_type: Union[AreaType, SIACategory]) -> Set[AreaType]:
        children = set()
        for child_type in self.area_tree[parent_type].get("children", set()):
            children.add(child_type)
            children |= self.get_children(child_type)

        return children

    @cached_property
    def leaf_area_types(self):
        for area_type in self.area_tree:
            if not self.get_children(area_type):
                yield area_type

    def area_types_per_level(self, level: AreaTreeLevel) -> Set[AreaType]:
        return {
            area_type
            for area_type, metadata in self.area_tree.items()
            if metadata["level"] is level
        }

    @property
    def AREA_TYPES_NO_CONNECTION_NEEDED(
        self,
    ) -> Set[AreaType]:
        """
        This property is needed to exclude areas from space connection validation and connectivity analysis
        """
        return self.AREA_TYPES_ACCEPTING_SHAFTS


class UnifiedClassificationScheme(BaseClassificationScheme):
    AREA_TYPE_LEVELS = ArchilyseAreaTreeLevel

    _AREA_TREE = {
        SIACategory.ANF: {
            "level": ArchilyseAreaTreeLevel.SIA_LEVEL,
            "children": {
                AreaType.ARCADE,
                AreaType.BALCONY,
                AreaType.GARDEN,
                AreaType.LOGGIA,
                AreaType.PATIO,
                AreaType.TERRACE,
            },
        },
        SIACategory.FF: {
            "level": ArchilyseAreaTreeLevel.SIA_LEVEL,
            "children": {
                AreaType.SHAFT,
                AreaType.TECHNICAL_AREA,
                AreaType.WASTEWATER,
                AreaType.WATER_SUPPLY,
                AreaType.HEATING,
                AreaType.GAS,
                AreaType.ELECTRICAL_SUPPLY,
                AreaType.TELECOMMUNICATIONS,
                AreaType.AIR,
                AreaType.ELEVATOR_FACILITIES,
                AreaType.OPERATIONS_FACILITIES,
            },
        },
        SIACategory.HNF: {
            "level": ArchilyseAreaTreeLevel.SIA_LEVEL,
            "children": {
                AreaType.BATHROOM,
                AreaType.BEDROOM,
                AreaType.CORRIDOR,
                AreaType.DINING,
                AreaType.KITCHEN_DINING,
                AreaType.KITCHEN,
                AreaType.LIVING_DINING,
                AreaType.LIVING_ROOM,
                AreaType.LOBBY,
                AreaType.OFFICE,
                AreaType.OIL_TANK,
                AreaType.ROOM,
                AreaType.STUDIO,
                AreaType.WINTERGARTEN,
                AreaType.COMMUNITY_ROOM,
                AreaType.BREAK_ROOM,
                AreaType.WAITING_ROOM,
                AreaType.CANTEEN,
                AreaType.PRISON_CELL,
                AreaType.OFFICE_SPACE,
                AreaType.OPEN_PLAN_OFFICE,
                AreaType.MEETING_ROOM,
                AreaType.DESIGN_ROOM,
                AreaType.COUNTER_ROOM,
                AreaType.CONTROL_ROOM,
                AreaType.RECEPTION_ROOM,
                AreaType.OFFICE_TECH_ROOM,
                AreaType.FACTORY_ROOM,
                AreaType.WORKSHOP,
                AreaType.TECHNICAL_LAB,
                AreaType.PHYSICS_LAB,
                AreaType.CHEMICAL_LAB,
                AreaType.LIVESTOCK,
                AreaType.PLANTS,
                AreaType.COMMON_KITCHEN,
                AreaType.SPECIAL_WORKSPACE,
                AreaType.WAREHOUSE,
                AreaType.ARCHIVE,
                AreaType.COLD_STORAGE,
                AreaType.LOGISTICS,
                AreaType.SALESROOM,
                AreaType.EXHIBITION,
                AreaType.TEACHING_ROOM,
                AreaType.FLEXIBLE_TEACHING_ROOM,
                AreaType.DEDICATED_TEACHING_ROOM,
                AreaType.LIBRARY,
                AreaType.SPORTS_ROOMS,
                AreaType.ASSEMBLY_HALL,
                AreaType.STAGE_ROOM,
                AreaType.SHOWROOM,
                AreaType.CHAPEL,
                AreaType.MEDICAL_ROOM,
                AreaType.DEDICATED_MEDICAL_ROOM,
                AreaType.SURGERY_ROOM,
                AreaType.RADIATION_DIAGNOSIS,
                AreaType.RADATION_THERAPY,
                AreaType.PHYSIO_AND_REHABILITATION,
                AreaType.MEDICAL_BEDROOM,
                AreaType.DEDICATED_MEDICAL_BEDROOM,
            },
        },
        SIACategory.NNF: {
            "level": ArchilyseAreaTreeLevel.SIA_LEVEL,
            "children": {
                AreaType.BASEMENT,
                AreaType.BASEMENT_COMPARTMENT,
                AreaType.BIKE_STORAGE,
                AreaType.GARAGE,
                AreaType.PRAM,
                AreaType.PRAM_AND_BIKE_STORAGE_ROOM,
                AreaType.STOREROOM,
                AreaType.WASH_AND_DRY_ROOM,
                AreaType.SANITARY_ROOMS,
                AreaType.CLOAKROOM,
                AreaType.PASSENGER_PLATFORM,
                AreaType.HOUSE_TECHNICS_FACILITIES,
                AreaType.SHELTER,
                AreaType.MOTORCYCLE_PARKING,
            },
        },
        SIACategory.VF: {
            "level": ArchilyseAreaTreeLevel.SIA_LEVEL,
            "children": {
                AreaType.CARPARK,
                AreaType.ELEVATOR,
                AreaType.FOYER,
                AreaType.STAIRCASE,
                AreaType.CORRIDORS_AND_HALLS,
                AreaType.TRANSPORT_SHAFT,
                AreaType.VEHICLE_TRAFFIC_AREA,
            },
        },
        AreaType.BALCONY: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 3,
            "color_code": "rgb(240, 230, 140)",
        },
        AreaType.LOGGIA: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 6,
            "color_code": "rgb(186, 85, 211)",
        },
        AreaType.ARCADE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 23,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.LOBBY: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.STUDIO: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.TERRACE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.PATIO: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.SHAFT: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 11,
            "color_code": "rgb(255, 255, 0)",
        },
        AreaType.TECHNICAL_AREA: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 21,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.OPERATIONS_FACILITIES: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 88,
            "color_code": "rgb(70, 250, 155)",
        },
        AreaType.WASTEWATER: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 80,
            "color_code": "rgb(60, 180, 75)",
        },
        AreaType.TELECOMMUNICATIONS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 85,
            "color_code": "rgb(60, 230, 125)",
        },
        AreaType.HEATING: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 82,
            "color_code": "rgb(60, 200, 95)",
        },
        AreaType.ELEVATOR_FACILITIES: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 87,
            "color_code": "rgb(60, 250, 145)",
        },
        AreaType.WATER_SUPPLY: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 81,
            "color_code": "rgb(60, 190, 85)",
        },
        AreaType.AIR: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 86,
            "color_code": "rgb(60, 240, 135)",
        },
        AreaType.ELECTRICAL_SUPPLY: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 84,
            "color_code": "rgb(60, 220, 115)",
        },
        AreaType.GAS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 83,
            "color_code": "rgb(60, 210, 105)",
        },
        AreaType.KITCHEN: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 7,
            "color_code": "rgb(176, 224, 230)",
        },
        AreaType.KITCHEN_DINING: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 8,
            "color_code": "rgb(238, 130, 238)",
        },
        AreaType.CORRIDOR: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 4,
            "color_code": "rgb(100, 149, 237)",
        },
        AreaType.DINING: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 9,
            "color_code": "rgb(154, 205, 50)",
        },
        AreaType.ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 1,
            "color_code": "rgb(240, 128, 128)",
        },
        AreaType.LIVING_DINING: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 16,
            "color_code": "rgb(188, 143, 143)",
        },
        AreaType.BEDROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 14,
            "color_code": "rgb(64, 224, 208)",
        },
        AreaType.LIVING_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 15,
            "color_code": "rgb(0, 139, 139)",
        },
        AreaType.BATHROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 2,
            "color_code": "rgb(21, 176, 26)",
        },
        AreaType.WINTERGARTEN: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 13,
            "color_code": "rgb(218, 165, 32)",
        },
        AreaType.CONTROL_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 26,
            "color_code": "rgb(0, 115, 115)",
        },
        AreaType.MEETING_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 23,
            "color_code": "rgb(0, 160, 160)",
        },
        AreaType.COUNTER_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 25,
            "color_code": "rgb(0, 130, 130)",
        },
        AreaType.OFFICE_TECH_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 28,
            "color_code": "rgb(0, 85, 85)",
        },
        AreaType.DESIGN_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 24,
            "color_code": "rgb(0, 145, 145)",
        },
        AreaType.OFFICE_SPACE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 21,
            "color_code": "rgb(0, 190, 190)",
        },
        AreaType.OPEN_PLAN_OFFICE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 22,
            "color_code": "rgb(0, 175, 175)",
        },
        AreaType.RECEPTION_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 27,
            "color_code": "rgb(0, 100, 100)",
        },
        AreaType.FACTORY_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 31,
            "color_code": "rgb(85, 100, 10)",
        },
        AreaType.PLANTS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 37,
            "color_code": "rgb(140, 160, 60)",
        },
        AreaType.TECHNICAL_LAB: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 33,
            "color_code": "rgb(85, 130, 30)",
        },
        AreaType.COMMON_KITCHEN: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 38,
            "color_code": "rgb(150, 170, 70)",
        },
        AreaType.SPECIAL_WORKSPACE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 39,
            "color_code": "rgb(160, 180, 80)",
        },
        AreaType.WORKSHOP: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 32,
            "color_code": "rgb(85, 115, 20)",
        },
        AreaType.PHYSICS_LAB: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 34,
            "color_code": "rgb(110, 130, 30)",
        },
        AreaType.LIVESTOCK: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 36,
            "color_code": "rgb(130, 150, 50)",
        },
        AreaType.CHEMICAL_LAB: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 35,
            "color_code": "rgb(130, 130, 40)",
        },
        AreaType.DEDICATED_MEDICAL_BEDROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 68,
            "color_code": "rgb(150, 250, 250)",
        },
        AreaType.PHYSIO_AND_REHABILITATION: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 66,
            "color_code": "rgb(110, 250, 250)",
        },
        AreaType.SURGERY_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 63,
            "color_code": "rgb(50, 250, 250)",
        },
        AreaType.RADATION_THERAPY: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 65,
            "color_code": "rgb(90, 250, 250)",
        },
        AreaType.MEDICAL_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 61,
            "color_code": "rgb(10, 250, 250)",
        },
        AreaType.DEDICATED_MEDICAL_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 62,
            "color_code": "rgb(30, 250, 250)",
        },
        AreaType.MEDICAL_BEDROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 67,
            "color_code": "rgb(130, 250, 250)",
        },
        AreaType.RADIATION_DIAGNOSIS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 64,
            "color_code": "rgb(70, 250, 250)",
        },
        AreaType.STAGE_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 57,
            "color_code": "rgb(250, 130, 250)",
        },
        AreaType.DEDICATED_TEACHING_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 53,
            "color_code": "rgb(250, 50, 250)",
        },
        AreaType.LIBRARY: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 54,
            "color_code": "rgb(250, 70, 250)",
        },
        AreaType.CHAPEL: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 59,
            "color_code": "rgb(250, 170, 250)",
        },
        AreaType.TEACHING_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 51,
            "color_code": "rgb(250, 10, 250)",
        },
        AreaType.ASSEMBLY_HALL: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 56,
            "color_code": "rgb(250, 110, 250)",
        },
        AreaType.FLEXIBLE_TEACHING_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 52,
            "color_code": "rgb(250, 30, 250)",
        },
        AreaType.SHOWROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 58,
            "color_code": "rgb(250, 150, 250)",
        },
        AreaType.SPORTS_ROOMS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 55,
            "color_code": "rgb(250, 90, 250)",
        },
        AreaType.SALESROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 44,
            "color_code": "rgb(245, 90, 30)",
        },
        AreaType.LOGISTICS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 43,
            "color_code": "rgb(245, 100, 35)",
        },
        AreaType.ARCHIVE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 42,
            "color_code": "rgb(245, 120, 44)",
        },
        AreaType.WAREHOUSE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 41,
            "color_code": "rgb(245, 130, 49)",
        },
        AreaType.EXHIBITION: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 45,
            "color_code": "rgb(245, 80, 25)",
        },
        AreaType.COLD_STORAGE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 42,
            "color_code": "rgb(245, 110, 40)",
        },
        AreaType.BREAK_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 13,
            "color_code": "rgb(195, 26, 84)",
        },
        AreaType.COMMUNITY_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 12,
            "color_code": "rgb(225, 26, 84)",
        },
        AreaType.CANTEEN: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 15,
            "color_code": "rgb(135, 26, 84)",
        },
        AreaType.WAITING_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 14,
            "color_code": "rgb(165, 26, 84)",
        },
        AreaType.PRISON_CELL: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 16,
            "color_code": "rgb(105, 26, 84)",
        },
        AreaType.OFFICE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": set(),
        },
        AreaType.OIL_TANK: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.STOREROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 5,
            "color_code": "rgb(255, 165, 0)",
        },
        AreaType.BASEMENT_COMPARTMENT: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 20,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.WASH_AND_DRY_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 22,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.BIKE_STORAGE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 24,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.PRAM_AND_BIKE_STORAGE_ROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 25,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.HOUSE_TECHNICS_FACILITIES: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 76,
            "color_code": "rgb(171, 130, 229)",
        },
        AreaType.MOTORCYCLE_PARKING: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 78,
            "color_code": "rgb(211, 140, 229)",
        },
        AreaType.SANITARY_ROOMS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 71,
            "color_code": "rgb(71, 105, 229)",
        },
        AreaType.SHELTER: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 77,
            "color_code": "rgb(191, 135, 229)",
        },
        AreaType.PASSENGER_PLATFORM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 75,
            "color_code": "rgb(151, 125, 229)",
        },
        AreaType.CLOAKROOM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 72,
            "color_code": "rgb(91, 110, 229)",
        },
        AreaType.BASEMENT: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.PRAM: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.GARAGE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.STAIRCASE: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 12,
            "color_code": "rgb(221, 160, 221)",
        },
        AreaType.ELEVATOR: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 10,
            "color_code": "rgb(255, 182, 193)",
        },
        AreaType.CARPARK: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 19,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.TRANSPORT_SHAFT: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 93,
            "color_code": "rgb(255, 225, 85)",
        },
        AreaType.VEHICLE_TRAFFIC_AREA: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 94,
            "color_code": "rgb(255, 225, 115)",
        },
        AreaType.CORRIDORS_AND_HALLS: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 91,
            "color_code": "rgb(255, 225, 25)",
        },
        AreaType.FOYER: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
        },
        AreaType.GARDEN: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 26,
            "color_code": "rgb(255, 255, 255)",
        },
        AreaType.OUTDOOR_VOID: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 17,
            "color_code": "rgb(152, 251, 152)",
        },
        AreaType.LIGHTWELL: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 18,
            "color_code": "rgb(152, 251, 152)",
        },
        AreaType.VOID: {
            "level": ArchilyseAreaTreeLevel.BASE_AREA_TYPE_LEVEL,
            "children": [],
            "sort_order": 17,
            "color_code": "rgb(152, 251, 152)",
        },
    }

    DEFAULT_SHAFT_AREA = AreaType.SHAFT
    DEFAULT_WATER_CONNECTION_AREA = AreaType.BATHROOM

    DEFAULT_ELEVATOR_AREA = AreaType.ELEVATOR
    DEFAULT_STAIR_AREA = AreaType.STAIRCASE

    VOID_SORT_ORDER = 17
    LIGHTWELL_SORT_ORDER = 18
    ROOM_COUNTS = {
        AreaType.ROOM: 1.0,
        AreaType.BEDROOM: 1.0,
        AreaType.KITCHEN_DINING: 1.5,
        AreaType.LIVING_DINING: 1.5,
        AreaType.DINING: 1.0,
        AreaType.LIVING_ROOM: 1.0,
    }

    NBR_OF_ROOMS_COUNTER = Counter(ROOM_COUNTS)

    _NET_AREA_CONTRIBUTIONS = {
        AreaType.BATHROOM: 1.0,
        AreaType.CORRIDOR: 1.0,
        AreaType.BEDROOM: 1.0,
        AreaType.DINING: 1.0,
        AreaType.LIVING_DINING: 1.0,
        AreaType.LIVING_ROOM: 1.0,
        AreaType.ROOM: 1.0,
        AreaType.KITCHEN: 1.0,
        AreaType.KITCHEN_DINING: 1.0,
        AreaType.STOREROOM: 1.0,
        AreaType.WINTERGARTEN: 1.0,
        AreaType.LOGGIA: 0.5,
        AreaType.OFFICE: 1.0,
        AreaType.BUF10_1_AUSSEN_PP_FAHRZEUG: 1.0,
        AreaType.BUF10_3_AUSSEN_PP_MOTO: 1.0,
        AreaType.BUF10_2_UEBERDACHTE_AUSSEN_PP_FAHRZEUG: 1.0,
        AreaType.BUF10_4_AUSSEN_PP_FAHRRAD: 1.0,
        AreaType.BUF10_5_BEARB__AUSSENFLAECHE: 1.0,
        AreaType.WASTEWATER: 1.0,
        AreaType.WATER_SUPPLY: 1.0,
        AreaType.HEATING: 1.0,
        AreaType.GAS: 1.0,
        AreaType.ELECTRICAL_SUPPLY: 1.0,
        AreaType.TELECOMMUNICATIONS: 1.0,
        AreaType.AIR: 1.0,
        AreaType.ELEVATOR_FACILITIES: 1.0,
        AreaType.OPERATIONS_FACILITIES: 1.0,
        AreaType.COMMUNITY_ROOM: 1.0,
        AreaType.BREAK_ROOM: 1.0,
        AreaType.WAITING_ROOM: 1.0,
        AreaType.CANTEEN: 1.0,
        AreaType.PRISON_CELL: 1.0,
        AreaType.OFFICE_SPACE: 1.0,
        AreaType.OPEN_PLAN_OFFICE: 1.0,
        AreaType.MEETING_ROOM: 1.0,
        AreaType.DESIGN_ROOM: 1.0,
        AreaType.COUNTER_ROOM: 1.0,
        AreaType.CONTROL_ROOM: 1.0,
        AreaType.RECEPTION_ROOM: 1.0,
        AreaType.OFFICE_TECH_ROOM: 1.0,
        AreaType.FACTORY_ROOM: 1.0,
        AreaType.WORKSHOP: 1.0,
        AreaType.TECHNICAL_LAB: 1.0,
        AreaType.PHYSICS_LAB: 1.0,
        AreaType.CHEMICAL_LAB: 1.0,
        AreaType.LIVESTOCK: 1.0,
        AreaType.PLANTS: 1.0,
        AreaType.COMMON_KITCHEN: 1.0,
        AreaType.SPECIAL_WORKSPACE: 1.0,
        AreaType.WAREHOUSE: 1.0,
        AreaType.ARCHIVE: 1.0,
        AreaType.COLD_STORAGE: 1.0,
        AreaType.LOGISTICS: 1.0,
        AreaType.SALESROOM: 1.0,
        AreaType.EXHIBITION: 1.0,
        AreaType.TEACHING_ROOM: 1.0,
        AreaType.FLEXIBLE_TEACHING_ROOM: 1.0,
        AreaType.DEDICATED_TEACHING_ROOM: 1.0,
        AreaType.LIBRARY: 1.0,
        AreaType.SPORTS_ROOMS: 1.0,
        AreaType.ASSEMBLY_HALL: 1.0,
        AreaType.STAGE_ROOM: 1.0,
        AreaType.SHOWROOM: 1.0,
        AreaType.CHAPEL: 1.0,
        AreaType.MEDICAL_ROOM: 1.0,
        AreaType.DEDICATED_MEDICAL_ROOM: 1.0,
        AreaType.SURGERY_ROOM: 1.0,
        AreaType.RADIATION_DIAGNOSIS: 1.0,
        AreaType.RADATION_THERAPY: 1.0,
        AreaType.PHYSIO_AND_REHABILITATION: 1.0,
        AreaType.MEDICAL_BEDROOM: 1.0,
        AreaType.DEDICATED_MEDICAL_BEDROOM: 1.0,
        AreaType.SANITARY_ROOMS: 1.0,
        AreaType.CLOAKROOM: 1.0,
        AreaType.PASSENGER_PLATFORM: 1.0,
        AreaType.HOUSE_TECHNICS_FACILITIES: 1.0,
        AreaType.SHELTER: 1.0,
        AreaType.MOTORCYCLE_PARKING: 1.0,
        AreaType.UUF11_1_UNBEARB__AUSSENFLAECHE: 1.0,
        AreaType.CORRIDORS_AND_HALLS: 1.0,
        AreaType.TRANSPORT_SHAFT: 1.0,
        AreaType.VEHICLE_TRAFFIC_AREA: 1.0,
    }

    SIA_CATEGORIES = {
        SIACategory.ANF,
        SIACategory.HNF,
        SIACategory.NNF,
        SIACategory.FF,
        SIACategory.VF,
    }

    @property
    def DXF_SIA_LAYERS(self):
        from brooks.visualization.floorplans.assetmanager_style import (
            STYLES_BY_SIA416_LAYER,
            DXFSiaDefaultStyle,
        )

        return [
            {
                "layer_name": area_type.name,
                "sia_area_type": area_type,
                "style": STYLES_BY_SIA416_LAYER.get(area_type, DXFSiaDefaultStyle),
            }
            for area_type in self.SIA_CATEGORIES
        ]

    @property
    def AREAS_WITHOUT_CEILINGS(
        self,
    ) -> Set[AreaType]:
        return {
            AreaType.BALCONY,
            AreaType.LIGHTWELL,
            AreaType.PATIO,
            AreaType.TERRACE,
            AreaType.GARDEN,
        }

    @property
    def AREAS_WITHOUT_FLOORS(
        self,
    ) -> Set[AreaType]:
        return {AreaType.VOID, AreaType.LIGHTWELL, AreaType.OUTDOOR_VOID}

    @property
    def STAIR_AREA(
        self,
    ) -> Set[AreaType]:
        return {AreaType.STAIRCASE}

    @property
    def BALCONY_AREAS(
        self,
    ) -> Set[AreaType]:
        return {AreaType.BALCONY}

    @property
    def OUTDOOR_AREAS(
        self,
    ) -> Set[AreaType]:
        return {
            AreaType.WINTERGARTEN,
            AreaType.BALCONY,
            AreaType.LOGGIA,
            AreaType.ARCADE,
            AreaType.GARDEN,
            AreaType.OUTDOOR_VOID,
            AreaType.PATIO,
            AreaType.TERRACE,
        }

    @property
    def DINING_AREAS(
        self,
    ) -> Set[AreaType]:
        return {
            AreaType.KITCHEN_DINING,
            AreaType.DINING,
            AreaType.LIVING_DINING,
            AreaType.CANTEEN,
        }

    @property
    def RESIDENTIAL_KITCHEN_AREAS(
        self,
    ) -> Set[AreaType]:
        return {AreaType.KITCHEN}

    @property
    def ROOM_VECTOR_NAMING(
        self,
    ) -> Dict[AreaType, str]:
        """AreaTypes not defined here will not be present in the PH result vector"""
        from common_utils.constants import PRICEHUBBLE_AREA_TYPES

        return {
            AreaType.NOT_DEFINED: PRICEHUBBLE_AREA_TYPES.NOT_DEFINED.value,
            AreaType.STAIRCASE: PRICEHUBBLE_AREA_TYPES.CORRIDOR.value,
            AreaType.ROOM: PRICEHUBBLE_AREA_TYPES.ROOM.value,
            AreaType.LIVING_ROOM: PRICEHUBBLE_AREA_TYPES.ROOM.value,
            AreaType.LIVING_DINING: PRICEHUBBLE_AREA_TYPES.ROOM.value,
            AreaType.BEDROOM: PRICEHUBBLE_AREA_TYPES.ROOM.value,
            AreaType.DINING: PRICEHUBBLE_AREA_TYPES.ROOM.value,
            AreaType.KITCHEN: PRICEHUBBLE_AREA_TYPES.KITCHEN.value,
            AreaType.KITCHEN_DINING: PRICEHUBBLE_AREA_TYPES.KITCHEN_DINING.value,
            AreaType.BATHROOM: PRICEHUBBLE_AREA_TYPES.BATHROOM.value,
            AreaType.CORRIDOR: PRICEHUBBLE_AREA_TYPES.CORRIDOR.value,
            AreaType.BALCONY: PRICEHUBBLE_AREA_TYPES.BALCONY.value,
            AreaType.STOREROOM: PRICEHUBBLE_AREA_TYPES.STOREROOM.value,
            AreaType.LOGGIA: PRICEHUBBLE_AREA_TYPES.LOGGIA.value,
            AreaType.WINTERGARTEN: PRICEHUBBLE_AREA_TYPES.WINTERGARTEN.value,
            AreaType.OFFICE: PRICEHUBBLE_AREA_TYPES.ROOM.value,
            AreaType.OFFICE_TECH_ROOM: "OFFICE_TECH_ROOM",
            AreaType.SPECIAL_WORKSPACE: "SPECIAL_WORKSPACE",
            AreaType.RADIATION_DIAGNOSIS: "RADIATION_DIAGNOSIS",
            AreaType.WATER_SUPPLY: "WATER_SUPPLY",
            AreaType.OPERATIONS_FACILITIES: "OPERATIONS_FACILITIES",
            AreaType.EXHIBITION: "EXHIBITION",
            AreaType.BREAK_ROOM: "BREAK_ROOM",
            AreaType.ELECTRICAL_SUPPLY: "ELECTRICAL_SUPPLY",
            AreaType.WAREHOUSE: "WAREHOUSE",
            AreaType.MEDICAL_ROOM: "MEDICAL_ROOM",
            AreaType.WASTEWATER: "WASTEWATER",
            AreaType.ELEVATOR_FACILITIES: "ELEVATOR_FACILITIES",
            AreaType.LIVESTOCK: "LIVESTOCK",
            AreaType.PLANTS: "PLANTS",
            AreaType.RECEPTION_ROOM: "RECEPTION_ROOM",
            AreaType.ASSEMBLY_HALL: "ASSEMBLY_HALL",
            AreaType.TECHNICAL_LAB: "TECHNICAL_LAB",
            AreaType.BUF10_1_AUSSEN_PP_FAHRZEUG: "BUF10_1_AUSSEN_PP_FAHRZEUG",
            AreaType.HOUSE_TECHNICS_FACILITIES: "HOUSE_TECHNICS_FACILITIES",
            AreaType.SURGERY_ROOM: "SURGERY_ROOM",
            AreaType.SPORTS_ROOMS: "SPORTS_ROOMS",
            AreaType.FACTORY_ROOM: "FACTORY_ROOM",
            AreaType.OFFICE_SPACE: "OFFICE_SPACE",
            AreaType.PRISON_CELL: "PRISON_CELL",
            AreaType.CLOAKROOM: "CLOAKROOM",
            AreaType.TEACHING_ROOM: "TEACHING_ROOM",
            AreaType.RADATION_THERAPY: "RADATION_THERAPY",
            AreaType.CHEMICAL_LAB: "CHEMICAL_LAB",
            AreaType.BUF10_5_BEARB__AUSSENFLAECHE: "BUF10_5_BEARB__AUSSENFLAECHE",
            AreaType.TRANSPORT_SHAFT: "TRANSPORT_SHAFT",
            AreaType.HEATING: "HEATING",
            AreaType.UUF11_1_UNBEARB__AUSSENFLAECHE: "UUF11_1_UNBEARB__AUSSENFLAECHE",
            AreaType.STAGE_ROOM: "STAGE_ROOM",
            AreaType.LOGISTICS: "LOGISTICS",
            AreaType.OPEN_PLAN_OFFICE: "OPEN_PLAN_OFFICE",
            AreaType.DEDICATED_MEDICAL_BEDROOM: "DEDICATED_MEDICAL_BEDROOM",
            AreaType.TELECOMMUNICATIONS: "TELECOMMUNICATIONS",
            AreaType.DEDICATED_MEDICAL_ROOM: "DEDICATED_MEDICAL_ROOM",
            AreaType.COMMUNITY_ROOM: "COMMUNITY_ROOM",
            AreaType.PASSENGER_PLATFORM: "PASSENGER_PLATFORM",
            AreaType.CONTROL_ROOM: "CONTROL_ROOM",
            AreaType.AIR: "AIR",
            AreaType.BUF10_4_AUSSEN_PP_FAHRRAD: "BUF10_4_AUSSEN_PP_FAHRRAD",
            AreaType.MEDICAL_BEDROOM: "MEDICAL_BEDROOM",
            AreaType.SALESROOM: "SALESROOM",
            AreaType.SHELTER: "SHELTER",
            AreaType.CHAPEL: "CHAPEL",
            AreaType.WORKSHOP: "WORKSHOP",
            AreaType.DESIGN_ROOM: "DESIGN_ROOM",
            AreaType.FLEXIBLE_TEACHING_ROOM: "FLEXIBLE_TEACHING_ROOM",
            AreaType.BUF10_3_AUSSEN_PP_MOTO: "BUF10_3_AUSSEN_PP_MOTO",
            AreaType.BUF10_2_UEBERDACHTE_AUSSEN_PP_FAHRZEUG: "BUF10_2_UEBERDACHTE_AUSSEN_PP_FAHRZEUG",
            AreaType.COLD_STORAGE: "COLD_STORAGE",
            AreaType.LIBRARY: "LIBRARY",
            AreaType.PHYSIO_AND_REHABILITATION: "PHYSIO_AND_REHABILITATION",
            AreaType.GAS: "GAS",
            AreaType.WAITING_ROOM: "WAITING_ROOM",
            AreaType.PHYSICS_LAB: "PHYSICS_LAB",
            AreaType.MEETING_ROOM: "MEETING_ROOM",
            AreaType.COMMON_KITCHEN: "COMMON_KITCHEN",
            AreaType.SANITARY_ROOMS: "SANITARY_ROOMS",
            AreaType.CANTEEN: "CANTEEN",
            AreaType.CORRIDORS_AND_HALLS: "CORRIDORS_AND_HALLS",
            AreaType.VEHICLE_TRAFFIC_AREA: "VEHICLE_TRAFFIC_AREA",
            AreaType.SHOWROOM: "SHOWROOM",
            AreaType.MOTORCYCLE_PARKING: "MOTORCYCLE_PARKING",
            AreaType.ARCHIVE: "ARCHIVE",
            AreaType.DEDICATED_TEACHING_ROOM: "DEDICATED_TEACHING_ROOM",
            AreaType.COUNTER_ROOM: "COUNTER_ROOM",
        }

    @property
    def AREA_TYPES_ACCEPTING_SHAFTS(
        self,
    ) -> Set[AreaType]:
        return {
            AreaType.VOID,
            AreaType.LIGHTWELL,
            AreaType.OUTDOOR_VOID,
            self.DEFAULT_SHAFT_AREA,
            AreaType.TECHNICAL_AREA,
            AreaType.WASTEWATER,
            AreaType.WATER_SUPPLY,
            AreaType.HEATING,
            AreaType.GAS,
            AreaType.ELECTRICAL_SUPPLY,
            AreaType.TELECOMMUNICATIONS,
            AreaType.AIR,
            AreaType.ELEVATOR_FACILITIES,
            AreaType.OPERATIONS_FACILITIES,
        }

    @property
    def AREA_TYPES_FEATURE_MAPPING(
        self,
    ) -> Dict[FeatureType, Set[AreaType]]:
        return {
            FeatureType.BATHTUB: {AreaType.BATHROOM, AreaType.SANITARY_ROOMS},
            FeatureType.TOILET: {AreaType.BATHROOM, AreaType.SANITARY_ROOMS},
            FeatureType.SHOWER: {AreaType.BATHROOM, AreaType.SANITARY_ROOMS},
            FeatureType.KITCHEN: {
                AreaType.KITCHEN_DINING,
                AreaType.KITCHEN,
                AreaType.COMMON_KITCHEN,
            },
        }

    @property
    def LIVING_AND_BEDROOMS(
        self,
    ) -> Set[AreaType]:
        return self.DINING_AREAS | {
            AreaType.ROOM,
            AreaType.BEDROOM,
            AreaType.LIVING_ROOM,
            AreaType.LIVING_DINING,
        }

    @property
    def CIRCULATION_AREAS(
        self,
    ) -> Set[AreaType]:
        """Used in the competition tool"""
        return {AreaType.CORRIDOR}

    @property
    def STOREROOM_AREAS(
        self,
    ) -> Set[AreaType]:
        return {AreaType.STOREROOM}

    @property
    def AREAS_WINDOW_REQUIRED(
        self,
    ) -> Set[AreaType]:
        return {
            AreaType.ROOM,
            AreaType.KITCHEN_DINING,
            AreaType.LIVING_DINING,
            AreaType.BEDROOM,
            AreaType.LIVING_ROOM,
            AreaType.LIGHTWELL,
        }

    @property
    def AREA_TYPES_WITH_WATER_SUPPLY(
        self,
    ) -> Set[AreaType]:
        return {
            AreaType.KITCHEN,
            AreaType.KITCHEN_DINING,
            AreaType.BATHROOM,
            AreaType.SHAFT,
        }


class CLASSIFICATIONS(Enum):
    UNIFIED = UnifiedClassificationScheme


class ClassificationJSONEncoder:
    @classmethod
    def default(cls, obj):
        if isinstance(obj, Enum):
            if isinstance(obj, AreaTreeLevel):
                return obj.value
            return str(obj)

        if isinstance(obj, (int, float, str)) or obj is None:
            return obj

        if isinstance(obj, dict):
            return {cls.default(k): cls.default(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple, set)):
            return [cls.default(k) for k in obj]
