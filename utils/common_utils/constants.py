import mimetypes
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Literal

import numpy as np  # type: ignore

########################################################################################
from common_utils.classes import AutoNameEnum

SMALL_ROOM_SIZE = 5.0  # constant for remaining logic requested by portfolio client life for small bathrooms and storerooms
ARTEFACT_AREA_SIZE = 1e-3  # in m2
GEOMETRIES_PRECISION = 12
OPENING_BUFFER_TO_CUT_WALLS = 0.01  # in m
########################################################################################

FLOORPLAN_UPLOAD_DIR = Path(os.environ["FLOORPLAN_UPLOAD_DIR"])
WORKING_DIR = Path(os.environ["WORKING_DIR"])

#
GOOGLE_CLOUD_BUCKET = os.environ["GCLOUD_BUCKET"]
VOLUME_BUCKET: str = os.environ.get("VOLUME_BUCKET", "")
#
# Public bucket
#

GOOGLE_CLOUD_LOCATION = "europe-west6"
GOOGLE_CLOUD_PLAN_IMAGES = Path("plan_images")
GOOGLE_CLOUD_PLAN_AREA_IMAGES = Path("plan_area_images")
GOOGLE_CLOUD_CLIENT_LOGOS = Path("client_logos")
GOOGLE_CLOUD_3D_TRIANGLES = Path("building_triangles")
GOOGLE_CLOUD_DXF_FILES = Path("dxf_files")
GOOGLE_CLOUD_CLOUD_CONVERT_FILES = Path("cloud_convert_files")
GOOGLE_CLOUD_BUILDING_SURROUNDINGS = Path("buildings")
GOOGLE_CLOUD_VIEW_SURROUNDINGS = Path("surroundings")
GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS = Path("sample_surroundings")
GOOGLE_CLOUD_RESULT_IMAGES = Path("images")
GOOGLE_CLOUD_SWISSTOPO = Path("swisstopo")
GOOGLE_CLOUD_EU_NOISE = Path("eu_noise")
GOOGLE_CLOUD_SRTM = Path("srtm")
GOOGLE_CLOUD_OSM = Path("osm")
GOOGLE_CLOUD_QUAVIS = Path("quavis")
GOOGLE_CLOUD_DELIVERABLES = Path("deliverables")
GOOGLE_CLOUD_SITE_IFC_FILES = Path("ifc_files")
GOOGLE_CLOUD_BOXPLOTS_DATAFRAME = Path("boxplots/slam_dataframe_v2.zip")
GOOGLE_CLOUD_BENCHMARK_APARTMENT_SCORES = Path(
    "datasets/2022_09_27/apartment_score_percentiles.zip"
)
GOOGLE_CLOUD_BENCHMARK_PERCENTILES = Path(
    "datasets/2022_09_27/dimension_percentiles.zip"
)
GOOGLE_CLOUD_BENCHMARK_CLUSTER_SIZES = Path("datasets/2022_09_27/reference_sizes.zip")
GOOGLE_CLOUD_POTENTIAL_DATASET = Path("datasets/potential")

########################################################################################

OUTPUT_DIR = WORKING_DIR.joinpath("output")
BUILDING_SURROUNDINGS_DIR = OUTPUT_DIR.joinpath("buildings/")
SURROUNDINGS_DIR = OUTPUT_DIR.joinpath("surroundings/")
PLOT_DIR = OUTPUT_DIR.joinpath("plots/")

########################################################################################


# Boxplots
BOXPLOT_DIR = WORKING_DIR.joinpath("boxplots")
SLAM_DATAFRAME_CSV = BOXPLOT_DIR.joinpath("slam_dataframe.csv")
SLAM_UNIT_DATAFRAME_CSV = BOXPLOT_DIR.joinpath("slam_unit_dataframe.csv")
SLAM_UNIT_DATAFRAME_INSIDE_CSV = BOXPLOT_DIR.joinpath("slam_unit_dataframe_inside.csv")
#
BENCHMARK_DATASET_DIR = WORKING_DIR.joinpath("unitplots")
BENCHMARK_DATASET_SIMULATIONS_PATH = BENCHMARK_DATASET_DIR.joinpath("simulations.csv")
BENCHMARK_DATASET_CLUSTER_SIZES_PATH = BENCHMARK_DATASET_DIR.joinpath(
    "reference_sizes.csv"
)
BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH = BENCHMARK_DATASET_DIR.joinpath(
    "simulations_apartment_scores.csv"
)
BENCHMARK_PERCENTILES_DIMENSIONS_PATH = BENCHMARK_DATASET_DIR.joinpath(
    "dimension_percentiles_per_cluster.json"
)
# SRTM DIRS
#
SRTM_DIR = WORKING_DIR.joinpath("srtm")
SRTM_FILENAME_PATTERN = "{}_{}_1arc_v3.tif"

