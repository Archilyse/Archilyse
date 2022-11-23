import contextlib
from enum import Enum, unique

from common_utils.constants import UNIT_USAGE


class AreaType(Enum):
    """
    Adding a new entity here means we have to review:
    - Migration ofc (covered by integration tests)
    - PNG namings (covered by unittests)
    - Classification scheme requires multiple changes:
        - ROOM_VECTOR_NAMING -> To map the new type to a known PH type
        - NBR_OF_ROOMS_COUNTER -> If it contributes to the total number of rooms
        - _AREA_TREE:
            - High level to make it appear in the classification step of the pipeline, with the color, etc.
            - If it belongs to a collection, such as living dining to AreaTypeCollection.ROOMS, which will make it
            count as a net area contributor, for instance, and will make it contribute to the right SIA dimension
    """

    ARCADE = "ARCADE"  # outdoor Erschliessung
    BALCONY = "BALCONY"  # outdoor area WITHOUT roof
    BASEMENT = "BASEMENT"
    BASEMENT_COMPARTMENT = "BASEMENT_COMPARTMENT"  # rooms and areas which contain storage compartment assigned to apartments (outside apartment)
    BATHROOM = "BATHROOM"  # Any rooms with showers, bathtub, toilet...in commercial and public units also "Vorraum" and "Garderobe"
    BEDROOM = "BEDROOM"
    BIKE_STORAGE = "BIKE_STORAGE"  # storage room for bikes (not to be splitted from corridor, only to be used for separated rooms)
    CARPARK = (
        "CARPARK"  # car parking and circulation area (incl ramp if inside building)
    )
    CORRIDOR = "CORRIDOR"  # any circualtion area apart from staircase and Laubengang
    DINING = "DINING"
    ELEVATOR = "ELEVATOR"  # area of the elevator CABIN (only cabin not lift shaft)
    FOYER = "FOYER"
    GARAGE = "GARAGE"
    GARDEN = "GARDEN"
    KITCHEN = "KITCHEN"  # separated room or separated area(area splitter) with kitchen elements
    KITCHEN_DINING = "KITCHEN_DINING"
    LIGHTWELL = "LIGHTWELL"  # area of a lightwell (no ceiling no floor)
    LIVING_DINING = "LIVING_DINING"
    LIVING_ROOM = "LIVING_ROOM"
    LOBBY = "LOBBY"
    LOGGIA = "LOGGIA"  # outdoor area WITH roof
    NOT_DEFINED = "NOT_DEFINED"
    OFFICE = "OFFICE"
    OIL_TANK = "OIL_TANK"
    OUTDOOR_VOID = "OUTDOOR_VOID"
    PATIO = "PATIO"
    PRAM = "PRAM"
    PRAM_AND_BIKE_STORAGE_ROOM = "PRAM_AND_BIKE_STORAGE_ROOM"  # mixed storage room for prams and bikes (not to be splitted from corridor, only to be used for separated rooms)
    ROOM = "ROOM"  # Any kind of room serving the main use of a unit (office, living space,...)
    SHAFT = "SHAFT"  # technical installations
    STAIRCASE = "STAIRCASE"
    STOREROOM = "STOREROOM"  # any kind of storeroom
    STUDIO = "STUDIO"
    TECHNICAL_AREA = "TECHNICAL_AREA"  # Rooms and areas for technical installations (heating, water, lift,...) -> not shafts
    TERRACE = "TERRACE"
    VOID = "VOID"  # area of a void (no floor)
    WASH_AND_DRY_ROOM = (
        "WASH_DRY_ROOM"  # Public shared washing machines and dryers (not commercial)
    )
    WINTERGARTEN = "WINTERGARTEN"

    # Formerly SIADynamicAreaType which will all be renamed
    MOTORCYCLE_PARKING = "MOTORCYCLE_PARKING"
    VEHICLE_TRAFFIC_AREA = "VEHICLE_TRAFFIC_AREA"
    COMMUNITY_ROOM = "COMMUNITY_ROOM"
    BREAK_ROOM = "BREAK_ROOM"
    WAITING_ROOM = "WAITING_ROOM"
    CANTEEN = "CANTEEN"
    PRISON_CELL = "PRISON_CELL"
    OFFICE_SPACE = "OFFICE_SPACE"
    OPEN_PLAN_OFFICE = "OPEN_PLAN_OFFICE"
    MEETING_ROOM = "MEETING_ROOM"
    DESIGN_ROOM = "DESIGN_ROOM"
    COUNTER_ROOM = "COUNTER_ROOM"
    CONTROL_ROOM = "CONTROL_ROOM"
    RECEPTION_ROOM = "RECEPTION_ROOM"
    OFFICE_TECH_ROOM = "OFFICE_TECH_ROOM"
    FACTORY_ROOM = "FACTORY_ROOM"
    WORKSHOP = "WORKSHOP"
    TECHNICAL_LAB = "TECHNICAL_LAB"
    PHYSICS_LAB = "PHYSICS_LAB"
    CHEMICAL_LAB = "CHEMICAL_LAB"
    LIVESTOCK = "LIVESTOCK"
    PLANTS = "PLANTS"
    COMMON_KITCHEN = "COMMON_KITCHEN"
    SPECIAL_WORKSPACE = "SPECIAL_WORKSPACE"
    WAREHOUSE = "WAREHOUSE"
    ARCHIVE = "ARCHIVE"
    COLD_STORAGE = "COLD_STORAGE"
    LOGISTICS = "LOGISTICS"
    SALESROOM = "SALESROOM"
    EXHIBITION = "EXHIBITION"
    TEACHING_ROOM = "TEACHING_ROOM"
    FLEXIBLE_TEACHING_ROOM = "FLEXIBLE_TEACHING_ROOM"
    DEDICATED_TEACHING_ROOM = "DEDICATED_TEACHING_ROOM"
    LIBRARY = "LIBRARY"
    SPORTS_ROOMS = "SPORTS_ROOMS"
    ASSEMBLY_HALL = "ASSEMBLY_HALL"
    STAGE_ROOM = "STAGE_ROOM"
    SHOWROOM = "SHOWROOM"
    CHAPEL = "CHAPEL"
    MEDICAL_ROOM = "MEDICAL_ROOM"
    DEDICATED_MEDICAL_ROOM = "DEDICATED_MEDICAL_ROOM"
    SURGERY_ROOM = "SURGERY_ROOM"
    RADIATION_DIAGNOSIS = "RADIATION_DIAGNOSIS"
    RADATION_THERAPY = "RADATION_THERAPY"
    PHYSIO_AND_REHABILITATION = "PHYSIO_AND_REHABILITATION"
    MEDICAL_BEDROOM = "MEDICAL_BEDROOM"
    DEDICATED_MEDICAL_BEDROOM = "DEDICATED_MEDICAL_BEDROOM"
    SANITARY_ROOMS = "SANITARY_ROOMS"
    CLOAKROOM = "CLOAKROOM"
    PASSENGER_PLATFORM = "PASSENGER_PLATFORM"
    HOUSE_TECHNICS_FACILITIES = "HOUSE_TECHNICS_FACILITIES"
    SHELTER = "SHELTER"
    WASTEWATER = "WASTEWATER"
    WATER_SUPPLY = "WATER_SUPPLY"
    HEATING = "HEATING"
    GAS = "GAS"
    ELECTRICAL_SUPPLY = "ELECTRICAL_SUPPLY"
    TELECOMMUNICATIONS = "TELECOMMUNICATIONS"
    AIR = "AIR"
    ELEVATOR_FACILITIES = "ELEVATOR_FACILITIES"
    OPERATIONS_FACILITIES = "OPERATIONS_FACILITIES"
    CORRIDORS_AND_HALLS = "CORRIDORS_AND_HALLS"
    TRANSPORT_SHAFT = "TRANSPORT_SHAFT"

    # area types that we need that are not part of unified classification scheme (needs to be extended)
    BUF10_1_AUSSEN_PP_FAHRZEUG = "BUF10_1_AUSSEN_PP_FAHRZEUG"
    BUF10_5_BEARB__AUSSENFLAECHE = "BUF10_5_BEARB__AUSSENFLAECHE"
    BUF10_3_AUSSEN_PP_MOTO = "BUF10_3_AUSSEN_PP_MOTO"
    BUF10_2_UEBERDACHTE_AUSSEN_PP_FAHRZEUG = "BUF10_2_UEBERDACHTE_AUSSEN_PP_FAHRZEUG"
    BUF10_4_AUSSEN_PP_FAHRRAD = "BUF10_4_AUSSEN_PP_FAHRRAD"
    UUF11_1_UNBEARB__AUSSENFLAECHE = "UUF11_1_UNBEARB__AUSSENFLAECHE"


