import os
import random
import string
from io import BytesIO
from itertools import chain

import numpy as np
import pytest
from PIL import Image
from shapely import wkb
from shapely.geometry import MultiPolygon, Point, Polygon

from common_utils.competition_constants import (
    CATEGORIES,
    FAKE_FEATURE_VALUES,
    CompetitionFeatures,
)
from common_utils.constants import (
    FIXED_SUN_DIMENSIONS,
    VIEW_DIMENSION_2,
    ManualSurroundingTypes,
)
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerDoorSweepingPoints,
    ReactPlannerGeomProperty,
    ReactPlannerHole,
    ReactPlannerHoleHeights,
    ReactPlannerHoleProperties,
    ReactPlannerLayer,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerType,
    ReactPlannerVertex,
)
from tests.e2e_utils import SlamUIClient


@pytest.fixture
def random_media_link():
    """Image that will help loading an image running the pipeline UI locally. To avoid CSRF problem use a static
    file serve through the API like http://localhost/public-admin-assets/logo.png"""
    return "http://localhost/public-admin-assets/logo.png"


@pytest.fixture
def random_plain_floorplan_link():
    """A large image defined in the URL, means there's no need of server and it's 1024x1024px."""
    return "data:image/svg+xml;charset=UTF-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%221024px%22%20height%3D%221024px%22%20viewBox%3D%220%200%201024px%201024px%22%3E%20%3Crect%20fill%3D%22white%22%20width%3D%221024px%22%20height%3D%221024px%22%2F%3E%20%3C%2Fsvg%3E"


@pytest.fixture
def site_coordinates():
    """This coordinates works to retrieve a small building shp file for testing"""
    return {"lat": 46.9022094312901, "lon": 9.2246596978254}


@pytest.fixture
def site_coordinates_outside_switzerland():
    return {"lon": 46.9022094312901, "lat": 9.2246596978254}


@pytest.fixture
def random_text():
    def f(stringLength=15):
        """Generate a random string of fixed length"""
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(stringLength))

    return f


@pytest.fixture
def random_image():
    def f():
        """Generate a random image"""
        a = np.random.rand(30, 30, 3) * 255
        im = Image.fromarray(a.astype("uint8")).convert("RGBA")
        with BytesIO() as f:
            im.save(f, format="png")
            f.seek(0)
            content = f.read()
        return content

    return f


@pytest.fixture(scope="session")
def background_floorplan_image(fixtures_path) -> bytes:
    with fixtures_path.joinpath("images/GS20-00-01-floorplan.png").open("rb") as f:
        return f.read()


@pytest.fixture
def zurich_location():
    return dict(lat=47.35367555812237, lon=8.402599639348733, floor_number=2)


@pytest.fixture
def prague_location():
    return dict(lat=50.06109932602108, lon=14.344355947930506, floor_number=2)


@pytest.fixture
def quavis_input():
    return {
        "quavis": {
            "header": {"name": "a1ca370d-6837-4e1f-a5c2-73fff62cb344"},
            "sceneObjects": "sceneObjects",
            "observationPoints": "observationPoints",
            "rendering": {"renderWidth": 128, "renderHeight": 128},
            "computeStages": [
                {"type": "volume", "name": "volume"},
                {"type": "groups", "name": "groups", "max_groups": 512},
                {"type": "sun", "name": "sun"},
            ],
            "output": {
                "filename": "/tmp/a1ca370d-6837-4e1f-a5c2-73fff62cb344.out.json",
                "imagesType": "png",
                "imageNaming": "{0:0>4}_{1}.png",
            },
        }
    }


@pytest.fixture
def qa_rows():
    from handlers.db.qa_handler import QA_COLUMN_HEADERS

    return {
        "2273211.01.01.0001": dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{"net_area": "94", "number_of_rooms": "4.5"},
        ),
        "2273211.01.01.0002": dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{"net_area": "90", "number_of_rooms": "3.5"},
        ),
    }


@pytest.fixture
def area_polygon_wkt() -> str:
    return """POLYGON ((550 -500, 550 -200, 650 -200, 650 -500, 550 -500))"""


@pytest.fixture
def non_convex_polygon_2d():
    from shapely.geometry import shape

    polygon_mapped = {
        "type": "Polygon",
        "coordinates": (
            (
                (2674471.5560000017, 1209098.164999999),
                (2674468.840999998, 1209098.5469999984),
                (2674466.601, 1209098.8630000018),
                (2674463.886, 1209099.245000001),
                (2674465.039999999, 1209107.4409999996),
                (2674465.4804697987, 1209107.8019405296),
                (2674465.6110000014, 1209107.9090000018),
                (2674465.610984572, 1209107.9088901354),
                (2674466.408, 1209108.561999999),
                (2674467.664999999, 1209109.5920000002),
                (2674468.6068662545, 1209110.3638903906),
                (2674468.833672399, 1209111.974473013),
                (2674468.6380000003, 1209112.2569999993),
                (2674467.217, 1209114.307),
                (2674466.631006569, 1209115.1530462387),
                (2674466.631000001, 1209115.1530000009),
                (2674466.625036614, 1209115.1616655476),
                (2674466.212000001, 1209115.7580000013),
                (2674466.631000001, 1209118.732999999),
                (2674469.346000001, 1209118.3500000015),
                (2674471.585000001, 1209118.0340000018),
                (2674474.300999999, 1209117.6510000005),
                (2674471.5560000017, 1209098.164999999),
            ),
            (
                (2674466.631000001, 1209115.1530000009),
                (2674466.631006553, 1209115.1530462627),
                (2674466.631006553, 1209115.153046263),
                (2674466.631000001, 1209115.1530000009),
            ),
            (
                (2674464.991747702, 1209099.5099642475),
                (2674465.2124307663, 1209099.5628453176),
                (2674465.212430766, 1209099.5628453176),
                (2674464.991747702, 1209099.5099642475),
            ),
            (
                (2674468.6785385776, 1209105.5022958736),
                (2674468.6787932245, 1209105.5015926848),
                (2674468.6785385776, 1209105.502295874),
                (2674468.6785385776, 1209105.5022958736),
            ),
        ),
    }
    return shape(polygon_mapped)


