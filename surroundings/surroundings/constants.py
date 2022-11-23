from enum import Enum
from pathlib import Path

from common_utils.constants import REGION, WORKING_DIR, SurroundingType

# This projections allow to make calculation in meters

GEOFABRIK_SUFFIX = "-latest-free.shp"
OSM_REGIONS_FILENAMES = {
    REGION.MC: Path(f"europe/monaco{GEOFABRIK_SUFFIX}"),
    REGION.CH: Path(f"europe/switzerland{GEOFABRIK_SUFFIX}"),
    REGION.DK: Path(f"europe/denmark{GEOFABRIK_SUFFIX}"),
    REGION.AT: Path(f"europe/austria{GEOFABRIK_SUFFIX}"),
    REGION.NO: Path(f"europe/norway{GEOFABRIK_SUFFIX}"),
    REGION.CZ: Path(f"europe/czech-republic{GEOFABRIK_SUFFIX}"),
    REGION.ES: Path(f"europe/spain{GEOFABRIK_SUFFIX}"),
    REGION.AD: Path(f"europe/andorra{GEOFABRIK_SUFFIX}"),
    # # ****************** GERMANY **************************
    REGION.DE_BADEN_WURTTEMBERG: Path(
        f"europe/germany/baden-wuerttemberg{GEOFABRIK_SUFFIX}"
    ),
    REGION.DE_BAYERN: Path(f"europe/germany/bayern{GEOFABRIK_SUFFIX}"),
    REGION.DE_BERLIN: Path(f"europe/germany/berlin{GEOFABRIK_SUFFIX}"),
    REGION.DE_BRANDENBURG: Path(f"europe/germany/brandenburg{GEOFABRIK_SUFFIX}"),
    REGION.DE_BREMEN: Path(f"europe/germany/bremen{GEOFABRIK_SUFFIX}"),
    REGION.DE_HAMBURG: Path(f"europe/germany/hamburg{GEOFABRIK_SUFFIX}"),
    REGION.DE_HESSEN: Path(f"europe/germany/hessen{GEOFABRIK_SUFFIX}"),
    REGION.DE_MECKLENBURG_VORPOMMERN: Path(
        f"europe/germany/mecklenburg-vorpommern{GEOFABRIK_SUFFIX}"
    ),
    REGION.DE_NIEDERSACHSEN: Path(f"europe/germany/niedersachsen{GEOFABRIK_SUFFIX}"),
    REGION.DE_NORDRHEIN_WESTFALEN: Path(
        f"europe/germany/nordrhein-westfalen{GEOFABRIK_SUFFIX}"
    ),
    REGION.DE_RHEINLAND_PFALZ: Path(
        f"europe/germany/rheinland-pfalz{GEOFABRIK_SUFFIX}"
    ),
    REGION.DE_SAARLAND: Path(f"europe/germany/saarland{GEOFABRIK_SUFFIX}"),
    REGION.DE_SACHSEN: Path(f"europe/germany/sachsen{GEOFABRIK_SUFFIX}"),
    REGION.DE_SACHSEN_ANHALT: Path(f"europe/germany/sachsen-anhalt{GEOFABRIK_SUFFIX}"),
    REGION.DE_SCHLESWIG_HOLSTEIN: Path(
        f"europe/germany/schleswig-holstein{GEOFABRIK_SUFFIX}"
    ),
    REGION.DE_THURINGEN: Path(f"europe/germany/thueringen{GEOFABRIK_SUFFIX}"),
    # ****************** UNITED STATES **************************
    REGION.US_GEORGIA: Path(f"north-america/us/georgia{GEOFABRIK_SUFFIX}"),
    REGION.US_PENNSYLVANIA: Path(f"north-america/us/pennsylvania{GEOFABRIK_SUFFIX}"),
    # # ****************** ASIA ***********************************
    REGION.SG: Path(f"asia/malaysia-singapore-brunei{GEOFABRIK_SUFFIX}"),
}
OSM_DIR = WORKING_DIR.joinpath("OSM")


PERCENTAGE_AREA_OVERLAP_TO_REMOVE_BUILDING = 0.1
LK25_SOUTH_WEST_INDEX = 1360
LK25_MIN_EAST = 2.48e6
LK25_MIN_NORTH = 1.074e6
LK25_TILE_WIDTH = 17.5e3
LK25_TILE_HEIGHT = 12e3
LK25_TILES_PER_ROW = 20

#
# All values below are in meters
#
BOUNDING_BOX_EXTENSION_SAMPLE = 200
BOUNDING_BOX_EXTENSION = 500
MULTIPLIER_BOUNDING_BOX_BIG_ITEMS = 10
BOUNDING_BOX_EXTENSION_ALTI = BOUNDING_BOX_EXTENSION
BOUNDING_BOX_EXTENSION_RIVERS = (
    BOUNDING_BOX_EXTENSION * MULTIPLIER_BOUNDING_BOX_BIG_ITEMS
)
BOUNDING_BOX_EXTENSION_LAKES = (
    BOUNDING_BOX_EXTENSION * MULTIPLIER_BOUNDING_BOX_BIG_ITEMS
)
BOUNDING_BOX_EXTENSION_NOISE = BOUNDING_BOX_EXTENSION
BOUNDING_BOX_EXTENSION_MOUNTAINS = BOUNDING_BOX_EXTENSION * 100
BOUNDING_BOX_EXTENSION_BUILDINGS = BOUNDING_BOX_EXTENSION
BOUNDING_BOX_EXTENSION_RAILROADS = BOUNDING_BOX_EXTENSION
BOUNDING_BOX_EXTENSION_SEA = BOUNDING_BOX_EXTENSION * MULTIPLIER_BOUNDING_BOX_BIG_ITEMS
BOUNDING_BOX_EXTENSION_GROUNDS = (
    BOUNDING_BOX_EXTENSION * MULTIPLIER_BOUNDING_BOX_BIG_ITEMS
)
BOUNDING_BOX_EXTENSION_GEOREFERENCING = 200
BOUNDING_BOX_EXTENSION_TARGET_BUILDING = 50
MAXIMUM_DISTANCE_TO_TARGET_BUILDING = 10


FOREST_GROUND_OFFSET = 0.05
PARKS_GROUND_OFFSET = 0.1
WATER_GROUND_OFFSET = 0.15
STREETS_GROUND_OFFSET = 0.2
RAILWAYS_GROUND_OFFSET = 0.25


OSM_OFFSETS = {
    SurroundingType.RAILROADS: RAILWAYS_GROUND_OFFSET,
    SurroundingType.STREETS: STREETS_GROUND_OFFSET,
    SurroundingType.RIVERS: WATER_GROUND_OFFSET,
    SurroundingType.LAKES: WATER_GROUND_OFFSET,
    SurroundingType.PARKS: PARKS_GROUND_OFFSET,
}


class UNMountainClass(Enum):
    CLASS_1 = 1
    CLASS_2 = 2
    CLASS_3 = 3
    CLASS_4 = 4
    CLASS_5 = 5
    CLASS_6 = 6
    CLASS_7 = 7
    GROUNDS = 8