class SIACategory(Enum):
    FF = "FF"
    VF = "VF"
    HNF = "HNF"
    NNF = "NNF"
    ANF = "ANF"


AllAreaTypes = Enum(  # type: ignore
    names={
        **{x.name: x.value for x in AreaType},
    },
    value="AllAreaTypes",
)


def get_valid_area_type_from_string(name: str) -> AreaType:
    with contextlib.suppress(KeyError):
        return AreaType[name]
    raise Exception(f"Invalid area type: {name}")


COMPATIBLE_AREA_TYPES = [
    (AreaType.KITCHEN_DINING, {AreaType.KITCHEN, AreaType.KITCHEN_DINING})
]


@unique
class FeatureType(Enum):
    """definition of features types"""

    NOT_DEFINED = 0
    BATHTUB = 1
    SHOWER = 2
    SINK = 3
    TOILET = 4
    KITCHEN = 6
    SEAT = 8
    STAIRS = 9
    SHAFT = 12
    ELEVATOR = 16
    WASHING_MACHINE = 19
    CAR_PARKING = 21
    RAMP = 23
    OFFICE_DESK = 24
    BIKE_PARKING = 25
    BUILT_IN_FURNITURE = 26


@unique
class LayoutType(Enum):
    """definition of space types"""

    APARTMENT = 0
    OFFICE = 1
    BUILDING = 2
    NOT_DEFINED = 3