@pytest.fixture
def non_convex_polygon_3d(non_convex_polygon_2d):
    from dufresne import from2dto3d

    return from2dto3d(non_convex_polygon_2d, z_coordinate=42)


@pytest.fixture
def polygon_with_holes():
    from shapely.geometry import shape

    polygon_mapped = {
        "type": "Polygon",
        "coordinates": (
            ((0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0), (0.0, 0.0)),
            ((1.0, 0.1), (1.5, 0.5), (1.0, 1.0), (0.5, 0.5), (1.0, 0.1)),
        ),
    }

    return shape(polygon_mapped)


@pytest.fixture
def polygon_with_tiny_holes():
    from math import sqrt

    from shapely.geometry import shape

    desired_hole_size = 0.9e-4
    hole_triangle_side = sqrt(4 * desired_hole_size / sqrt(3))
    hole_triangle_height = 0.5 * hole_triangle_side * sqrt(3)

    polygon_mapped = {
        "type": "Polygon",
        "coordinates": (
            ((0.0, 0.0), (0.0, 2.0), (2.0, 2.0), (2.0, 0.0), (0.0, 0.0)),
            (
                (1.0, 1.0),
                (1.0 + hole_triangle_side, 1.0),
                (1.0 + hole_triangle_side / 2, 1.0 + hole_triangle_height),
                (1.0, 1.0),
            ),
        ),
    }

    return shape(polygon_mapped)