#
# EU NOISE DIRS
#
EU_NOISE_DIR = WORKING_DIR.joinpath("eu_noise")

#
# SWISSTOPO DIRS
#
SWISSTOPO_DIR = WORKING_DIR
SWISSTOPO_BUILDINGS_DIR = SWISSTOPO_DIR.joinpath(
    "2021_SWISSBUILDINGS3D 2.0/SHP_LV95LN02/"
)
SWISSTOPO_ALTI_DIR = SWISSTOPO_DIR.joinpath("esri_ascii_grid/")
SWISSTOPO_MOUNTAINS_FILE = SWISSTOPO_DIR.joinpath(
    "swisstopo_mountains/swissmountains_50mx50m.tif"
)
########################################################################################

# NOTE: Used for IFC site creation before adding the location from the IFC file
#       asynchronosuly afterwards. The values are outside of the range of lat lon possible values to avoid issues
DEFAULT_IFC_LOCATION = (-999, -999)

QUAVIS_INPUT_FILENAME_TEMPLATE = "{run_id}-in.zip"
QUAVIS_OUTPUT_FILENAME_TEMPLATE = "{run_id}-out.zip"


class LENGTH_SI_UNITS(Enum):
    METRE = 1.0
    CENTIMETRE = 0.01
    MILLIMETRE = 0.0001


SI_UNIT_BY_NAME: dict[str, LENGTH_SI_UNITS] = {
    "m": LENGTH_SI_UNITS.METRE,
    "cm": LENGTH_SI_UNITS.CENTIMETRE,
    "mm": LENGTH_SI_UNITS.MILLIMETRE,
}

WALL_BUFFER_BY_SI_UNIT: dict[LENGTH_SI_UNITS, float] = {
    LENGTH_SI_UNITS.METRE: 0.001,
    LENGTH_SI_UNITS.CENTIMETRE: 0.1,
    LENGTH_SI_UNITS.MILLIMETRE: 1.0,
}


class UNIT_BASICS_DIMENSION(Enum):
    NET_AREA = "net-area"
    NUMBER_OF_ROOMS = "number-of-rooms"
    NUMBER_OF_BALCONIES = "number-of-balconies"
    SIA_416_HNF = "area-sia416-HNF"
    SIA_416_NNF = "area-sia416-NNF"
    SIA_416_FF = "area-sia416-FF"
    SIA_416_VF = "area-sia416-VF"


class SEASONS(Enum):
    SUMMER = datetime(2018, 6, 21)
    WINTER = datetime(2018, 12, 21)


class SUN_DIMENSION(Enum):
    SUN_MARCH_MORNING = "sun-2018-03-21 07:00:00+00:00"
    SUN_MARCH_MIDDAY = "sun-2018-03-21 12:00:00+00:00"
    SUN_MARCH_AFTERNOON = "sun-2018-03-21 17:00:00+00:00"
    SUN_JUNE_MORNING = "sun-2018-06-21 07:00:00+00:00"
    SUN_JUNE_MIDDAY = "sun-2018-06-21 12:00:00+00:00"
    SUN_JUNE_AFTERNOON = "sun-2018-06-21 17:00:00+00:00"
    SUN_DECEMBER_MORNING = "sun-2018-12-21 07:00:00+00:00"
    SUN_DECEMBER_MIDDAY = "sun-2018-12-21 12:00:00+00:00"
    SUN_DECEMBER_AFTERNOON = "sun-2018-12-21 17:00:00+00:00"


class VIEW_DIMENSION(Enum):
    VIEW_SITE = "site"
    VIEW_GROUND = "ground"
    VIEW_BUILDINGS = "buildings"
    VIEW_STREETS = "streets"
    VIEW_GREENERY = "greenery"
    VIEW_RAILWAY_TRACKS = "railway_tracks"
    VIEW_WATER = "water"
    VIEW_MOUNTAINS = "mountains"
    VIEW_ISOVIST = "isovist"
    VIEW_SKY = "sky"


class VIEW_DIMENSION_2(Enum):
    VIEW_SITE = "site"
    VIEW_GROUND = "ground"
    VIEW_BUILDINGS = "buildings"
    VIEW_TERTIARY_STREETS = "tertiary_streets"
    VIEW_SECONDARY_STREETS = "secondary_streets"
    VIEW_PRIMARY_STREETS = "primary_streets"
    VIEW_HIGHWAYS = "highways"
    VIEW_PEDESTRIAN = "pedestrians"
    VIEW_GREENERY = "greenery"
    VIEW_RAILWAY_TRACKS = "railway_tracks"
    VIEW_WATER = "water"
    VIEW_ISOVIST = "isovist"
    VIEW_SKY = "sky"
    MOUNTAINS_CLASS_1 = "mountains_class_1"
    MOUNTAINS_CLASS_2 = "mountains_class_2"
    MOUNTAINS_CLASS_3 = "mountains_class_3"
    MOUNTAINS_CLASS_4 = "mountains_class_4"
    MOUNTAINS_CLASS_5 = "mountains_class_5"
    MOUNTAINS_CLASS_6 = "mountains_class_6"