@unique
class OpeningType(Enum):
    """definition of opening types"""

    NOT_DEFINED = 0
    DOOR = 1
    # This 2 extra windows should be deleted
    # but dont wanna mess with auto classification
    WINDOW_ENVELOPE = 2
    WINDOW_INTERIOR = 3
    WINDOW = 4
    ENTRANCE_DOOR = 5


@unique
class SeparatorType(Enum):
    """definition of separator types"""

    NOT_DEFINED = 0
    WALL = 1
    COLUMN = 2
    RAILING = 3
    AREA_SPLITTER = 4


@unique
class SpaceType(Enum):
    """definition of space types"""

    NOT_DEFINED = 0


@unique
class AnnotationType(Enum):
    AREA_SPLITTER = "area_splitter"
    WALL = "walls"
    COLUMN = "columns"
    RAILING = "railings"
    WINDOW = "windows"
    DOOR = "doors"
    ENTRANCE_DOOR = "entrance_doors"
    SHAFT = "shafts"
    STAIRS = "stairs"
    KITCHEN = "kitchens"
    TOILET = "toilets"
    SINK = "sinks"
    SHOWER = "showers"
    BATHTUB = "bathtubs"
    ELEVATOR = "elevators"
    SEAT = "seats"
    NOT_DEFINED = "not_defined"
    WASHING_MACHINE = "washing_machines"
    CAR_PARKING = "car_parking"
    RAMP = "ramp"
    OFFICE_DESK = "office_desk"
    BIKE_PARKING = "bike_parking"
    BUILT_IN_FURNITURE = "built_in_furniture"


class OpeningSubType(Enum):
    DEFAULT = "default_door"  # normal winged door
    SLIDING = "sliding_door"