@pytest.fixture
def expected_competition_features_site_1():
    return {
        CompetitionFeatures.RESIDENTIAL_USE.value: {"RESIDENTIAL": 584.1925137564431},
        CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: {
            "RESIDENTIAL": 584.1925137564431
        },
        CompetitionFeatures.RESIDENTIAL_TOTAL_HNF_REQ.value: 430.5283699974727,
        CompetitionFeatures.APT_PCT_W_OUTDOOR.value: 0.4285714285,
        CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: {
            "0.0": [0, 0],
            "1.0": [28.424774677401153],
            "3.0": [29.3280243514939],
            "4.5": [41.774937995215865, 29.430487304800806, 40.139564277662856],
        },
        CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: {
            "competition_5797_0": 7.686476686207385,
            "competition_5797_1": 0,
            "competition_5797_2": 0,
            "competition_5797_3": 9.116478433110727,
            "competition_5825_0": 0,
            "competition_5825_1": 0,
            "competition_5825_2": 3.106179672929113,
        },
        CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: {
            "competition_5797_0": [],
            "competition_5797_1": [],
            "competition_5797_2": [],
            "competition_5797_3": [],
            "competition_5825_0": [[10.93955625, 3.3075, 3.3075]],
            "competition_5825_1": [[10.93955625, 3.3075, 3.3075]],
            "competition_5825_2": [[10.93955625, 3.3075, 3.3075]],
        },
        CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: [
            ["3.0", 65.51325603721432],
            ["1.0", 35.84088572520211],
            ["0.0", 3.4390887649764994],
            ["0.0", 0.0],
            ["4.5", 102.7598447485137],
            ["4.5", 80.59080347612401],
            ["4.5", 107.98456598622387],
        ],
        CompetitionFeatures.APT_HAS_WASHING_MACHINE.value: 0.0,
        CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER.value: 200.0,
        CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.value: 200.0,
        CompetitionFeatures.BUILDING_AVG_MAX_RECT_ALL_APT_AREAS.value: 10.543879998480646,
        CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 0.04236378,
        CompetitionFeatures.APT_MAX_RECT_IN_PRIVATE_OUTDOOR.value: 7.720738117868126,
        CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value: 0.2857142857142857,
        CompetitionFeatures.APT_PCT_W_STORAGE.value: {
            "competition_5797_0": 0.0,
            "competition_5797_1": 1.0787536451712025,
            "competition_5797_2": 20.287883641005386,
            "competition_5797_3": 0.0,
            "competition_5825_0": 0.0,
            "competition_5825_1": 1.6710197759991179,
            "competition_5825_2": 0.0,
        },
        CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: {
            "competition_5797_0": [[10.93955625, 3.3075, 3.3075]],
            "competition_5797_1": [[10.93955625, 3.3075, 3.3075]],
            "competition_5797_2": [],
            "competition_5797_3": [],
            "competition_5825_0": [
                [10.93955625, 3.3075, 3.3075],
                [10.93955625, 3.3075, 3.3075],
            ],
            "competition_5825_1": [
                [10.93955625, 3.3075, 3.3075],
                [2.2628392799988046, 1.750503220505001, 1.2926793012960012],
            ],
            "competition_5825_2": [
                [2.5695914243969344, 1.9928805894980002, 1.2926793012960012],
                [10.93955625, 3.3075, 3.3075],
            ],
        },
        CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: {
            "competition_5797_0": [
                [10.93955625, 3.3075, 3.3075],
                [14.90640496768604, 4.266032339073718, 3.494208150077611],
            ],
            "competition_5797_1": [],
            "competition_5797_2": [],
            "competition_5797_3": [],
            "competition_5825_0": [
                [10.93955625, 3.3075, 3.3075],
                [10.93955625, 3.3075, 3.3075],
                [12.291188829569736, 4.324258666248128, 2.8443788842781994],
            ],
            "competition_5825_1": [
                [13.950611455853254, 4.468518570996821, 3.121976832859218],
                [11.644257029221533, 3.7952477030921727, 3.0681151640601456],
                [11.64242945293967, 4.414656901964918, 2.6372218071483076],
            ],
            "competition_5825_2": [
                [10.93955625, 3.3075, 3.3075],
                [16.0413740920703, 4.414656901964918, 3.633662694133818],
                [10.93955625, 3.3075, 3.3075],
            ],
        },
        CompetitionFeatures.BUILDING_BICYCLE_BOXES_AVAILABLE.value: False,
        CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: {
            "1.2": 0.923588262995427,
            "1.5": 0.7885385037963664,
        },
        CompetitionFeatures.BUILDING_PCT_CIRCULATION_RESIDENTIAL.value: 0.10290,
        CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: {
            "0.0": 0.2857142857142857,
            "1.0": 0.14285714285714285,
            "3.0": 0.14285714285714285,
            "4.5": 0.42857142857142855,
        },
        CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: {
            "0.0": [{"features": [], "percentage": 1.0}],
            "1.0": [
                {
                    "features": [{"BATHTUB": 0, "SHOWER": 0, "SINK": 0, "TOILET": 0}],
                    "percentage": 1.0,
                }
            ],
            "3.0": [
                {
                    "features": [{"BATHTUB": 0, "SHOWER": 0, "SINK": 0, "TOILET": 0}],
                    "percentage": 1.0,
                }
            ],
            "4.5": [
                {
                    "features": [
                        {"BATHTUB": 1, "SHOWER": 0, "SINK": 1, "TOILET": 1},
                        {"BATHTUB": 0, "SHOWER": 0, "SINK": 1, "TOILET": 1},
                    ],
                    "percentage": 0.3333333333333333,
                },
                {
                    "features": [
                        {"BATHTUB": 0, "SHOWER": 1, "SINK": 1, "TOILET": 1},
                        {"BATHTUB": 0, "SHOWER": 1, "SINK": 1, "TOILET": 1},
                    ],
                    "percentage": 0.3333333333333333,
                },
                {
                    "features": [
                        {"BATHTUB": 0, "SHOWER": 0, "SINK": 1, "TOILET": 1},
                        {"BATHTUB": 0, "SHOWER": 1, "SINK": 1, "TOILET": 0},
                    ],
                    "percentage": 0.3333333333333333,
                },
            ],
        },
        CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value: {
            "0.0": [[], []],
            "1.0": [[]],
            "3.0": [[]],
            "4.5": [
                ["TOILET", "BATHROOM"],
                ["TOILET", "BATHROOM"],
                ["BATHROOM", "BATHROOM"],
            ],
        },
        CompetitionFeatures.JANITOR_HAS_WC.value: False,
        CompetitionFeatures.JANITOR_HAS_STORAGE.value: False,
        CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value: None,
        CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value: None,
        CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: 0,
        CompetitionFeatures.JANITOR_WATER_CONN_AVAILABLE.value: False,
        CompetitionFeatures.JANITOR_WC_CLOSENESS.value: False,
        CompetitionFeatures.BUILDING_MINIMUM_ELEVATOR_DIMENSIONS.value: False,
        CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER.value: 6.0,
        CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER.value: 14.0,
        CompetitionFeatures.ANALYSIS_BUILDINGS.value: 3.0,
        CompetitionFeatures.ANALYSIS_GREENERY.value: 3.0,
        CompetitionFeatures.ANALYSIS_SKY.value: 3.0,
        CompetitionFeatures.ANALYSIS_WATER.value: 3.0,
        CompetitionFeatures.ANALYSIS_STREETS.value: 3.0,
        CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: 3.0,
        CompetitionFeatures.NOISE_STRUCTURAL.value: 41.3333333,
        CompetitionFeatures.NOISE_INSULATED_ROOMS.value: 0.0,
        CompetitionFeatures.AGF_W_REDUIT.value: 442.50403265722304,
    }


@pytest.fixture
def expected_competition_features_site_2(expected_competition_features_site_1):
    return {
        **expected_competition_features_site_1,
        **{
            CompetitionFeatures.ANALYSIS_BUILDINGS.value: 6.0,
            CompetitionFeatures.ANALYSIS_GREENERY.value: 6.0,
            CompetitionFeatures.ANALYSIS_SKY.value: 6.0,
            CompetitionFeatures.ANALYSIS_WATER.value: 6.0,
            CompetitionFeatures.ANALYSIS_STREETS.value: 6.0,
            CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: 6.0,
        },
    }