CONNECTIVITY_DIMENSIONS = {
    "closeness_centrality",
    "betweenness_centrality",
    "eigen_centrality",
    "ENTRANCE_DOOR_distance",
    *{
        f"{a}_distance"
        for a in (
            "ROOM",
            "LIVING_DINING",
            "BATHROOM",
            "KITCHEN",
            "BALCONY",
            "LOGGIA",
        )
    },
}

SUN_V2_QUAVIS_PREFIX = "sun.v2"
SUN_V2_VECTOR_PREFIX = "Sun.v2"

VIEW_SUN_DIMENSIONS = {
    "view": [vd.value for vd in VIEW_DIMENSION],
    "sun": [sd.value for sd in SUN_DIMENSION],
}

VIEW_SUN_AGGREGATION_METHODS = {
    "mean": np.mean,
    "std": np.std,
    "min": np.min,
    "max": np.max,
}


class PRICEHUBBLE_AREA_TYPES(Enum):
    NOT_DEFINED = "Undefined"
    ROOM = "Room"
    KITCHEN = "Kitchen"
    KITCHEN_DINING = "LivingKitchen"
    BATHROOM = "Bathroom"
    CORRIDOR = "Corridor"
    BALCONY = "Balcony"
    STOREROOM = "StorageRoom"
    LOGGIA = "Loggia"
    WINTERGARTEN = "SunRoom"


class RESULT_VECTORS(Enum):
    UNIT_VECTOR_WITH_BALCONY = "unit_vector_with_balcony"
    ROOM_VECTOR_WITH_BALCONY = "room_vector_with_balcony"
    FULL_VECTOR_WITH_BALCONY = "full_vector_with_balcony"
    UNIT_VECTOR_NO_BALCONY = "unit_vector_no_balcony"
    ROOM_VECTOR_NO_BALCONY = "room_vector_no_balcony"
    FULL_VECTOR_NO_BALCONY = "full_vector_no_balcony"
    NEUFERT_AREA_SIMULATIONS = "simulations"
    NEUFERT_UNIT_GEOMETRY = "geometries"


DEFAULT_RESULT_VECTORS = [
    RESULT_VECTORS.UNIT_VECTOR_WITH_BALCONY,
    RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY,
    RESULT_VECTORS.FULL_VECTOR_WITH_BALCONY,
    RESULT_VECTORS.UNIT_VECTOR_NO_BALCONY,
    RESULT_VECTORS.ROOM_VECTOR_NO_BALCONY,
    RESULT_VECTORS.FULL_VECTOR_NO_BALCONY,
]


class NOISE_SURROUNDING_TYPE(Enum):
    TRAFFIC_DAY: Literal["noise_TRAFFIC_DAY"] = "noise_TRAFFIC_DAY"
    TRAFFIC_NIGHT: Literal["noise_TRAFFIC_NIGHT"] = "noise_TRAFFIC_NIGHT"
    TRAIN_DAY: Literal["noise_TRAIN_DAY"] = "noise_TRAIN_DAY"
    TRAIN_NIGHT: Literal["noise_TRAIN_NIGHT"] = "noise_TRAIN_NIGHT"


class NOISE_SOURCE_TYPE(AutoNameEnum):
    TRAIN = auto()
    TRAFFIC = auto()


class NOISE_TIME_TYPE(AutoNameEnum):
    DAY = auto()
    NIGHT = auto()