AREA_TYPE_USAGE = {
    AreaType.ARCADE: {UNIT_USAGE.COMMERCIAL},
    AreaType.BALCONY: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
    },
    AreaType.BASEMENT_COMPARTMENT: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.BASEMENT: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.BATHROOM: {
        UNIT_USAGE.RESIDENTIAL,
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.JANITOR,
    },
    AreaType.BEDROOM: {UNIT_USAGE.RESIDENTIAL},
    AreaType.BIKE_STORAGE: {UNIT_USAGE.PUBLIC},
    AreaType.CARPARK: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.CORRIDOR: {UNIT_USAGE.RESIDENTIAL},
    AreaType.DINING: {UNIT_USAGE.RESIDENTIAL},
    AreaType.ELEVATOR: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.FOYER: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.GARAGE: {UNIT_USAGE.PUBLIC},
    AreaType.GARDEN: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC, UNIT_USAGE.RESIDENTIAL},
    AreaType.KITCHEN: {UNIT_USAGE.RESIDENTIAL},
    AreaType.KITCHEN_DINING: {UNIT_USAGE.RESIDENTIAL},
    AreaType.LIGHTWELL: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
    },
    AreaType.LIVING_DINING: {UNIT_USAGE.RESIDENTIAL},
    AreaType.LIVING_ROOM: {UNIT_USAGE.RESIDENTIAL},
    AreaType.LOBBY: {UNIT_USAGE.COMMERCIAL},
    AreaType.LOGGIA: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC, UNIT_USAGE.RESIDENTIAL},
    AreaType.OFFICE: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.JANITOR},
    AreaType.OIL_TANK: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.OUTDOOR_VOID: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
    },
    AreaType.PATIO: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC, UNIT_USAGE.RESIDENTIAL},
    AreaType.PRAM_AND_BIKE_STORAGE_ROOM: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
    },
    AreaType.PRAM: {UNIT_USAGE.PUBLIC, UNIT_USAGE.COMMERCIAL},
    AreaType.ROOM: {UNIT_USAGE.RESIDENTIAL},
    AreaType.SHAFT: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC, UNIT_USAGE.RESIDENTIAL},
    AreaType.STAIRCASE: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.STOREROOM: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
        UNIT_USAGE.JANITOR,
    },
    AreaType.STUDIO: {UNIT_USAGE.RESIDENTIAL},
    AreaType.TECHNICAL_AREA: {
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
        UNIT_USAGE.JANITOR,
    },
    AreaType.TERRACE: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
        UNIT_USAGE.RESIDENTIAL,
    },
    AreaType.VOID: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC, UNIT_USAGE.RESIDENTIAL},
    AreaType.WASH_AND_DRY_ROOM: {UNIT_USAGE.PUBLIC},
    AreaType.WINTERGARTEN: {UNIT_USAGE.RESIDENTIAL},
    AreaType.WASTEWATER: {UNIT_USAGE.PUBLIC},
    AreaType.WATER_SUPPLY: {UNIT_USAGE.PUBLIC},
    AreaType.HEATING: {UNIT_USAGE.PUBLIC},
    AreaType.GAS: {UNIT_USAGE.PUBLIC},
    AreaType.ELECTRICAL_SUPPLY: {UNIT_USAGE.PUBLIC},
    AreaType.TELECOMMUNICATIONS: {UNIT_USAGE.PUBLIC},
    AreaType.AIR: {UNIT_USAGE.PUBLIC},
    AreaType.ELEVATOR_FACILITIES: {UNIT_USAGE.PUBLIC},
    AreaType.OPERATIONS_FACILITIES: {UNIT_USAGE.PUBLIC},
    AreaType.COMMUNITY_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.BREAK_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.WAITING_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.CANTEEN: {UNIT_USAGE.COMMERCIAL},
    AreaType.PRISON_CELL: {UNIT_USAGE.COMMERCIAL},
    AreaType.OFFICE_SPACE: {UNIT_USAGE.COMMERCIAL},
    AreaType.OPEN_PLAN_OFFICE: {UNIT_USAGE.COMMERCIAL},
    AreaType.MEETING_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.DESIGN_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.COUNTER_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.CONTROL_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.RECEPTION_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.OFFICE_TECH_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.FACTORY_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.WORKSHOP: {UNIT_USAGE.COMMERCIAL},
    AreaType.TECHNICAL_LAB: {UNIT_USAGE.COMMERCIAL},
    AreaType.PHYSICS_LAB: {UNIT_USAGE.COMMERCIAL},
    AreaType.CHEMICAL_LAB: {UNIT_USAGE.COMMERCIAL},
    AreaType.LIVESTOCK: {UNIT_USAGE.COMMERCIAL},
    AreaType.PLANTS: {UNIT_USAGE.COMMERCIAL},
    AreaType.COMMON_KITCHEN: {
        UNIT_USAGE.COMMERCIAL,
    },
    AreaType.SPECIAL_WORKSPACE: {UNIT_USAGE.COMMERCIAL},
    AreaType.WAREHOUSE: {UNIT_USAGE.COMMERCIAL},
    AreaType.ARCHIVE: {UNIT_USAGE.COMMERCIAL},
    AreaType.COLD_STORAGE: {UNIT_USAGE.COMMERCIAL},
    AreaType.LOGISTICS: {UNIT_USAGE.COMMERCIAL},
    AreaType.SALESROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.EXHIBITION: {UNIT_USAGE.COMMERCIAL},
    AreaType.TEACHING_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.FLEXIBLE_TEACHING_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.DEDICATED_TEACHING_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.LIBRARY: {UNIT_USAGE.COMMERCIAL},
    AreaType.SPORTS_ROOMS: {UNIT_USAGE.COMMERCIAL},
    AreaType.ASSEMBLY_HALL: {UNIT_USAGE.COMMERCIAL},
    AreaType.STAGE_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.SHOWROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.CHAPEL: {UNIT_USAGE.COMMERCIAL},
    AreaType.MEDICAL_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.DEDICATED_MEDICAL_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.SURGERY_ROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.RADIATION_DIAGNOSIS: {UNIT_USAGE.COMMERCIAL},
    AreaType.RADATION_THERAPY: {UNIT_USAGE.COMMERCIAL},
    AreaType.PHYSIO_AND_REHABILITATION: {UNIT_USAGE.COMMERCIAL},
    AreaType.MEDICAL_BEDROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.DEDICATED_MEDICAL_BEDROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.SANITARY_ROOMS: {UNIT_USAGE.COMMERCIAL, UNIT_USAGE.PUBLIC},
    AreaType.CLOAKROOM: {UNIT_USAGE.COMMERCIAL},
    AreaType.PASSENGER_PLATFORM: {UNIT_USAGE.PUBLIC},
    AreaType.HOUSE_TECHNICS_FACILITIES: {UNIT_USAGE.PUBLIC},
    AreaType.SHELTER: {UNIT_USAGE.PUBLIC},
    AreaType.CORRIDORS_AND_HALLS: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
    },
    AreaType.TRANSPORT_SHAFT: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
    },
    AreaType.VEHICLE_TRAFFIC_AREA: {
        UNIT_USAGE.COMMERCIAL,
        UNIT_USAGE.PUBLIC,
    },
}