@pytest.fixture
def expected_competition_features_preprocessed_site_1(
    expected_competition_features_site_1,
):
    return {
        **expected_competition_features_site_1,
        CompetitionFeatures.RESIDENTIAL_USE.value: True,
        CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: 1.0,
        CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: 0.923588262995427,
        CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: 0.0,
        CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: 5 / 7,
        CompetitionFeatures.APT_PCT_W_STORAGE.value: 0.14285714285714285,
        CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: 0.42857142857142855,
        CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: 0.0,
        CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value: 1.0,
        CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value: False,
        CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value: False,
        CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: False,
        CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: 1.0,
        CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: 0.285714285,
        CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: 0.42857142857,
        CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: 1.0,
    }


@pytest.fixture
def expected_competition_features_preprocessed_site_2(
    expected_competition_features_site_2,
):
    return {
        **expected_competition_features_site_2,
        CompetitionFeatures.RESIDENTIAL_USE.value: True,
        CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: 1.0,
        CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: 5 / 7,
        CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: 0.923588262995427,
        CompetitionFeatures.APT_RATIO_BEDROOM_MIN_REQUIREMENT.value: 0.0,
        CompetitionFeatures.APT_PCT_W_STORAGE.value: 0.14285714285714285,
        CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: 0.42857142857142855,
        CompetitionFeatures.APT_SHOWER_BATHTUB_DISTRIBUTION.value: 0.0,
        CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value: 1.0,
        CompetitionFeatures.JANITOR_STORAGE_MIN_SIZE_REQUIREMENT.value: False,
        CompetitionFeatures.JANITOR_OFFICE_MIN_SIZE_REQUIREMENT.value: False,
        CompetitionFeatures.BUILDING_BICYCLE_BOXES_QUANTITY_PERFORMANCE.value: False,
        CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: 1.0,
        CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: 0.28571,
        CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: 0.42857142857,
        CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: 1.0,
    }


@pytest.fixture
def expected_competition_scores_site_1(site):
    expected = {
        "id": site["id"],
        "total": 0.0,
        **{k: 0.0 for k in FAKE_FEATURE_VALUES.keys()},
        **{c["key"]: 0.0 for c in CATEGORIES},
        **{sub_c["key"]: 0.0 for c in CATEGORIES for sub_c in c["sub_sections"]},
    }
    expected.update(
        {
            CompetitionFeatures.APT_DISTRIBUTION_TYPES.value: 4.3,
            CompetitionFeatures.APT_LIVING_DINING_MIN_REQ_PER_APT_TYPE.value: 10.0,
            CompetitionFeatures.APT_MIN_OUTDOOR_REQUIREMENT.value: 2.9,
            CompetitionFeatures.APT_SIZE_DINING_TABLE_REQ.value: 4.3,
            CompetitionFeatures.APT_DISTRIBUTION_TYPES_AREA_REQ.value: 10.0,
            CompetitionFeatures.RESIDENTIAL_USE.value: 10.0,
            CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: 10.0,
            CompetitionFeatures.RESIDENTIAL_TOTAL_HNF_REQ.value: 10.0,
            "residential_share": 10.0,
            "flat_deviation": 7.15,
            "architecture_room_programme": 2.85,
            CompetitionFeatures.APT_MAX_RECT_IN_PRIVATE_OUTDOOR.value: 10.0,
            CompetitionFeatures.APT_PCT_W_OUTDOOR.value: 0.0,
            "private_outdoor_areas": 8.0,
            CompetitionFeatures.BUILDING_AVG_MAX_RECT_ALL_APT_AREAS.value: 10.0,
            "flat_circulation_areas": 9.0,
            "storage_rooms_for_prams_bikes": 0.0,
            CompetitionFeatures.APT_PCT_W_STORAGE.value: 0.0,
            CompetitionFeatures.APT_AVG_DARKEST_ROOM_SUMMER.value: 10.0,
            CompetitionFeatures.APT_AVG_BRIGHTEST_ROOM_WINTER.value: 10.0,
            "environmental": 7.5,
            "environmental_design": 7.5,
            CompetitionFeatures.APT_BATHROOMS_TOILETS_DISTRIBUTION.value: 10.0,
            CompetitionFeatures.APT_RATIO_OUTDOOR_INDOOR.value: 10.0,
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: 0.0,
            CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_SUMMER.value: 10.0,
            CompetitionFeatures.APARTMENT_OUTDOOR_AREAS_TOTAL_HOURS_OF_SUN_WINTER.value: 10.0,
            CompetitionFeatures.BUILDING_PCT_CIRCULATION_RESIDENTIAL.value: 9.0,
            CompetitionFeatures.ANALYSIS_GREENERY.value: 5.0,
            CompetitionFeatures.ANALYSIS_SKY.value: 5.0,
            CompetitionFeatures.ANALYSIS_WATER.value: 5.0,
            CompetitionFeatures.ANALYSIS_BUILDINGS.value: 10.0,
            CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: 10.0,
            CompetitionFeatures.ANALYSIS_STREETS.value: 10.0,
            "noise": 5.0,
            CompetitionFeatures.NOISE_STRUCTURAL.value: 10.0,
            CompetitionFeatures.NOISE_INSULATED_ROOMS.value: 0.0,
            "reduit": 0.0,
            CompetitionFeatures.APT_RATIO_NAVIGABLE_AREAS.value: 9.2,
            "car_bicycle_bicycle_parking": 2.5,
            CompetitionFeatures.SECOND_BASEMENT_FLOOR_AVAILABLE.value: 10.0,
            CompetitionFeatures.AGF_W_REDUIT.value: 10.0,
            "further_key_figures": 10.0,
            "distribution_showers/bathtubs": 5.0,
            "areas": 10.0,
            "handicapped_accessible_building": 3.07,
            "architecture_usage": 7.5,
            "generosity": 5.72,
            "exposure": 10.0,
            "furnishability": 0.86,
            "total": 3.83,
            "total_program": 2.28,
            "total_archilyse": 1.56,
        }
    )
    return expected


