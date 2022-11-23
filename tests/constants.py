import os
from collections import OrderedDict
from pathlib import Path

from shapely.geometry import Point

from common_utils.constants import POTENTIAL_API_NIGHTLY_USER_NAME, USER_ROLE

TEST_CLIENT_NAME = "test_archilyse_client"

TIME_TO_WAIT = 10
PERCY_TIME_TO_WAIT = 5

UNIT_ID_1 = 100
CLIENT_ID_1 = "GS20.00.01"
UNIT_ID_2 = 200
CLIENT_ID_2 = "GS20.00.02"
UNIT_ID_3 = 300
CLIENT_ID_3 = "GS20.01.02"
UNIT_ID_4 = 301
CLIENT_ID_4 = "GS20.01.02"
CLIENT_ID_5 = "GS20.00.03"


USERS = {
    "ADMIN": {
        "login": "admin",
        "password": "admin",
        "roles": [USER_ROLE.ADMIN],
        "group": "Archilyse",
        "email": "admin@fake.com",
    },
    "POTENTIAL_API": {
        "login": "potential",
        "password": "potential",
        "roles": [USER_ROLE.POTENTIAL_API],
        "email": "potential@fake.com",
    },
    "POTENTIAL_NIGHTLY": {
        "name": POTENTIAL_API_NIGHTLY_USER_NAME,
        "login": "potential_nightly",
        "password": "potential",
        "roles": [USER_ROLE.POTENTIAL_API],
        "email": "potential_nightly@fake.com",
    },
    "TEAMMEMBER": {
        "login": "teammember",
        "password": "teammember",
        "roles": [USER_ROLE.TEAMMEMBER],
        "group": "OECC",
        "email": "teammember@fake.com",
    },
    "ARCHILYSE_ONE_ADMIN": {
        "login": "dms_amigo",
        "password": "dms_amigo",
        "roles": [USER_ROLE.ARCHILYSE_ONE_ADMIN],
        "group": "Archilyse",
        "email": "dms_amigo@fake.com",
    },
    "DMS_LIMITED": {
        "login": "dms_limited",
        "password": "dms_limited",
        "roles": [USER_ROLE.DMS_LIMITED],
        "group": "Archilyse",
        "email": "dms_limited@fake.com",
    },
    "DMS_LIMITED_2": {
        "login": "dms_limited_2",
        "password": "dms_limited_2",
        "roles": [USER_ROLE.DMS_LIMITED],
        "group": "Archilyse",
        "email": "dms_limited_2@fake.com",
    },
    "COMPETITION_ADMIN": {
        "login": "competition_admin",
        "password": "competition_admin",
        "roles": [USER_ROLE.COMPETITION_ADMIN],
        "group": "Archilyse",
        "email": "competition_admin@fake.com",
    },
    "COMPETITION_VIEWER": {
        "login": "competition_viewer",
        "password": "competition_viewer",
        "roles": [USER_ROLE.COMPETITION_VIEWER],
        "group": "Archilyse",
        "email": "competition_viewer@fake.com",
    },
    "TEAMLEADER": {
        "login": "teamleader",
        "password": "teamleader",
        "roles": [USER_ROLE.TEAMLEADER, USER_ROLE.TEAMMEMBER],
        "group": "UpWork",
        "email": "teamleader@fake.com",
    },
}


ELEVATION_BY_POINT = {(2623240, 1193070): 948.371, (2623246, 1193078): 948.476}

INTEGRATION_IMAGE_DIFF_DIR = Path().cwd().joinpath("tests/image_differences/")

SLAM_AUTH_COOKIE_NAME = "slam-auth"

FLAKY_RERUNS = 3

GECKODRIVER_LOG_FILE = "/tmp/geckodriver.log"
SPLINTER_SCREENSHOTS_DIRECTORY = Path().cwd().joinpath("tests/splinter_images/")
BROWSER_NAME = os.environ.get("BROWSER_NAME", "chrome")

NON_DEFAULT_ISOLATION_LEVEL = "READ COMMITTED"
SUN_ENTITY = {
    "geometry": {"type": "Point", "coordinates": (0.0, 0.0, 0.0)},
    "properties": OrderedDict(
        {
            "footprint_id": Point(0.5, 0.5).wkt,
            "level": 0,
            "201803210800": 0.0,
            "201803211000": 0.0,
            "201803211200": 0.0,
            "201803211400": 0.0,
            "201803211600": 0.0,
            "201803211800": 0.0,
            "201806210600": 0.0,
            "201806210800": 0.0,
            "201806211000": 0.0,
            "201806211200": 0.0,
            "201806211400": 0.0,
            "201806211600": 0.0,
            "201806211800": 0.0,
            "201806212000": 0.0,
            "201812211000": 0.0,
            "201812211200": 0.0,
            "201812211400": 0.0,
            "201812211600": 0.0,
        }
    ),
}
VIEW_ENTITY = {
    "geometry": {"type": "Point", "coordinates": (0.0, 0.0, 0.0)},
    "properties": OrderedDict(
        {
            "footprint_id": Point(0.5, 0.5).wkt,
            "level": 0,
            "ground": 0.0,
            "greenery": 0.0,
            "buildings": 0.0,
            "sky": 0.0,
            "site": 0.0,
            "water": 0.0,
            "isovist": 0.0,
            "railway_tracks": 0.0,
            "highways": 0.0,
            "pedestrians": 0.0,
            "primary_streets": 0.0,
            "secondary_streets": 0.0,
            "tertiary_streets": 0.0,
            "mountains_class_1": 0.0,
            "mountains_class_2": 0.0,
            "mountains_class_3": 0.0,
            "mountains_class_4": 0.0,
            "mountains_class_5": 0.0,
            "mountains_class_6": 0.0,
        }
    ),
}

TEST_SKELETONIZE_TIMEOUT_IN_SECS = 15
