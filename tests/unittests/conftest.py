import json
import os

import pytest
from shapely.geometry import Point

from brooks.models import SimLayout
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData

pytest_plugins = (
    "tests.constant_fixtures",
    "tests.annotations_fixtures",
    "tests.file_fixtures",
    "tests.mocks_fixtures",
    "tests.helper_fixtures",
)


@pytest.mark.firstresult
def pytest_xdist_auto_num_workers():
    return os.cpu_count()


@pytest.fixture
def site(site_coordinates, site_region_proj_ch):
    return {
        "id": 44,
        "group_id": 1,
        "name": "test_site",
        **site_coordinates,
        **site_region_proj_ch,
    }


@pytest.fixture
def plan_info():
    return {
        "id": 123,
        "site_id": 44,
        "annotation_finished": False,
        "image_width": 2479,
        "image_height": 3508,
        "georef_rot_angle": 52.0,
        "georef_rot_x": 5825.17195187236,
        "default_window_lower_edge": 0.5,
        "default_window_upper_edge": 2.4,
        "default_ceiling_slab_height": 0.3,
        "georef_x": 8.63921658028377,
        "georef_rot_y": -5624.49165408218,
        "default_wall_height": 2.8,
        "georef_y": 47.54729293632132,
        "georef_scale": 1.56183579474477,
    }


@pytest.fixture
def user():
    return {"id": 1, "group_id": 1}


@pytest.fixture()
def basel_location():
    """lat = 47.5575
    lon = 7.6165
    """
    return Point(2613388.1984786573, 1267435.7158098095)


@pytest.fixture()
def monaco_sea_location():
    """lat = 43.734765
    lon = 7.4208953
    """
    return Point(372833.31418195815, 4843626.08414902)


@pytest.fixture()
def monaco_street_location():
    """lat = 43.73585981372685
    lon = 7.431144462092484
    """
    return Point(373661, 4843732)


@pytest.fixture()
def monaco_buildings_location():
    """lat = 43.734765
    lon = 7.4208953
    """
    return Point(372833.31418195815, 4843626.08414902)


@pytest.fixture()
def oslo_location():
    """lat = 59.91473290604278
    lon = 10.752783100935165
    """
    return Point(662504, 6652195)


@pytest.fixture
def layout_scaled_classified_wo_db_conn(
    annotations_path, fixtures_path, georef_plan_values
):
    def _layout_scaled_classified_wrapped(annotation_plan_id) -> SimLayout:
        from handlers import PlanLayoutHandler, ReactPlannerHandler

        with annotations_path.joinpath(
            f"plan_{annotation_plan_id}.json"
        ).open() as annotation_file, fixtures_path.joinpath(
            f"areas/areas_plan_{annotation_plan_id}.json"
        ).open() as areas_file:
            planner_elements = ReactPlannerData(**json.load(annotation_file))
            layout = ReactPlannerToBrooksMapper.get_layout(
                planner_elements=planner_elements, scaled=True
            )
            scaled_db_areas = PlanLayoutHandler.scale_areas(
                db_areas=json.load(areas_file),
                pixels_to_meters_scale=ReactPlannerHandler().pixels_to_meters_scale(
                    plan_id=annotation_plan_id, plan_scale=planner_elements.scale
                ),
            )
            layout = PlanLayoutHandler(plan_id=-999).map_and_classify_layout(
                layout=layout, areas_db=scaled_db_areas, raise_on_inconsistency=False
            )
        return layout

    return _layout_scaled_classified_wrapped


@pytest.fixture(autouse=True)
def requests_mock(requests_mock):
    """To make sure no requests are happening in unittests"""
    return requests_mock