@pytest.fixture
def expected_competition_scores_site_1_w_manual_input(
    overwritten_client_features, expected_competition_scores_site_1
):
    expected_competition_scores_site_1.pop("id")
    return {
        **expected_competition_scores_site_1,
        **{
            list(overwritten_client_features.keys())[0]: 0.0,
            "residential_share": 6.67,
            "architecture_usage": 5.83,
            "total": 5.66,
            "total_program": 3.19,
            "total_archilyse": 2.47,
        },
    }


@pytest.fixture
def expected_competition_scores_site_1_no_red_flags(expected_competition_scores_site_1):
    return {
        **expected_competition_scores_site_1,
        **{
            CompetitionFeatures.APT_PCT_W_OUTDOOR.value: 4.3,
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: 7.1,
            CompetitionFeatures.APT_PCT_W_STORAGE.value: 1.4,
            CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value: 2.9,
        },
    }


@pytest.fixture
def expected_competition_scores_site_2(expected_competition_scores_site_1):
    return {
        **expected_competition_scores_site_1,
        **{
            CompetitionFeatures.ANALYSIS_GREENERY.value: 10.0,
            CompetitionFeatures.ANALYSIS_SKY.value: 10.0,
            CompetitionFeatures.ANALYSIS_WATER.value: 10.0,
            CompetitionFeatures.ANALYSIS_BUILDINGS.value: 0.0,
            CompetitionFeatures.ANALYSIS_RAILWAY_TRACKS.value: 0.0,
            CompetitionFeatures.ANALYSIS_STREETS.value: 0.0,
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: 0.0,
            "environmental": 5.0,
            "environmental_design": 5.0,
            "total": 5.61,
            "total_program": 3.64,
            "total_archilyse": 1.97,
        },
    }


@pytest.fixture
def expected_competition_scores_site_2_no_red_flags(expected_competition_scores_site_2):
    return {
        **expected_competition_scores_site_2,
        **{
            CompetitionFeatures.APT_PCT_W_OUTDOOR.value: 4.3,
            CompetitionFeatures.APT_RATIO_BATHROOM_MIN_REQUIREMENT.value: 7.1,
            CompetitionFeatures.APT_PCT_W_STORAGE.value: 1.4,
            CompetitionFeatures.APT_RATIO_REDUIT_W_WATER_CONNEXION.value: 2.9,
        },
    }


@pytest.fixture
def competition_configuration():
    return {
        "flat_types_distribution": [
            {"apartment_type": [2], "percentage": 0.5},
            {"apartment_type": [4.5], "percentage": 0.5},
        ],
        "living_dining_desired_sizes_per_apt_type": [
            {"apartment_type": 1.0, "desired": 5},
            {"apartment_type": 3.0, "desired": 5},
            {"apartment_type": 4.5, "desired": 5},
        ],
        "min_outdoor_area_per_apt": 7.0,
        "residential_ratio": {"desired_ratio": 1.0, "acceptable_deviation": 0.0},
        "total_hnf_req": 10,
        "bikes_boxes_count_min": 1,
        "showers_bathtubs_distribution": [
            {
                "apartment_type": 2,
                "percentage": 0.5,
                "features": [
                    {
                        "SHOWER": 1,
                        "BATHTUB": 1,
                        "SINK": 1,
                        "TOILET": 1,
                    }
                ],
            },
            {
                "apartment_type": 4.5,
                "percentage": 0.5,
                "features": [
                    {
                        "SHOWER": 1,
                        "BATHTUB": 1,
                        "SINK": 1,
                        "TOILET": 1,
                    }
                ],
            },
        ],
        "bathrooms_toilets_distribution": [
            {
                "apartment_type": 1.5,
                "desired": ["BATHROOM"],
            },
            {
                "apartment_type": 2.5,
                "desired": ["BATHROOM"],
            },
            {
                "apartment_type": 3.5,
                "desired": ["BATHROOM", "TOILET"],
            },
            {
                "apartment_type": 3.5,
                "desired": ["BATHROOM", "BATHROOM"],
            },
        ],
        "dining_area_table_min_big_side": 3,
        "dining_area_table_min_small_side": 2,
        "flat_types_area_fulfillment": [{"apartment_type": 3.5, "area": 30}],
    }


@pytest.fixture
def expected_full_set_competition_features(expected_competition_features_site_1):
    """provides FULL set of features, mixed with the close to real expected features"""
    return {
        **FAKE_FEATURE_VALUES,
        **expected_competition_features_site_1,
    }


@pytest.fixture
def base_url():
    return f"http://{os.environ['SLAM_API_INTERNAL_URL']}"


@pytest.fixture
def dashboard_url(base_url):
    return f"{base_url}/dashboard"


@pytest.fixture
def admin_url(base_url):
    return f"{base_url}/admin"


@pytest.fixture
def dms_url(base_url):
    return f"{base_url}/dms"


@pytest.fixture
def api_url(base_url):
    return f"{base_url}/api"