# TODO: Add wildcard/folder support in download procedure to shorten this (esp. relevant for missing lakes)
# Note: {lk25}, {lk25_subindex_2} and {lk_25_subindex_1} are variables generically
#       replaced by the specific LK25 tile indices that are required for a certain location
SWISSTOPO_BUILDING_FILES_PREFIX = "2021_SWISSBUILDINGS3D_2.0/SHP_LV95LN02/"
SWISSTOPO_REQUIRED_FILES_BUILDINGS = [
    SWISSTOPO_BUILDING_FILES_PREFIX
    + "SWISSBUILDINGS3D_2_0_CHLV95LN02_{lk25}-{lk25_subindex_2}.shp",
    SWISSTOPO_BUILDING_FILES_PREFIX
    + "SWISSBUILDINGS3D_2_0_CHLV95LN02_{lk25}-{lk25_subindex_2}.shx",
    SWISSTOPO_BUILDING_FILES_PREFIX
    + "SWISSBUILDINGS3D_2_0_CHLV95LN02_{lk25}-{lk25_subindex_2}.prj",
    SWISSTOPO_BUILDING_FILES_PREFIX
    + "SWISSBUILDINGS3D_2_0_CHLV95LN02_{lk25}-{lk25_subindex_2}.dbf",
]
SWISSTOPO_REQUIRED_FILES_ALTI = ["esri_ascii_grid/swiss_{lk25}_{lk25_subindex_1}.asc"]
SWISSTOPO_REQUIRED_FILES_MOUNTAINS = ["swisstopo_mountains/swissmountains_50mx50m.tif"]
SWISSTOPO_REQUIRED_FILES_TLM = [
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_STRASSEN/swissTLM3D_TLM_STRASSE.shp",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_STRASSEN/swissTLM3D_TLM_STRASSE.shx",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_STRASSEN/swissTLM3D_TLM_STRASSE.prj",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_STRASSEN/swissTLM3D_TLM_STRASSE.dbf",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.shp",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.shx",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.prj",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_STEHENDES_GEWAESSER.dbf",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_AREALE/swissTLM3D_TLM_FREIZEITAREAL.shp",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_AREALE/swissTLM3D_TLM_FREIZEITAREAL.shx",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_AREALE/swissTLM3D_TLM_FREIZEITAREAL.prj",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_AREALE/swissTLM3D_TLM_FREIZEITAREAL.dbf",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.shp",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.shx",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.prj",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_GEWAESSER/swissTLM3D_TLM_FLIESSGEWAESSER.dbf",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_EINZELBAUM_GEBUESCH.shp",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_EINZELBAUM_GEBUESCH.shx",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_EINZELBAUM_GEBUESCH.prj",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_EINZELBAUM_GEBUESCH.dbf",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_OEV/swissTLM3D_TLM_EISENBAHN.shp",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_OEV/swissTLM3D_TLM_EISENBAHN.shx",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_OEV/swissTLM3D_TLM_EISENBAHN.prj",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_OEV/swissTLM3D_TLM_EISENBAHN.dbf",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/MISSING_LAKES/Brienzersee.wkt",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/MISSING_LAKES/Vierwaldstätter See.wkt",
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_BODENBEDECKUNG.shp",  # Rivers shape
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_BODENBEDECKUNG.shx",  # Rivers shape
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_BODENBEDECKUNG.prj",  # Rivers shape
    "2021_SWISSTLM3D_SHP_CHLV95_LN02/TLM_BB/swissTLM3D_TLM_BODENBEDECKUNG.dbf",  # Rivers shape
]
SWISSTOPO_MISSING_TILES_BUILDINGS = {
    1033: [31],
    1034: [31, 44],
    1047: [24],
    1049: [24],
    1055: [11, 12, 14, 23, 32, 41, 43, 44],
    1065: [42],
    1084: [34],
    1096: [21, 23, 32],
    1136: [14],
    1143: [32],
    1153: [43],
    1157: [13, 43],
    1162: [22, 32],
    1164: [23],
    1177: [23],
    1178: [42, 44],
    1179: [13, 24, 33, 41],
    1182: [32],
    1184: [11],
    1192: [42],
    1193: [13, 34, 43],
    1198: [12, 14],
    1201: [42],
    1202: [13],
    1211: [21],
    1217: [42],
    1218: [31],
    1219: [24, 32, 42, 44],
    1229: [24, 42, 44],
    1230: [22, 31, 33, 34],
    1231: [13],
    1236: [44],
    1238: [12, 21, 23, 24],
    1239: [31, 32, 34, 43],
    1240: [42],
    1242: [44],
    1243: [33, 34],
    1248: [34, 41, 44],
    1249: [14, 21, 23, 31, 32, 42, 43, 44],
    1250: [11, 31],
    1253: [24, 42],
    1254: [13],
    1255: [14, 31, 34, 43],
    1256: [24],
    1257: [22],
    1258: [32],
    1260: [42],
    1261: [44],
    1262: [13, 14, 21, 22, 23, 31],
    1263: [11, 12, 21, 22, 24],
    1264: [13, 14],
    1267: [24],
    1268: [12, 24, 43],
    1269: [11, 12, 21],
    1270: [22, 23, 24],
    1271: [11, 14],
    1274: [22],
    1275: [21, 23, 33, 41, 42],
    1276: [31, 44],
    1277: [24, 33, 41, 42],
    1278: [22, 24],
    1280: [42],
    1281: [21],
    1286: [12],
    1289: [44],
    1290: [12, 14, 31],
    1291: [13, 31],
    1295: [11, 13],
    1296: [13, 23, 24],
    1298: [22],
    1303: [44],
    1309: [22, 34],
    1310: [31, 33],
    1314: [22],
    1318: [12],
    1324: [11, 14, 34],
    1327: [41, 42],
    1328: [11, 21],
    1329: [22, 23, 24, 32],
    1344: [21, 24, 42],
    1346: [21, 24, 31, 32, 34, 42],
    1347: [12, 31, 33],
    1348: [22, 32, 34, 43],
    1349: [12, 13, 14],
    1365: [11, 13, 32, 42],
    1366: [12, 13, 21, 22, 23],
    1368: [11, 12, 21, 22],
}