@pytest.fixture
def classification_url_wrong_plan():
    return SlamUIClient._classification_url_plan(plan_id=9999999999)


@pytest.fixture
def linking_url_wrong_plan():
    return SlamUIClient._linking_url_plan(plan_id=9999999999)


@pytest.fixture
def georeference_url_wrong_plan():
    return SlamUIClient._georeference_url_plan(plan_id=9999999999)


@pytest.fixture
def splitting_url_wrong_plan():
    return SlamUIClient._splitting_url_plan(plan_id=9999999999)


@pytest.fixture
def login_url():
    return SlamUIClient._base_login_url()


@pytest.fixture
def viewer_url(base_url):
    return f"{base_url}/viewer"


@pytest.fixture
def editor_url():
    return SlamUIClient._base_editor_url()


@pytest.fixture
def editor_v2_url():
    return SlamUIClient._base_editor_v2_url()


@pytest.fixture
def potential_view_v2_url():
    return SlamUIClient._base_potential_view_v2_url()


@pytest.fixture
def overwritten_client_features():
    return {CompetitionFeatures.RESIDENTIAL_USE.value: {"COMMERCIAL": 10.0}}


@pytest.fixture
def triangle_polygon():
    return Polygon(((0.0, 0.0), (2.0, 0.0), (1.0, 2.0), (0.0, 0.0)))


@pytest.fixture
def invalid_multipolygon():
    polygon1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    polygon2 = Polygon([(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)])
    polygon3 = Polygon([(1, 0), (2, 0), (2, 1), (1, 1), (1, 0)])

    return MultiPolygon([polygon1, polygon2, polygon3])


@pytest.fixture
def circle_polygon():
    p = Point(0.0, 0.0)
    return p.buffer(1.0)


@pytest.fixture
def georef_plan_values(site_coordinates):
    return {
        332: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -706.50158144458,
            "georef_rot_angle": 89.0,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 1077.90072416267,
            "georef_scale": 0.000651438937907149,
        },
        863: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -1810.79140831601,
            "georef_rot_angle": 41.3330676609113,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 2271.31138717759,
            "georef_scale": 7.02954388265308e-05,
        },
        2494: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -2373.99198641457,
            "georef_rot_angle": 55.6246685463828,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 7714.28883693959,
            "georef_scale": 1.68006054178236e-05,
        },
        3332: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -1858.93754069634,
            "georef_rot_angle": 231.85955274211,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 1307.93061338708,
            "georef_scale": 0.000143589743589744,
        },
        3354: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -1702.9458372535,
            "georef_rot_angle": 305.264671122156,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 1274.84106434143,
            "georef_scale": 0.000160919540229885,
        },
        3489: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -833.033794328579,
            "georef_rot_angle": 335.284253385872,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 1877.59953704938,
            "georef_scale": 0.000295094166181684,
        },
        4976: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -2034.75128245626,
            "georef_rot_angle": 312.854498274469,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 2910.11813521304,
            "georef_scale": 7.42811211419092e-05,
        },
        5797: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -297.0,
            "georef_rot_angle": 291.941460997825,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 397.5,
            "georef_scale": 0.000747469144362779,
        },
        5825: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -377.449287221441,
            "georef_rot_angle": 219.115103841475,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 619.908070026149,
            "georef_scale": 0.000725269861441508,
        },
        6380: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -3302.5,
            "georef_rot_angle": 287.863360643585,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 6648.5,
            "georef_scale": 1.78614621038232e-05,
        },
        6951: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -1803.0,
            "georef_rot_angle": 290.954266118316,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 4189.0,
            "georef_scale": 7.33718054410552e-05,
        },
        7641: {
            "georef_y": site_coordinates["lat"],
            "georef_rot_y": -1057.29354085503,
            "georef_rot_angle": 79.6136576089139,
            "georef_x": site_coordinates["lon"],
            "georef_rot_x": 2383.69635750003,
            "georef_scale": 7.10431071927844e-05,
        },
    }


@pytest.fixture
def georeference_parameters():
    return {
        "_rotation_pivot_x": 1.0,
        "_rotation_pivot_y": 1.0,
        "_rotation_angle": 1.0,
        "_scaling_pivot_x": 0,
        "_scaling_pivot_y": 0,
        "_scaling_factor": 1,
        "_translation_x": 2715739.6394532886,
        "_translation_y": 1242377.7402708225,
        "_translation_z": 100,
        "_swap_dimensions": (0, 1),
    }


@pytest.fixture
def extrusion_parameters():
    return {
        "window_start_height": 0.5,
        "window_end_height": 2.4,
        "wall_height": 2.6,
        "level_baseline": 2.9,
        "door_height": 2,
    }


@pytest.fixture
def qa_data():
    return {
        "61728": {
            "HNF": 135.6138330670805,
            "number_of_rooms": 3.5,
            "client_building_id": "fake-id-1",
        },
        "61734": {
            "HNF": 54.332033712307684,
            "floor": 1,
            "client_building_id": "fake-id-1",
        },
        "61735": {
            "HNF": 80.14868763812319,
            "floor": 1,
            "client_building_id": "fake-id-1",
        },
        "61736": {
            "HNF": 89.69823103895916,
            "floor": 1,
            "client_building_id": "fake-id-1",
        },
    }


@pytest.fixture
def validation_unit_stats():
    from handlers.sim_validators import SUN_DIMENSION_JUNE_MIDDAY

    return {
        1: {"site": {"min": 13}, SUN_DIMENSION_JUNE_MIDDAY: {"max": 2}},  # fails site
        2: {"site": {"min": 10}, SUN_DIMENSION_JUNE_MIDDAY: {"max": 0.09}},  # fails sun
    }


@pytest.fixture
def validation_unit_stats_results():
    from handlers.sim_validators import UnitsHighSiteViewValidator, UnitsLowSunValidator

    return {"1": [UnitsHighSiteViewValidator.msg], "2": [UnitsLowSunValidator.msg]}


@pytest.fixture
def site_region_proj_ch():
    from common_utils.constants import REGION

    return {
        "georef_region": REGION.CH.name,
    }


@pytest.fixture
def convex_building_1(fixtures_swisstopo_path):
    with fixtures_swisstopo_path.joinpath("buildings/3d_convex_building1.wkb").open(
        "r"
    ) as f:
        return wkb.load(fp=f, hex=True)


@pytest.fixture
def expected_unit_clusters():
    # clusters and centroids
    return [
        (["02.L", "01.L", "03.L", "04.L"], "03.L"),
        (["02.R", "01.R", "03.R"], "02.R"),
        (["00.L", "00.R"], "00.L"),
        (["05.R"], "05.R"),
        (["04.R"], "04.R"),
        (["05.L"], "05.L"),
    ]


@pytest.fixture
def manually_created_surroundings():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
                    "height": 100.0,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [8.522558212280273, 47.375685893433115],
                            [8.526248931884766, 47.36219950880962],
                            [8.540925979614258, 47.36981508949069],
                            [8.522558212280273, 47.375685893433115],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "surrounding_type": ManualSurroundingTypes.EXCLUSION_AREA.name,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [7.522558212280273, 47.375685893433115],
                            [7.526248931884766, 47.36219950880962],
                            [7.540925979614258, 47.36981508949069],
                            [7.522558212280273, 47.375685893433115],
                        ]
                    ],
                },
            },
        ],
    }


@pytest.fixture
def manually_created_surroundings_JAN():
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
                    "height": 100.0,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [8.716481924057007, 47.49778890741363],
                            [8.716594576835632, 47.49735036517129],
                            [8.71712028980255, 47.49723801078424],
                            [8.717356324195862, 47.4974880895758],
                            [8.717517256736755, 47.497745415784614],
                            [8.71766746044159, 47.49814046342564],
                            [8.717710375785828, 47.49841590772859],
                            [8.718016147613525, 47.49842315624335],
                            [8.718075156211853, 47.49864423546326],
                            [8.716937899589539, 47.49868410210877],
                            [8.716857433319092, 47.49837241661892],
                            [8.717308044433594, 47.49837966513971],
                            [8.717061281204224, 47.497484465254004],
                            [8.716728687286377, 47.4975460786907],
                            [8.716723322868347, 47.49781427751393],
                            [8.716481924057007, 47.49778890741363],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "surrounding_type": ManualSurroundingTypes.EXCLUSION_AREA.name,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [8.717501163482666, 47.497212640405515],
                            [8.717903494834898, 47.49725975681342],
                            [8.718150258064268, 47.49766205672831],
                            [8.718493580818176, 47.497622189306774],
                            [8.718552589416504, 47.49715465092239],
                            [8.718976378440857, 47.49716552395535],
                            [8.718493580818176, 47.49861886576399],
                            [8.717501163482666, 47.497212640405515],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
                    "height": 100.0,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [8.719019293785095, 47.497125656156804],
                            [8.71916949748993, 47.49708216397842],
                            [8.719362616539001, 47.49807160212414],
                            [8.719496726989746, 47.49809334780807],
                            [8.719770312309265, 47.49700967693435],
                            [8.720247745513916, 47.496948062868235],
                            [8.720521330833435, 47.498383289399726],
                            [8.720188736915588, 47.49842678050037],
                            [8.71987760066986, 47.49743010039689],
                            [8.719566464424133, 47.49855362933819],
                            [8.719314336776733, 47.498571750575714],
                            [8.719019293785095, 47.497125656156804],
                        ]
                    ],
                },
            },
        ],
    }


@pytest.fixture
def default_plan_info():
    return {
        "georef_scale": 1.0,
        "default_wall_height": 2.6,
        "default_door_height": 2.0,
        "default_window_lower_edge": 0.5,
        "default_window_upper_edge": 2.4,
        "default_ceiling_slab_height": 0.3,
    }


@pytest.fixture
def custom_element_heights():
    from brooks.types import FeatureType, OpeningType, SeparatorType

    return {
        SeparatorType.WALL: (0, 0),
        SeparatorType.AREA_SPLITTER: (1, 1),
        "GENERIC_SPACE_HEIGHT": (2, 4),
        FeatureType.ELEVATOR: (3, 9),
        FeatureType.BATHTUB: (4, 16),
        FeatureType.SINK: (5, 25),
        FeatureType.SHOWER: (6, 36),
        FeatureType.TOILET: (7, 49),
        FeatureType.KITCHEN: (8, 64),
        FeatureType.SHAFT: (9, 81),
        FeatureType.STAIRS: (10, 100),
        FeatureType.SEAT: (11, 121),
        FeatureType.RAMP: (15, 225),
        FeatureType.BIKE_PARKING: (18, 324),
        FeatureType.BUILT_IN_FURNITURE: (19, 361),
        FeatureType.CAR_PARKING: (20, 400),
        FeatureType.WASHING_MACHINE: (21, 441),
        FeatureType.OFFICE_DESK: (13, 169),
        OpeningType.DOOR: (22, 484),
        OpeningType.ENTRANCE_DOOR: (23, 529),
        OpeningType.WINDOW: (24, 576),
        SeparatorType.RAILING: (25, 625),
        SeparatorType.COLUMN: (26, 676),
        "CEILING_SLAB": (27, 729),
        "FLOOR_SLAB": (28, 784),  # only used in the most bottom floor
    }