DEFAULT_GRID_RESOLUTION = 0.25  # simulation grid resolution in meters.
DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW = 1.0  # default resolution potential view
DEFAULT_GRID_BUFFER = 0.1  # minimum distance to walls for hexagons in meters
DEFAULT_SUN_OBS_FREQ_IN_HOURS_POTENTIAL_VIEW = 2
DEFAULT_SUN_OBS_DATES = {
    "march": datetime(2018, 3, 21),
    "june": datetime(2018, 6, 21),
    "december": datetime(2018, 12, 21),
}

DEFAULT_SUN_V2_OBSERVATION_HEIGHT = 0.1  # meters

DEFAULT_SUN_TIMES = datetimes = [
    datetime(2018, 3, 21, 7, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 6, 21, 7, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 12, 21, 7, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 3, 21, 12, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 6, 21, 12, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 12, 21, 12, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 3, 21, 17, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 6, 21, 17, 0, 0, 0, tzinfo=timezone.utc),
    datetime(2018, 12, 21, 17, 0, 0, 0, tzinfo=timezone.utc),
]
DEFAULT_OBSERVATION_HEIGHT = 1.55  # meters
DEFAULT_WRAPPER_RESOLUTION = 128  # pixels

PDF_TO_IMAGE_RESOLUTION = 300

SQUASHED_MIGRATION = 293

IMMO_RESPONSE_PRECISION = 5


@dataclass
class PipelineCompletedCriteria:
    labelled: bool = False
    classified: bool = False
    splitted: bool = False
    units_linked: bool = False
    georeferenced: bool = False

    @property
    def ok(self):
        for field_name in self.__annotations__.keys():
            if getattr(self, field_name) is False:
                return False
        return True


RASTER_NODATA_VALUE = -9999.0


class QA_VALIDATION_CODES(Enum):
    INDEX_NO_AREA = "The client's index doesn't provide net areas"
    DB_NO_AREA = "The processed unit does not have area"

    HNF_AREA_MISMATCH = "HNF mismatch."
    NET_AREA_MISMATCH = "Net area mismatch."

    INDEX_NO_ROOMS = "The client's index doesn't provide number of rooms"
    DB_NO_ROOMS = "The processed unit does not have rooms"
    ROOMS_MISMATCH = "Rooms mismatch."

    MISSING_KITCHEN = "Kitchen missing"
    MISSING_BATHROOM = "Bathrooms missing"

    UNIT_NOT_SIMULATED = "Does not have simulation results in the DB."

    # Client ids are missing from the DB
    CLIENT_IDS_MISSING = (
        "The following client unit ids of this site's Index are not linked"
    )

    # Client ids not expected according to client's index
    CLIENT_IDS_UNEXPECTED = (
        "The following client unit ids you assigned are not part of this site's"
    )

    MISSING_SITE_IN_INDEX = "Site doesn't have an entry in the client's index"

    BUILDING_WO_PLANS = "Site contains a building without plans"
    PLAN_WO_FLOORS = "Site contains a plan without floors"
    SITE_WO_BUILDINGS = "Site contains no buildings"
    ANNOTATIONS_ERROR = "Site contains a plan with errors in annotations"
    GEOREFERENCE_ERROR = "Plans are not correctly georeferenced"
    CLASSIFICATION_ERROR = "Plan incorrectly classified"
    LINKING_ERROR = "Units containing area types not allowed for unit usage type"
    ROOM_ERROR = "Plan contains a room without a window"
    ANF_MISMATCH = "ANF mismatch."


NET_AREA_DIFFERENCE_THRESHOLD = 0.03
ANF_DIFFERENCE_THRESHOLD = NET_AREA_DIFFERENCE_THRESHOLD
MIN_NET_AREA_DIFFERENCE_SQ_M_THRESHOLD = 3
ANF_DIFFERENCE_SQ_M_THRESHOLD = 1
ROOM_NUMBER_THRESHOLD = 0.0
DB_INDEX_ROOM_NUMBER = "UnitBasics.number-of-rooms"
DB_INDEX_HNF = "UnitBasics.area-sia416-HNF"
DB_INDEX_NNF = "UnitBasics.area-sia416-NNF"
DB_INDEX_ANF = "UnitBasics.area-sia416-ANF"
DB_INDEX_VF = "UnitBasics.area-sia416-VF"
DB_INDEX_FF = "UnitBasics.area-sia416-FF"
DB_INDEX_NET_AREA = "UnitBasics.net-area"