@pytest.fixture
def react_planner_non_rectangular_walls() -> ReactPlannerData:
    """

    ┌────x
    │    xx
    │    ┼ xx
    │    xx xxx
    │    │xx  xx
    │    │ xxx  xx
    │    │   xxx xxx
    │    │     xx  xx
    │    │      xxx  xx
    │    │        xx  xx
    │    │          xx xxx
    │    │           xx  xxx
    │    │            xxx  xxx
    │    │              xx   xx
    │    │               xx   xxx
    │    │                 xx   xx
    │    │                  xx   xxx
    │    │                   xxx   xx
    │    │                     xxx  xx
    │   x└───────────────────────x   xx
    │ xx                              xx
    └────────────────────────────────────

    There is also 1 door in the bottom line
    """
    fake_vertex_a = ReactPlannerVertex(x=0, y=0)
    fake_vertex_b = ReactPlannerVertex(x=1, y=0)
    fake_vertex_c = ReactPlannerVertex(x=2, y=0)
    fake_vertex_d = ReactPlannerVertex(x=3, y=0)
    fake_vertex_e = ReactPlannerVertex(x=4, y=0)
    fake_vertex_f = ReactPlannerVertex(x=5, y=0)
    vertices = [fake_vertex_a, fake_vertex_b]
    aux_vertices = [
        fake_vertex_c,
        fake_vertex_d,
        fake_vertex_e,
        fake_vertex_f,
    ]

    bottom_line = ReactPlannerLine(
        vertices=[v.id for v in vertices],
        auxVertices=[v.id for v in aux_vertices],
        coordinates=[
            [
                [0, 0],
                [5, 0],
                [3.5, 1],
                [1, 1],
                [0, 0],
            ]
        ],
        properties=ReactPlannerLineProperties(
            height=ReactPlannerGeomProperty(value=280),
            width=ReactPlannerGeomProperty(value=1),
        ),
    )
    left_line = ReactPlannerLine(
        vertices=[v.id for v in vertices],
        auxVertices=[v.id for v in aux_vertices],
        coordinates=[
            [
                [0, 0],
                [0, 5],
                [1, 5],
                [1, 1],
                [0, 0],
            ]
        ],
        properties=ReactPlannerLineProperties(
            height=ReactPlannerGeomProperty(value=280),
            width=ReactPlannerGeomProperty(value=1),
        ),
    )
    top_line = ReactPlannerLine(
        vertices=[v.id for v in vertices],
        auxVertices=[v.id for v in aux_vertices],
        coordinates=[
            [
                [1, 5],
                [1, 4],
                [3.5, 1],
                [5, 0],
                [1, 5],
            ]
        ],
        properties=ReactPlannerLineProperties(
            height=ReactPlannerGeomProperty(value=280),
            width=ReactPlannerGeomProperty(value=1),
        ),
    )
    hole = ReactPlannerHole(
        line=bottom_line.id,
        coordinates=[
            [
                [2, 0],
                [3, 0],
                [3, 1],
                [2, 1],
                [2, 0],
            ]
        ],
        door_sweeping_points=ReactPlannerDoorSweepingPoints(
            angle_point=[3, 0], closed_point=[2, 0], opened_point=[3, -1]
        ),
        type=ReactPlannerType.DOOR.value,
        properties=ReactPlannerHoleProperties(
            heights=ReactPlannerHoleHeights(lower_edge=40, upper_edge=260),
            width=ReactPlannerGeomProperty(value=2),
            altitude=ReactPlannerGeomProperty(value=0),
            length=ReactPlannerGeomProperty(value=0),
        ),
    )

    for vertex in chain(vertices, aux_vertices):
        vertex.lines = [bottom_line.id, left_line.id, top_line.id]

    return ReactPlannerData(
        width=100,
        height=100,
        scale=10000.0,  # Given the coordinates are in pixels, with this scale we will have
        # elements with a size of meters = pixels
        layers={
            "layer-1": ReactPlannerLayer(
                vertices={v.id: v for v in chain(vertices, aux_vertices)},
                lines={
                    left_line.id: left_line,
                    top_line.id: top_line,
                    bottom_line.id: bottom_line,
                },
                holes={hole.id: hole},
            )
        },
    )


@pytest.fixture
def acute_triangle():
    acute_triangle = Polygon([(0.0, 0.0), (-1.00, 2.0), (-0.7, 2.05), (0, 0)])
    return MultiPolygon([acute_triangle])


@pytest.fixture
def potential_view_results():
    return {
        "observation_points": [{"lat": 0.0, "lon": 0.0, "height": 0.0}],
        **{dimension.value: [0.0] for dimension in VIEW_DIMENSION_2},
    }


@pytest.fixture
def potential_sun_results():
    return {
        "observation_points": [{"lat": 0.0, "lon": 0.0, "height": 0.0}],
        **{dimension: [0.0] for dimension in FIXED_SUN_DIMENSIONS},
    }