SIA_DIMENSION_PREFIX = "area-sia416-"


# Wall Postprocessing
WALL_SEGMENT_MINIMUM_SIZE = 0.01
MAXIMUM_ITERATIONS = 100000


class UNIT_USAGE(Enum):
    RESIDENTIAL = "RESIDENTIAL"
    COMMERCIAL = "COMMERCIAL"
    JANITOR = "JANITOR"
    PLACEHOLDER = "PLACEHOLDER"
    PUBLIC = "PUBLIC"


class POTENTIAL_SIMULATION_STATUS(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class TASK_TYPE(Enum):
    BIGGEST_RECTANGLE = "BIGGEST_RECTANGLE"
    VIEW_SUN = "VIEW_SUN"
    BASIC_FEATURES = "BASIC_FEATURES"
    CONNECTIVITY = "CONNECTIVITY"
    SUN_V2 = "SUN_V2"
    NOISE = "NOISE"
    NOISE_WINDOWS = "NOISE_WINDOWS"
    COMPETITION = "COMPETITION"


class ADMIN_SIM_STATUS(Enum):
    UNPROCESSED = "UNPROCESSED"  # It has never been in the queue nor processed.
    # POTENTIAL_SIMULATION_STATUS + UNPROCESSED
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


TASK_READY_STATES = frozenset(
    {
        ADMIN_SIM_STATUS.UNPROCESSED.value,
        ADMIN_SIM_STATUS.SUCCESS.value,
        ADMIN_SIM_STATUS.FAILURE.value,
    }
)
TASK_UNREADY_STATE = frozenset(
    {ADMIN_SIM_STATUS.PROCESSING.value, ADMIN_SIM_STATUS.PENDING.value}
)


class SIMULATION_TYPE(Enum):
    SUN = "sun"
    VIEW = "view"


class SIMULATION_VERSION(AutoNameEnum):
    PH_2020 = auto()
    PH_01_2021 = auto()
    PH_2022_H1 = auto()
    EXPERIMENTAL = auto()


class POTENTIAL_LAYOUT_MODE(AutoNameEnum):
    WITH_WINDOWS = auto()


class USER_ROLE(Enum):
    ADMIN = "ADMIN"
    POTENTIAL_API = "POTENTIAL_API"
    DMS_LIMITED = "DMS_LIMITED"
    COMPETITION_ADMIN = "COMPETITION_ADMIN"
    COMPETITION_VIEWER = "COMPETITION_VIEWER"
    TEAMMEMBER = "TEAMMEMBER"
    TEAMLEADER = "TEAMLEADER"
    ARCHILYSE_ONE_ADMIN = "ARCHILYSE_ONE_ADMIN"


class DMS_PERMISSION(Enum):
    READ = "READ"
    WRITE = "WRITE"
    READ_ALL = "READ_ALL"
    WRITE_ALL = "WRITE_ALL"


DMS_FOLDER_NAME = "dms"
DMS_FILE_RETENTION_PERIOD = timedelta(days=30)

# User name for the nightly potential api task triggered with celery beat
POTENTIAL_API_NIGHTLY_USER_NAME = "nightly-simulations-archilyse"


class SUN_DAYTIMES(Enum):
    MORNING = 0
    MIDDAY = 12
    EVENING = 18


class SIMULATION_VALUE_TYPE(Enum):
    MIN = "min"
    MAX = "max"
    MEAN = "mean"
    STD = "std"


class SUPPORTED_LANGUAGES(Enum):
    DE = auto()
    EN = auto()
    FR = auto()
    IT = auto()


class SUPPORTED_OUTPUT_FILES(Enum):
    PNG = auto()
    DXF = auto()
    PDF = auto()
    IFC = auto()
    DWG = auto()


def get_slam_version():
    return os.environ.get("SLAM_VERSION")


def get_slam_secret_key():
    return os.environ["SLAM_API_SECRET_KEY"]


def get_security_password_salt():
    return os.environ["SECURITY_PASSWORD_SALT"]


PASSWORD_RESET_TOKEN_EXPIRATION_TIME = 86400


def get_sendgrid_email_default_sender():
    return os.environ["SENDGRID_MAIL_DEFAULT_SENDER"]


PRODUCTION_URL = os.environ.get("PRODUCTION_URL", "https://app.archilyse.com")


class SURROUNDING_SOURCES(Enum):
    SWISSTOPO = "SWISSTOPO"
    OSM = "OSM"


class REGION(Enum):
    LAT_LON = "LAT_LON"
    EUROPE = "EUROPE"

    MC = "MONACO"
    CH = "SWITZERLAND"
    DK = "DENMARK"
    AT = "AUSTRIA"
    NO = "NORWAY"
    CZ = "CZECH_REPUBLIC"
    ES = "SPAIN"
    AD = "ANDORRA"
    # ****************** GERMANY **************************
    DE_BADEN_WURTTEMBERG = "GERMANY_BADEN_WURTTEMBERG"
    DE_BAYERN = "GERMANY_BAYERN"
    DE_BERLIN = "GERMANY_BERLIN"
    DE_BRANDENBURG = "GERMANY_BRANDENBURG"
    DE_BREMEN = "GERMANY_BREMEN"
    DE_HAMBURG = "GERMANY_HAMBURG"
    DE_HESSEN = "GERMANY_HESSEN"
    DE_MECKLENBURG_VORPOMMERN = "GERMANY_MECKLENBURG_VORPOMMERN"
    DE_NIEDERSACHSEN = "GERMANY_NIEDERSACHSEN"
    DE_NORDRHEIN_WESTFALEN = "GERMANY_NORDRHEIN_WESTFALEN"
    DE_RHEINLAND_PFALZ = "GERMANY_RHEINLAND_PFALZ"
    DE_SAARLAND = "GERMANY_SAARLAND"
    DE_SACHSEN = "GERMANY_SACHSEN"
    DE_SACHSEN_ANHALT = "GERMANY_SACHSEN_ANHALT"
    DE_SCHLESWIG_HOLSTEIN = "GERMANY_SCHLESWIG_HOLSTEIN"
    DE_THURINGEN = "GERMANY_THURINGEN"
    # ****************** UNITED STATES **************************
    US_GEORGIA = "UNITED_STATES_GEORGIA"
    US_PENNSYLVANIA = "UNITED_STATES_PENNSYLVANIA"
    # ****************** ASIA ***********************************
    SG = "SINGAPORE"


class SurroundingType(Enum):
    RIVERS = 1
    LAKES = 2
    STREETS = 3
    PARKS = 4
    RAILROADS = 5
    TREES = 6
    BUILDINGS = 7
    GROUNDS = 8
    MOUNTAINS = 9
    SEA = 10
    FOREST = 11
    MOUNTAINS_CLASS_1 = "mountains_class_1"
    MOUNTAINS_CLASS_2 = "mountains_class_2"
    MOUNTAINS_CLASS_3 = "mountains_class_3"
    MOUNTAINS_CLASS_4 = "mountains_class_4"
    MOUNTAINS_CLASS_5 = "mountains_class_5"
    MOUNTAINS_CLASS_6 = "mountains_class_6"
    PEDESTRIAN = 12
    HIGHWAY = 13
    TERTIARY_STREET = 14
    SECONDARY_STREET = 15
    PRIMARY_STREET = 16


# To be deprecated
SurroundingTypeToViewDimension = {
    SurroundingType.BUILDINGS.name: VIEW_DIMENSION.VIEW_BUILDINGS.value,
    SurroundingType.LAKES.name: VIEW_DIMENSION.VIEW_WATER.value,
    SurroundingType.STREETS.name: VIEW_DIMENSION.VIEW_STREETS.value,
    SurroundingType.PARKS.name: VIEW_DIMENSION.VIEW_GREENERY.value,
    SurroundingType.RAILROADS.name: VIEW_DIMENSION.VIEW_RAILWAY_TRACKS.value,
    SurroundingType.TREES.name: VIEW_DIMENSION.VIEW_GREENERY.value,
    SurroundingType.RIVERS.name: VIEW_DIMENSION.VIEW_WATER.value,
    SurroundingType.GROUNDS.name: VIEW_DIMENSION.VIEW_GROUND.value,
    SurroundingType.SEA.name: VIEW_DIMENSION.VIEW_WATER.value,
    SurroundingType.FOREST.name: VIEW_DIMENSION.VIEW_GREENERY.value,
    SurroundingType.MOUNTAINS.name: VIEW_DIMENSION.VIEW_MOUNTAINS.value,
    "site": VIEW_DIMENSION.VIEW_SITE.value,
}
SurroundingTypeToView2Dimension = {
    SurroundingType.BUILDINGS.name: VIEW_DIMENSION.VIEW_BUILDINGS.value,
    SurroundingType.LAKES.name: VIEW_DIMENSION.VIEW_WATER.value,
    SurroundingType.PARKS.name: VIEW_DIMENSION.VIEW_GREENERY.value,
    SurroundingType.RAILROADS.name: VIEW_DIMENSION.VIEW_RAILWAY_TRACKS.value,
    SurroundingType.TREES.name: VIEW_DIMENSION.VIEW_GREENERY.value,
    SurroundingType.RIVERS.name: VIEW_DIMENSION.VIEW_WATER.value,
    SurroundingType.GROUNDS.name: VIEW_DIMENSION.VIEW_GROUND.value,
    SurroundingType.SEA.name: VIEW_DIMENSION.VIEW_WATER.value,
    SurroundingType.FOREST.name: VIEW_DIMENSION.VIEW_GREENERY.value,
    "site": VIEW_DIMENSION.VIEW_SITE.value,
    #  New ones
    SurroundingType.MOUNTAINS_CLASS_1.name: VIEW_DIMENSION_2.MOUNTAINS_CLASS_1.value,
    SurroundingType.MOUNTAINS_CLASS_2.name: VIEW_DIMENSION_2.MOUNTAINS_CLASS_2.value,
    SurroundingType.MOUNTAINS_CLASS_3.name: VIEW_DIMENSION_2.MOUNTAINS_CLASS_3.value,
    SurroundingType.MOUNTAINS_CLASS_4.name: VIEW_DIMENSION_2.MOUNTAINS_CLASS_4.value,
    SurroundingType.MOUNTAINS_CLASS_5.name: VIEW_DIMENSION_2.MOUNTAINS_CLASS_5.value,
    SurroundingType.MOUNTAINS_CLASS_6.name: VIEW_DIMENSION_2.MOUNTAINS_CLASS_6.value,
    SurroundingType.PEDESTRIAN.name: VIEW_DIMENSION_2.VIEW_PEDESTRIAN.value,
    SurroundingType.HIGHWAY.name: VIEW_DIMENSION_2.VIEW_HIGHWAYS.value,
    SurroundingType.PRIMARY_STREET.name: VIEW_DIMENSION_2.VIEW_PRIMARY_STREETS.value,
    SurroundingType.SECONDARY_STREET.name: VIEW_DIMENSION_2.VIEW_SECONDARY_STREETS.value,
    SurroundingType.TERTIARY_STREET.name: VIEW_DIMENSION_2.VIEW_TERTIARY_STREETS.value,
}


# Additional mimetypes recognized by our platform
mimetypes.add_type(type=mimetypes.types_map[".txt"], ext=".ifc")
DXF_MIME_TYPE = "image/vnd.dxf"
DWG_MIME_TYPE = "image/vnd.dwg"
mimetypes.add_type(type=DXF_MIME_TYPE, ext=".dxf")
mimetypes.add_type(type=DWG_MIME_TYPE, ext=".dwg")
BUFFERING_1CM = 0.01


class CURRENCY(Enum):
    CHF = "CHF"
    EUR = "EUR"
    CZK = "CZK"
    USD = "USD"


CURRENCY_REGION = {
    REGION.CH: CURRENCY.CHF,
    REGION.DE_HAMBURG: CURRENCY.EUR,
    REGION.CZ: CURRENCY.CZK,
    REGION.US_GEORGIA: CURRENCY.USD,
}


COUNTRY_CODE = {REGION.CH: "CH"}


class ManualSurroundingTypes(Enum):
    BUILDINGS = 1
    EXCLUSION_AREA = 2


# DXF Import

DXF_IMPORT_DEFAULT_SCALE_FACTOR = (2 / 100) ** 2  # 1px per 2cm
IS_RECTANGLE_THRESHOLD_IN_CM2 = 1  # Threshold for using the minimum rotated rectangle of a polygon instead of the original geometry
SKELETONIZE_TIMEOUT_IN_SECS = 1


FIXED_SUN_DIMENSIONS = {
    "sun-2018-03-21 08:00:00+01:00",
    "sun-2018-03-21 10:00:00+01:00",
    "sun-2018-03-21 12:00:00+01:00",
    "sun-2018-03-21 14:00:00+01:00",
    "sun-2018-03-21 16:00:00+01:00",
    "sun-2018-03-21 18:00:00+01:00",
    "sun-2018-06-21 06:00:00+02:00",
    "sun-2018-06-21 08:00:00+02:00",
    "sun-2018-06-21 10:00:00+02:00",
    "sun-2018-06-21 12:00:00+02:00",
    "sun-2018-06-21 14:00:00+02:00",
    "sun-2018-06-21 16:00:00+02:00",
    "sun-2018-06-21 18:00:00+02:00",
    "sun-2018-06-21 20:00:00+02:00",
    "sun-2018-12-21 10:00:00+01:00",
    "sun-2018-12-21 12:00:00+01:00",
    "sun-2018-12-21 14:00:00+01:00",
    "sun-2018-12-21 16:00:00+01:00",
}

N_DIGITS_ROUNDING_VERTICES = 4  # For vertices in meters

AREA_BUFFER_FOR_WALLS_INTERSECTION_IN_M = 0.01
AREA_BUFFER_TO_INCLUDE_WALLS_IN_M = 0.3
