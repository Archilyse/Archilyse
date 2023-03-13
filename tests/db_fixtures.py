import functools
import json
import uuid
from collections import defaultdict
from itertools import chain
from operator import itemgetter
from typing import Dict
from zipfile import ZipFile

import pytest
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import split

from brooks.models import SimArea, SimLayout, SimSpace
from brooks.types import AreaType
from common_utils.competition_constants import CompetitionFeatures
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    CONNECTIVITY_DIMENSIONS,
    DB_INDEX_ANF,
    DB_INDEX_FF,
    DB_INDEX_HNF,
    DB_INDEX_NET_AREA,
    DB_INDEX_NNF,
    DB_INDEX_ROOM_NUMBER,
    DB_INDEX_VF,
    NOISE_SURROUNDING_TYPE,
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SI_UNIT_BY_NAME,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    SUN_DIMENSION,
    TASK_TYPE,
    UNIT_USAGE,
    VIEW_DIMENSION,
    VIEW_DIMENSION_2,
)
from handlers import AreaHandler
from handlers.db import (
    AreaDBHandler,
    ManualSurroundingsDBHandler,
    ReactPlannerProjectsDBHandler,
)
from handlers.db.qa_handler import (
    INDEX_ANF_AREA,
    INDEX_HNF_AREA,
    INDEX_ROOM_NUMBER,
    QA_COLUMN_HEADERS,
)
from handlers.editor_v2.schema import ReactPlannerData
from simulations.suntimes.suntimes_handler import SuntimesHandler

from .constants import (
    CLIENT_ID_1,
    CLIENT_ID_2,
    CLIENT_ID_3,
    CLIENT_ID_4,
    CLIENT_ID_5,
    TEST_CLIENT_NAME,
    UNIT_ID_1,
    UNIT_ID_2,
    UNIT_ID_3,
    UNIT_ID_4,
    USERS,
)
from .utils import (
    _get_or_create,
    add_simulation,
    create_user_context,
    db_areas_from_layout,
    fake_unit_simulation_results,
    load_plan_helper,
    login_with,
    prepare_for_competition,
    random_simulation_version,
)

# Login as user helper decorator
login_as = functools.partial(pytest.mark.parametrize("login", indirect=True))


@pytest.fixture
def login(client, request):
    """Login as user with flask test_client, with default user being Admin"""
    try:
        user = USERS[request.param]
    except AttributeError:
        user = USERS["ADMIN"]

    yield login_with(client, user)
    client.cookie_jar.clear_session_cookies()


@pytest.fixture
def client_db():
    from handlers.db import ClientDBHandler

    return _get_or_create(
        ClientDBHandler,
        {
            "name": TEST_CLIENT_NAME,
            "option_dxf": True,
            "option_analysis": True,
            "option_pdf": True,
            "option_ifc": True,
        },
    )


@pytest.fixture
def site(
    client_db,
    login,
    site_coordinates,
    site_region_proj_ch,
) -> dict:
    from handlers.db import SiteDBHandler

    return SiteDBHandler.add(
        client_id=client_db["id"],
        client_site_id="Leszku-payaso",
        name="Big-ass portfolio",
        region="Switzerland",
        gcs_buildings_link="random gcs_buildings_link",
        group_id=login["group"]["id"],
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        **site_region_proj_ch,
        **site_coordinates,
    )


@pytest.fixture
def site_w_qa_data(site, qa_data):
    from handlers.db import QADBHandler

    QADBHandler.add(
        client_site_id=site["client_site_id"],
        client_id=site["client_id"],
        site_id=site["id"],
        data=qa_data,
    )
    return site


@pytest.fixture
def site_bf_success(site):
    from handlers.db import SiteDBHandler

    return SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"basic_features_status": ADMIN_SIM_STATUS.SUCCESS},
    )


@pytest.fixture
def upwork_group():
    from handlers.db import GroupDBHandler

    return _get_or_create(GroupDBHandler, dict(name="UpWork"))


@pytest.fixture
def oecc_group():
    from handlers.db import GroupDBHandler

    return _get_or_create(GroupDBHandler, dict(name="OECC"))


@pytest.fixture
def archilyse_group():
    from handlers.db import GroupDBHandler

    return _get_or_create(GroupDBHandler, dict(name=USERS["ADMIN"]["group"]))


@pytest.fixture
def site_delivered_simulated(
    site, basic_features_finished, view_sun_simulation_finished
):
    from handlers.db import SiteDBHandler

    return SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={
            "delivered": True,
            "pipeline_and_qa_complete": True,
            "heatmaps_qa_complete": True,
            "basic_features_status": ADMIN_SIM_STATUS.SUCCESS.value,
            "full_slam_results": ADMIN_SIM_STATUS.SUCCESS.value,
            "sample_surr_task_state": ADMIN_SIM_STATUS.SUCCESS.value,
        },
    )


@pytest.fixture
def validation_notes():
    return "some notes"


@pytest.fixture
def site_delivered_simulated_notes(site_delivered_simulated, validation_notes):
    from handlers.db import SiteDBHandler

    return SiteDBHandler.update(
        item_pks={"id": site_delivered_simulated["id"]},
        new_values={"validation_notes": validation_notes},
    )


@pytest.fixture
def site_for_coordinate_validation(
    client_db, qa_without_site, site_coordinates, site_region_proj_ch
):
    from handlers.db import SiteDBHandler

    return SiteDBHandler.add(
        client_id=client_db["id"],
        name="Big-ass portfolio",
        region="Switzerland",
        client_site_id="blah",
        **site_region_proj_ch,
        **site_coordinates,
    )


@pytest.fixture
def qa_without_site(client_db):
    from handlers.db import QADBHandler
    from handlers.db.qa_handler import QA_COLUMN_HEADERS

    return QADBHandler.add(
        client_id=client_db["id"],
        data={
            CLIENT_ID_1: dict(
                {column_header: None for column_header in QA_COLUMN_HEADERS},
                **{"net_area": "94", "number_of_rooms": "4.5"},
            )
        },
    )


@pytest.fixture
def qa_db(site, qa_without_site):
    from handlers.db import QADBHandler

    return QADBHandler.update(
        item_pks={"id": qa_without_site["id"]},
        new_values={
            "client_site_id": site["client_site_id"],
            "site_id": site["id"],
        },
    )


@pytest.fixture
def qa_db_empty(site):
    from handlers.db import QADBHandler

    return QADBHandler.add(
        client_site_id=site["client_site_id"],
        client_id=site["client_id"],
        site_id=site["id"],
        data={},
    )


@pytest.fixture
def unit(site, plan, floor):
    from handlers.db import UnitDBHandler

    return UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=0,
        client_id=CLIENT_ID_1,
    )


@pytest.fixture
def plan(mocked_plan_image_upload_to_gc, fixtures_path, site, building):
    floorplan_path = fixtures_path.joinpath("images/image_plan_332.jpg")
    return load_plan_helper(floorplan_path, site, building)


@pytest.fixture
def plan_masterplan(mocked_plan_image_upload_to_gc, fixtures_path, site, building):
    floorplan_path = fixtures_path.joinpath("images/image_plan_332.jpg")
    return load_plan_helper(floorplan_path, site, building, is_masterplan=True)


@pytest.fixture
def plan_annotated(
    plan,
    fixtures_path,
    celery_eager,
    react_planner_background_image_one_unit,
):
    from handlers.editor_v2 import ReactPlannerHandler

    ReactPlannerHandler().store_plan_data(
        plan_id=plan["id"],
        plan_data=react_planner_background_image_one_unit,
        validated=True,
    )
    return plan


@pytest.fixture
def plan_georeferenced(
    mocked_plan_image_upload_to_gc, fixtures_path, site, building, georef_plan_values
):
    floorplan_path = fixtures_path.joinpath("images/image_plan_332.jpg")
    return load_plan_helper(floorplan_path, site, building, **georef_plan_values[332])


@pytest.fixture
def other_clients_plan(
    mocked_plan_image_upload_to_gc,
    fixtures_path,
    other_clients_site_with_full_slam_results_success,
    other_clients_building,
):
    floorplan_path = fixtures_path.joinpath("images/image_plan_332.jpg")
    return load_plan_helper(
        floorplan_path,
        other_clients_site_with_full_slam_results_success,
        other_clients_building,
    )


@pytest.fixture
def plan_b(mocked_plan_image_upload_to_gc, fixtures_path, site, building):
    floorplan_path = fixtures_path.joinpath("images/floorplan_b.jpg")
    return load_plan_helper(floorplan_path, site, building)


@pytest.fixture
def plan_image_b(site, mocked_plan_image_upload_to_gc, building, image_b_path):
    from handlers import PlanHandler

    with image_b_path.open("rb") as fp:
        content_type = "image/jpg"

        return PlanHandler.add(
            plan_content=fp.read(),
            plan_mime_type=content_type,
            site_id=site["id"],
            building_id=building["id"],
            georef_rot_x=1161.1285264436553,
            georef_rot_y=-710.3825398742664,
            georef_x=site["lon"] - 0.01,
            georef_y=site["lat"] + 0.01,
            georef_scale=1,
            georef_rot_angle=0.1,
        )


@pytest.fixture
def areas_db(plan, area_polygon_wkt):
    from handlers.db import AreaDBHandler

    return [
        AreaDBHandler.add(**x)
        for x in [
            {
                "plan_id": plan["id"],
                "coord_x": 100.0,
                "coord_y": 200.0,
                "area_type": AreaType.NOT_DEFINED.name,
                "scaled_polygon": area_polygon_wkt,
            },
            {
                "plan_id": plan["id"],
                "coord_x": 200.0,
                "coord_y": 300.0,
                "area_type": AreaType.ROOM.name,
                "scaled_polygon": area_polygon_wkt,
            },
        ]
    ]


@pytest.fixture
def building(site):
    from handlers.db import BuildingDBHandler

    return BuildingDBHandler.add(
        site_id=site["id"],
        client_building_id="1",
        housenumber="20-22",
        city="Zurich",
        zipcode="8000",
        street="some street",
        elevation=100.0,
    )


@pytest.fixture
def other_client():
    from handlers.db import ClientDBHandler

    return ClientDBHandler.add(name="other client")


@pytest.fixture
def other_clients_site_with_full_slam_results_success(
    other_client,
    site_coordinates,
    login,
    site_region_proj_ch,
):
    from handlers.db import SiteDBHandler

    return SiteDBHandler.add(
        client_id=other_client["id"],
        client_site_id="Leszku-payaso-other",
        name="Big-ass portfolio",
        region="Switzerland",
        gcs_buildings_link="random gcs_buildings_link",
        group_id=login["group"]["id"],
        full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
        **site_region_proj_ch,
        **site_coordinates,
    )


@pytest.fixture
def other_clients_building(other_clients_site_with_full_slam_results_success):
    from handlers.db import BuildingDBHandler

    return BuildingDBHandler.add(
        site_id=other_clients_site_with_full_slam_results_success["id"],
        housenumber="20-22",
        city="Zurich",
        zipcode="8000",
        street="somestreet",
        elevation=100.0,
    )


@pytest.fixture
def floor(plan, building, floor_number=1):
    from handlers.db import FloorDBHandler

    return FloorDBHandler.add(
        plan_id=plan["id"], building_id=building["id"], floor_number=floor_number
    )


@pytest.fixture
def floor2(plan, building, floor_number=2):
    from handlers.db import FloorDBHandler

    return FloorDBHandler.add(
        plan_id=plan["id"], building_id=building["id"], floor_number=floor_number
    )


def _finish_annotations_method(plan, annotations: Dict, annotation_finished=True):
    from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler

    ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotations)
    update_plan_kwargs = dict(annotation_finished=annotation_finished)

    PlanDBHandler.update(item_pks=dict(id=plan["id"]), new_values=update_plan_kwargs)
    return annotations


@pytest.fixture
def annotations_finished(plan, annotations_plan_2016):
    return _finish_annotations_method(plan, annotations=annotations_plan_2016)


@pytest.fixture
def annotations_box_finished(plan, annotations_box_data):
    return _finish_annotations_method(plan, annotations=annotations_box_data)


@pytest.fixture
def annotations_box_unfinished(plan, annotations_box_data):
    return _finish_annotations_method(
        plan,
        annotations=annotations_box_data,
        annotation_finished=False,
    )


@pytest.fixture
def plan_box_pipelined(plan, annotations_box_finished, fixtures_path):
    from handlers import AreaHandler, PlanLayoutHandler
    from handlers.db import PlanDBHandler

    default_box_brooks_model = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
        validate=False, classified=False, scaled=False
    )
    for area in default_box_brooks_model.areas:
        area._type = AreaType.ROOM

    AreaHandler.recover_and_upsert_areas(
        plan_id=plan["id"],
        plan_layout=default_box_brooks_model,
    )

    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values=dict(
            georef_x=-19.91798993747354,
            georef_y=32.124497846031055,
            georef_scale=10**-4,
            georef_rot_angle=1.0,
            georef_rot_x=1.0,
            georef_rot_y=1.0,
        ),
    )
    return plan


@pytest.fixture
def annotations_box_finished_classified_and_splitted(plan, unit, plan_box_pipelined):
    from handlers import AreaHandler
    from handlers.db import AreaDBHandler

    area_id = list(AreaDBHandler.find_ids(plan_id=plan["id"]))[0]
    AreaHandler.update_relationship_with_units(
        plan_id=plan["id"],
        apartment_no=unit["apartment_no"],
        area_ids=[area_id],
    )
    return plan_box_pipelined


@pytest.fixture
def plan_classified_scaled(plan, annotations_finished, annotations_plan_2016):

    from handlers import AreaHandler
    from handlers.db import PlanDBHandler
    from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper

    brooks_model = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_2016)
    )
    AreaHandler.recover_and_upsert_areas(plan_id=plan["id"], plan_layout=brooks_model)

    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values=dict(
            georef_scale=7.78269632188872e-05,
            georef_rot_x=1261.67548247451,
            georef_rot_y=-793.262922077922,
        ),
    )
    return plan


@pytest.fixture
def plan_classified_scaled_georeferenced(plan_classified_scaled, annotations_finished):
    from handlers.db import PlanDBHandler

    return PlanDBHandler.update(
        item_pks=dict(id=plan_classified_scaled["id"]),
        new_values=dict(
            georef_x=8.28466497809749,
            georef_y=47.0655380525778,
            georef_rot_angle=298.27219500966,
        ),
    )


@pytest.fixture
def plan_1478_result_vector_paths(fixtures_path):
    unit_ids = [UNIT_ID_1, UNIT_ID_2, UNIT_ID_3, UNIT_ID_4]

    vector_names = ["full_vector_with_balcony"]

    result_vector_paths = dict()
    for unit_id in unit_ids:
        result_vector_paths[unit_id] = {
            name: fixtures_path.joinpath(f"vectors/{name}-1478-{unit_id}.json")
            for name in vector_names
        }

    return result_vector_paths


@pytest.fixture
def result_vector_paths(raw_data_path):
    unit_ids = [UNIT_ID_1, UNIT_ID_2, UNIT_ID_3, UNIT_ID_4]

    vector_names = ["full_vector_with_balcony"]

    result_vector_paths = dict()
    for unit_id in unit_ids:
        result_vector_paths[unit_id] = {
            name: raw_data_path.joinpath(f"{name}-{unit_id}.json")
            for name in vector_names
        }

    return result_vector_paths


@pytest.fixture
def first_pipeline_complete_db_models(
    client_db, site, building, plan, make_classified_plans, fixtures_path
):
    from handlers import AreaHandler
    from handlers.db import FloorDBHandler, PlanDBHandler, SiteDBHandler, UnitDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site["id"]), new_values=dict(pipeline_and_qa_complete=True)
    )
    floor = FloorDBHandler.add(
        plan_id=plan["id"], building_id=building["id"], floor_number=1, georef_z=1.0
    )
    plan = PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values={
            "annotation_finished": True,
            "georef_x": 8.969686466464522,
            "georef_y": 47.32211927705434,
            "georef_rot_angle": 1.0,
            "georef_rot_x": 1.0,
            "georef_scale": 1.0,
            "georef_rot_y": 1.0,
        },
    )
    db_areas = make_classified_plans(plan)
    units = [
        UnitDBHandler.add(
            id=UNIT_ID_1,
            site_id=site["id"],
            plan_id=plan["id"],
            floor_id=floor["id"],
            unit_type="1.5",
            apartment_no=0,
            client_id=CLIENT_ID_1,
            ph_final_gross_rent_adj_factor=1,
            ph_final_gross_rent_annual_m2=1000.00,
        ),
        UnitDBHandler.add(
            id=UNIT_ID_2,
            site_id=site["id"],
            plan_id=plan["id"],
            floor_id=floor["id"],
            unit_type="2.5",
            apartment_no=1,
            client_id=CLIENT_ID_2,
            ph_final_gross_rent_adj_factor=1,
            ph_final_gross_rent_annual_m2=1000.00,
        ),
        UnitDBHandler.add(
            id=UNIT_ID_3,
            site_id=site["id"],
            plan_id=plan["id"],
            floor_id=floor["id"],
            unit_type="2.5",
            apartment_no=2,
            client_id=CLIENT_ID_3,
            ph_final_gross_rent_adj_factor=1,
            ph_final_gross_rent_annual_m2=1000.00,
        ),
        UnitDBHandler.add(
            id=UNIT_ID_4,
            site_id=site["id"],
            plan_id=plan["id"],
            floor_id=floor["id"],
            unit_type="3.5",
            apartment_no=3,
            client_id=CLIENT_ID_4,
            ph_final_gross_rent_adj_factor=1,
            ph_final_gross_rent_annual_m2=1000.00,
        ),
    ]

    # Add basic features data to the units
    add_simulation(
        fixtures_path=fixtures_path.joinpath("competition/basic_features.json"),
        task_type=TASK_TYPE.BASIC_FEATURES,
        site_id=site["id"],
        units_ids=(UNIT_ID_1, UNIT_ID_2, UNIT_ID_3, UNIT_ID_4),
    )

    db_areas = sorted(
        db_areas, key=lambda x: wkt.loads(x["scaled_polygon"]).area, reverse=True
    )
    for apartment_no, _ in enumerate([UNIT_ID_1, UNIT_ID_2, UNIT_ID_3, UNIT_ID_4]):
        AreaHandler.update_relationship_with_units(
            plan_id=plan["id"],
            apartment_no=apartment_no,
            area_ids=[db_areas[apartment_no]["id"]],
        )

    return dict(
        site=site,
        building=building,
        plan=plan,
        floor=floor,
        units=units,
    )


@pytest.fixture
def potential_db_simulation_ch_sun_empty(zurich_location):
    from handlers.db import PotentialSimulationDBHandler

    return PotentialSimulationDBHandler.add(
        type=SIMULATION_TYPE.SUN,
        status=POTENTIAL_SIMULATION_STATUS.PROCESSING,
        result={},
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        building_footprint=Point(zurich_location["lon"], zurich_location["lat"]).buffer(
            0.01
        ),
        floor_number=zurich_location["floor_number"],
    )


@pytest.fixture
def site_with_full_slam_results_success(site):
    from handlers.db import SiteDBHandler

    return SiteDBHandler.update(
        item_pks=dict(id=site["id"]),
        new_values=dict(
            full_slam_results=ADMIN_SIM_STATUS.SUCCESS, heatmaps_qa_complete=True
        ),
    )


@pytest.fixture
def units_with_vector_with_balcony(site, plan, floor, floor2):
    from handlers.db import UnitDBHandler

    unit1_floor1 = UnitDBHandler.add(
        id=UNIT_ID_1,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=1,
        unit_type="3.5",
        client_id=CLIENT_ID_1,
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
    )
    unit1_floor2 = UnitDBHandler.add(
        id=UNIT_ID_2,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor2["id"],
        apartment_no=1,
        unit_type="3.5",
        client_id=CLIENT_ID_1,
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
    )
    unit2 = UnitDBHandler.add(
        id=UNIT_ID_3,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=2,
        unit_type="2.5",
        client_id=CLIENT_ID_2,
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
    )
    unit3 = UnitDBHandler.add(
        id=UNIT_ID_4,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=3,
        client_id=CLIENT_ID_5,
        unit_type="2.5",
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
    )
    return [unit1_floor1, unit1_floor2, unit2, unit3]


def _create_plans(make_sites, make_buildings, make_plans, client_db):
    site_a, site_b = make_sites(client_db, client_db)
    building_a, building_b = make_buildings(site_a, site_b)
    return make_plans(building_a, building_b)


@pytest.fixture
def unassigned_and_upwork_plan(
    make_sites, make_buildings, make_plans, client_db, annotations_box_data
):
    from handlers.db import SiteDBHandler

    context = create_user_context(USERS["TEAMLEADER"])

    plan_a, plan_b = _create_plans(make_sites, make_buildings, make_plans, client_db)
    SiteDBHandler.update(
        {"id": plan_a["site_id"]}, {"group_id": context["group"]["id"]}
    )
    _finish_annotations_method(
        plan_a,
        annotations=annotations_box_data,
        annotation_finished=False,
    )
    return plan_a, plan_b


@pytest.fixture
def simple_layout_2_spaces_4_areas():
    # Generate a trivial layout with 2 spaces and 2 areas each
    space1 = SimSpace(footprint=Polygon(([[0, 0], [0, 10], [10, 10], [10, 0]])))
    space2 = SimSpace(footprint=Polygon(([[11, 0], [11, 10], [21, 10], [21, 0]])))
    splitter = LineString([(0, 5), (50, 5)])  # Divide spaces by half
    for space in (space1, space2):
        for area, area_type in zip(
            split(space.footprint, splitter),
            [AreaType.KITCHEN, AreaType.BATHROOM],
        ):
            space.add_area(SimArea(footprint=area, area_type=area_type))
    return SimLayout(spaces={space1, space2})


@pytest.fixture
def areas_in_db(plan, annotations_finished):
    from handlers import AreaHandler

    AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])


@pytest.fixture
def site_1439(
    fixtures_path,
    client_db,
    login,
    site_region_proj_ch,
):
    from handlers.db import SiteDBHandler

    site = {
        "id": 1439,
        "name": "Site 1439",
        "region": "Region",
        "lat": 46.371598386,
        "lon": 8.172740161,
        "georef_region": "EPSG:2056",
        "client_site_id": "1439",
        "client_id": client_db["id"],
        "group_id": login["group"]["id"],
        "basic_features_status": ADMIN_SIM_STATUS.SUCCESS.value,
        "heatmaps_qa_complete": True,
        "pipeline_and_qa_complete": True,
        "full_slam_results": ADMIN_SIM_STATUS.SUCCESS.value,
        "simulation_version": random_simulation_version().value,
        **site_region_proj_ch,
    }
    return SiteDBHandler.add(**site)


@pytest.fixture
def site_834(
    make_classified_plans, site, plan, building, floor, fixtures_path, site_coordinates
):
    """
    This fixture is adding floor 7832 with all its units
    to the site,building,floor,plan fixtures
    """

    def create_units(plan_id, floor_fixture_id, site_id, floor_id):
        from handlers import AreaHandler
        from handlers.db import UnitDBHandler

        units = []

        with fixtures_path.joinpath(
            f"units_areas/unit_areas_floor_{floor_fixture_id}.json"
        ).open() as f:
            i = 1
            for unit_id, areas_ids in json.load(f).items():
                unit = UnitDBHandler.add(
                    id=unit_id,
                    plan_id=plan_id,
                    floor_id=floor_id,
                    site_id=site_id,
                    apartment_no=i,
                    unit_type=None,
                )
                AreaHandler.update_relationship_with_units(
                    plan_id=plan_id,
                    apartment_no=i,
                    area_ids=areas_ids,
                )
                units.append(unit)
                i += 1

        return units

    fixture_site_id = 834
    fixture_plan_id = 4976
    fixture_floor_id = 7832
    floor_number = 0

    plan_info = {
        "georef_scale": 7.42811211419092e-05,
        "georef_y": site_coordinates["lat"],
        "georef_rot_angle": 312.854498274469,
        "georef_rot_x": 2910.11813521304,
        "georef_rot_y": -2034.75128245626,
        "georef_x": site_coordinates["lon"],
    }

    building_info = {
        "housenumber": "6-8a",
        "street": "Random Street",
        "city": "Random City",
        "zipcode": "9999",
        "client_building_id": "Random building id",
    }

    from handlers.db import (
        BuildingDBHandler,
        FloorDBHandler,
        PlanDBHandler,
        QADBHandler,
    )

    FloorDBHandler.update(
        item_pks={"id": floor["id"]}, new_values={"floor_number": floor_number}
    )
    make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
    units = create_units(
        plan_id=plan["id"],
        floor_fixture_id=fixture_floor_id,
        site_id=site["id"],
        floor_id=floor["id"],
    )

    with fixtures_path.joinpath(f"qa_data/site_{fixture_site_id}.json").open(
        mode="r"
    ) as f:
        QADBHandler.add(
            site_id=site["id"], client_id=site["client_id"], data=json.load(f)
        )
    PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=plan_info)
    BuildingDBHandler.update(item_pks={"id": building["id"]}, new_values=building_info)
    manual_surroundings = ManualSurroundingsDBHandler.add(
        site_id=site["id"], surroundings={}
    )

    return {
        "site": site,
        "building": building,
        "floor": floor,
        "plan": plan,
        "units": units,
        "manual_surroundings": manual_surroundings,
    }


@pytest.fixture
def site_data(client_db, site_coordinates):
    return {
        "client_id": client_db["id"],
        "client_site_id": "wooohooo",
        **site_coordinates,
        "name": "Big-ass portfolio",
        "region": "Switzerland",
    }


@pytest.fixture
def make_triangles_site_1439_3d_building_gcs(fixtures_path):
    def _internal(buildings):
        """this should be generated only once during the execution of the test of this module.
        If the bucket gets regenerated in one test then this should be changed"""
        from handlers import BuildingHandler

        for building in buildings:
            building_id = building["id"]
            with ZipFile(
                fixtures_path.joinpath(f"dashboard/triangles_{building_id}.zip")
            ) as zip_file:
                with zip_file.open(f"triangles_{building_id}.json") as json_file:
                    triangles = json.load(json_file)

                    BuildingHandler(building_id=building_id)._upload_triangles_to_gcs(
                        triangles=triangles
                    )

    return _internal


@pytest.fixture
def site_1439_buildings(site_1439):
    from handlers.db import BuildingDBHandler

    buildings = [
        {
            "housenumber": "Number 1",
            "client_building_id": "Building 1",
            "city": "City",
            "elevation": 437.696807861328,
            "street": "Street",
            "id": 2656,
            "zipcode": "0001",
        },
        {
            "housenumber": "Number 2",
            "client_building_id": "Building 2",
            "city": "City",
            "elevation": 437.627014160156,
            "street": "Street",
            "id": 2659,
            "zipcode": "0001",
        },
    ]
    return [
        BuildingDBHandler.add(**building, site_id=site_1439["id"])
        for building in buildings
    ]


@pytest.fixture
def site_1439_simulated(
    site_1439, site_1439_buildings, fixtures_path, random_plain_floorplan_link
):
    """Fixtures generated out this code snippet:
    >>>import json
    >>>from handlers.db import UnitDBHandler

    >>>floor_ids = set()
    >>>units = list(UnitDBHandler.find_in(site_id=[1439, 1440]))
    >>>units = [
    >>>    {
    >>>        k: v
    >>>        for k, v in unit.items()
    >>>        if not k.startswith("gcs")
    >>>        and k
    >>>        not in {
    >>>            "full_vector_with_balcony",
    >>>            "unit_vector_no_balcony",
    >>>            "full_vector_no_balcony",
    >>>            "room_vector_no_balcony",
    >>>        }
    >>>    }
    >>>    for unit in units
    >>>]
    >>>new_units = []
    >>>for unit in units:
    >>>    if unit["client_id"] == "TR1.01" or unit["floor_id"] not in floor_ids:
    >>>        new_units.append(
    >>>            {
    >>>                k: {
    >>>                    sub_k: [round(x, 2) for x in sub_v]
    >>>                    if sub_k != "observation_points"
    >>>                    else [[round(x, 5) for x in sub_l] for sub_l in sub_v]
    >>>                    for sub_k, sub_v in unit[k].items()
    >>>                }
    >>>                if k == "raw_results_view_sun"
    >>>                else v
    >>>                for k, v in unit.items()
    >>>            }
    >>>        )
    >>>        floor_ids.add(unit["floor_id"])
    >>>with open("tests/fixtures/dashboard/units.json", "w") as f:
    >>>    json.dump(new_units, f)

    To get the simulations updated:
    >>> unit_ids = [61584,
    >>>  61588,
    >>>  61592,
    >>>  61596,
    >>>  61599,
    >>>  61603,
    >>>  61607,
    >>>  61611,
    >>>  61615,
    >>>  61619,
    >>>  61713,
    >>>  61719,
    >>>  61728,
    >>>  61737,
    >>>  61746,
    >>>  61755]

    # The order of the run ids is relevant because they are order by the same type as we need to replace it.
    # Everything needs to be mapped as if it was only 1 site, 1439
    >>> run_ids_site_1439 = [
    >>>  'dbc190f9-29e1-4653-9b47-31812e8fb23e',
    >>>  'f8a98bfa-856e-41fd-90fb-2ba62645f654',
    >>>  '1a97ce23-ac02-4686-86d7-1537b60d7590'
    >>> ]
    >>> run_ids_site_1440 = [
    >>>  '2119cf4a-6866-48cc-9447-035e1883e53e',
    >>>  '4ab9b94f-6066-4288-a696-72c118d76b9a',
    >>>  '7f6acf46-74b7-43cf-ab16-80cfc11b0d2d'
    >>> ]

    # Here you have to get the latest run_ids for the sites 1440 and 1439 for at least ViewSUN, sunv2 and
    # basic features.
    >>> from handlers.db import UnitSimulationDBHandler, SlamSimulationDBHandler, UnitAreaStatsDBHandler
    >>> import json
    >>> for name, db_handler in {
    >>>    "slam_unit_simulations": UnitSimulationDBHandler,
    >>>    "unit_area_stats": UnitAreaStatsDBHandler,
    >>> }.items():
    >>>    res = list(db_handler.find_in(run_id=run_ids_site_1439 + run_ids_site_1440))
    >>>    res = [us for us in res if us["unit_id"] in unit_ids]
    >>>    for re in res:
    >>>        if re["run_id"] in run_ids_site_1440:
    >>>            re["run_id"] = run_ids_site_1439[run_ids_site_1440.index(re["run_id"])]
    >>>    with open(f"tests/fixtures/dashboard/site_1439_fixture/{name}.json", "w") as f:
    >>>        json.dump(res, f)

    >>> slam_unit_simulations = list(SlamSimulationDBHandler.find_in(run_id=run_ids_site_1439))
    >>> with open(f"tests/fixtures/dashboard/site_1439_fixture/slam_simulations.json", "w") as f:
    >>>     json.dump(slam_unit_simulations, f)
    """
    from handlers import AreaHandler
    from handlers.db import (
        AreaDBHandler,
        FloorDBHandler,
        PlanDBHandler,
        ReactPlannerProjectsDBHandler,
        SlamSimulationDBHandler,
        UnitAreaDBHandler,
        UnitAreaStatsDBHandler,
        UnitDBHandler,
        UnitSimulationDBHandler,
    )

    result_entities = {
        "site": site_1439,
        "building": site_1439_buildings,
    }
    zip_files_handler = (
        ("plans", PlanDBHandler, {"image_gcs_link": random_plain_floorplan_link}),
        ("annotations", ReactPlannerProjectsDBHandler, {}),
        ("areas", AreaDBHandler, {}),
        ("floors", FloorDBHandler, {}),
        ("units", UnitDBHandler, {}),
        ("unit_areas", UnitAreaDBHandler, {}),
        ("slam_simulations", SlamSimulationDBHandler, {}),
        ("slam_unit_simulations", UnitSimulationDBHandler, {}),
        ("unit_area_stats", UnitAreaStatsDBHandler, {}),
    )
    fixture_folder = "dashboard/site_1439_fixture"
    for entity_name, handler, additional_fields in zip_files_handler:
        zip_path = fixtures_path.joinpath(f"{fixture_folder}/{entity_name}.zip")
        if zip_path.exists():
            with ZipFile(zip_path) as zip_file, zip_file.open(
                f"{entity_name}.json"
            ) as json_file:
                new_items = [
                    {**entity, **additional_fields}
                    for entity in json.loads(json_file.read())
                ]
                result_entities[entity_name] = new_items
                handler.bulk_insert(items=new_items)
    for plan in result_entities["plans"]:
        AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])
    return result_entities


@pytest.fixture
def first_unit_site_1439(site_1439_simulated):
    return site_1439_simulated["units"][0]


@pytest.fixture
def add_unit_same_id_floor_1_site_1439(first_unit_site_1439):
    from handlers.db import UnitAreaDBHandler, UnitDBHandler

    new_unit = UnitDBHandler.add(
        site_id=first_unit_site_1439["site_id"],
        plan_id=first_unit_site_1439["plan_id"],
        floor_id=first_unit_site_1439["floor_id"],
        client_id=first_unit_site_1439["client_id"],
        apartment_no=first_unit_site_1439["apartment_no"] + 1,
    )
    unit_areas_to_insert = [
        {"unit_id": new_unit["id"], "area_id": area_id}
        for area_id in [
            650177,
            650157,
            650160,
            650147,
            650148,
            650143,
            650144,
            650186,
            650153,
        ]
    ]
    UnitAreaDBHandler.bulk_insert(items=unit_areas_to_insert)


@pytest.fixture
def triangles_site_1439_3d_building_gcs_2(
    site_1439_simulated, make_triangles_site_1439_3d_building_gcs
):
    """this should be generated only once during the execution of the test of this module.
    If the bucket get's regenerated in one test then this should be changed"""
    make_triangles_site_1439_3d_building_gcs(site_1439_simulated["building"])


@pytest.fixture
def triangles_site_1439_3d_building_gcs(
    site_1439_simulated, make_triangles_site_1439_3d_building_gcs
):
    """this should be generated only once during the execution of the test of this module.
    If the bucket get's regenerated in one test then this should be changed"""
    make_triangles_site_1439_3d_building_gcs(site_1439_simulated["building"])


@pytest.fixture
def plans_ready_for_georeferencing(
    site, building, make_plans, make_classified_plans, make_floor, annotation_plan_1478
):
    from brooks.util.projections import project_geometry
    from handlers import PlanHandler
    from handlers.db import PlanDBHandler, SiteDBHandler
    from surroundings.constants import REGION

    georef_scale = annotation_plan_1478["scale"] * SI_UNIT_BY_NAME["cm"].value ** 2
    site_lat_lon_location = project_geometry(
        Point(2614896.8, 1268188.6), crs_from=REGION.CH, crs_to=REGION.LAT_LON
    )

    SiteDBHandler.update(
        item_pks=dict(id=site["id"]),
        new_values=dict(lon=site_lat_lon_location.x, lat=site_lat_lon_location.y),
    )

    plan_to_georeference = make_plans(building)[0]
    make_classified_plans(
        plan_to_georeference, db_fixture_ids=False, annotations_plan_id=1478
    )
    make_floor(building=building, plan=plan_to_georeference, floornumber=1)
    PlanHandler(plan_id=plan_to_georeference["id"]).update_rotation_point()
    PlanDBHandler.update(
        item_pks=dict(id=plan_to_georeference["id"]),
        new_values=dict(
            georef_scale=georef_scale,
            annotation_finished=True,
        ),
    )

    already_georeferenced_plan = make_plans(building)[0]
    make_floor(building=building, plan=already_georeferenced_plan, floornumber=0)
    make_classified_plans(
        already_georeferenced_plan, db_fixture_ids=False, annotations_plan_id=1478
    )

    PlanHandler(plan_id=already_georeferenced_plan["id"]).update_rotation_point()
    PlanDBHandler.update(
        item_pks=dict(id=already_georeferenced_plan["id"]),
        new_values=dict(
            georef_x=site_lat_lon_location.x + 0.0001,  # 11 meters
            georef_y=site_lat_lon_location.y + 0.0001,
            georef_scale=georef_scale,
            georef_rot_angle=30.0,
        ),
    )
    return plan_to_georeference, already_georeferenced_plan


@pytest.fixture
def heavy_plan_layout(plan, heavy_annotations) -> SimLayout:
    from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper

    return ReactPlannerToBrooksMapper.get_layout(
        planner_elements=heavy_annotations, scaled=True
    )


@pytest.fixture
def make_areas_from_layout():
    from handlers.db import AreaDBHandler

    def _make_areas_from_layout(layout, plan_id):
        for area in db_areas_from_layout(layout=layout, plan_id=plan_id):
            AreaDBHandler.add(**area)

    return _make_areas_from_layout


@pytest.fixture
def pending_simulation(site):
    from handlers import SlamSimulationHandler

    return SlamSimulationHandler.register_simulation(
        site_id=site["id"], run_id=str(uuid.uuid4()), task_type=TASK_TYPE.VIEW_SUN
    )


@pytest.fixture
def basic_features_finished(site):
    from handlers import SlamSimulationHandler
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site["id"]),
        new_values={"basic_features_status": ADMIN_SIM_STATUS.SUCCESS.name},
    )

    return SlamSimulationHandler.register_simulation(
        site_id=site["id"],
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.BASIC_FEATURES,
        state=ADMIN_SIM_STATUS.SUCCESS,
    )


@pytest.fixture
def qa_report_mock(mocker, site, basic_features_finished):
    from handlers import SlamSimulationHandler
    from handlers.db import UnitDBHandler

    unit_id_1 = 4554
    unit_id_2 = 342544
    client_id_1 = "2215391.01.01.0001"
    client_id_2 = "2215391.01.01.0002"
    client_id_3 = "2215391.01.01.0003"
    client_data = {
        client_id_1: dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{INDEX_ROOM_NUMBER: 4.5, INDEX_HNF_AREA: 68.75, INDEX_ANF_AREA: 66.0},
        ),
        client_id_2: dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{INDEX_ROOM_NUMBER: 1.5, INDEX_HNF_AREA: 30.3, INDEX_ANF_AREA: 3.0},
        ),
        client_id_3: dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{INDEX_ROOM_NUMBER: 2.5, INDEX_HNF_AREA: 47.0, INDEX_ANF_AREA: 14.0},
        ),
    }

    units_info = [
        {"id": unit_id_1, "client_id": client_id_1},
        {"id": unit_id_2, "client_id": client_id_2},
    ]
    mocker.patch.object(
        UnitDBHandler, UnitDBHandler.find.__name__, return_value=units_info
    )

    simulation_results = [
        {
            "unit_id": unit_id_1,
            "results": [
                {
                    DB_INDEX_ROOM_NUMBER: client_data[client_id_1][INDEX_ROOM_NUMBER],
                    DB_INDEX_NET_AREA: client_data[client_id_1][INDEX_HNF_AREA],
                    DB_INDEX_HNF: client_data[client_id_1][INDEX_HNF_AREA],
                    DB_INDEX_ANF: client_data[client_id_1][INDEX_ANF_AREA],
                    DB_INDEX_VF: 0.0,
                    DB_INDEX_FF: 0.0,
                    DB_INDEX_NNF: 0.0,
                }
            ],
        },
        {
            "unit_id": unit_id_2,
            "results": [
                {
                    DB_INDEX_ROOM_NUMBER: client_data[client_id_2][INDEX_ROOM_NUMBER],
                    DB_INDEX_NET_AREA: client_data[client_id_2][INDEX_HNF_AREA],
                    DB_INDEX_HNF: client_data[client_id_2][INDEX_HNF_AREA],
                    DB_INDEX_ANF: client_data[client_id_2][INDEX_ANF_AREA],
                    DB_INDEX_VF: 10.0,
                    DB_INDEX_FF: 5.0,
                    DB_INDEX_NNF: 20.0,
                }
            ],
        },
    ]

    mocker.patch.object(
        SlamSimulationHandler,
        SlamSimulationHandler.get_all_results.__name__,
        return_value=simulation_results,
    )
    return {
        "client_unit_ids": {
            "client_id_1": client_id_1,
            "client_id_2": client_id_2,
            "client_id_3": client_id_3,
        },
        "qa_data": client_data,
    }


@pytest.fixture
def view_sun_simulation_finished(site):
    from handlers import SlamSimulationHandler

    return SlamSimulationHandler.register_simulation(
        site_id=site["id"],
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.VIEW_SUN,
        state=ADMIN_SIM_STATUS.SUCCESS,
    )


@pytest.fixture
def basic_features_started(site):
    from handlers import SlamSimulationHandler
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site["id"]),
        new_values={"basic_features_status": ADMIN_SIM_STATUS.PROCESSING.name},
    )

    return SlamSimulationHandler.register_simulation(
        site_id=site["id"],
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.BASIC_FEATURES,
        state=ADMIN_SIM_STATUS.PROCESSING,
    )


@pytest.fixture
def expected_aggregated_units():
    sun_dimensions_and_labels = {
        "03": [
            ("sun-2018-03-21 18:00:00+01:00", "18:00:00"),
            ("sun-2018-03-21 16:00:00+01:00", "16:00:00"),
            ("sun-2018-03-21 14:00:00+01:00", "14:00:00"),
            ("sun-2018-03-21 12:00:00+01:00", "12:00:00"),
            ("sun-2018-03-21 10:00:00+01:00", "10:00:00"),
            ("sun-2018-03-21 08:00:00+01:00", "08:00:00"),
        ],
        "06": [
            ("sun-2018-06-21 20:00:00+02:00", "20:00:00"),
            ("sun-2018-06-21 18:00:00+02:00", "18:00:00"),
            ("sun-2018-06-21 16:00:00+02:00", "16:00:00"),
            ("sun-2018-06-21 14:00:00+02:00", "14:00:00"),
            ("sun-2018-06-21 12:00:00+02:00", "12:00:00"),
            ("sun-2018-06-21 10:00:00+02:00", "10:00:00"),
            ("sun-2018-06-21 08:00:00+02:00", "08:00:00"),
            ("sun-2018-06-21 06:00:00+02:00", "06:00:00"),
        ],
        "12": [
            ("sun-2018-12-21 16:00:00+01:00", "16:00:00"),
            ("sun-2018-12-21 14:00:00+01:00", "14:00:00"),
            ("sun-2018-12-21 12:00:00+01:00", "12:00:00"),
            ("sun-2018-12-21 10:00:00+01:00", "10:00:00"),
        ],
    }
    sun_info_by_floor = defaultdict(lambda: defaultdict(list))
    for month, dimensions_and_labels in sun_dimensions_and_labels.items():
        for dimension, label in dimensions_and_labels:
            sun_info_by_floor[1][month].append(
                {
                    "dimension": dimension,
                    "label": label,
                    "value": 1.6666666666666667,
                }
            )
            sun_info_by_floor[2][month].append(
                {
                    "dimension": dimension,
                    "label": label,
                    "value": 1.0,
                }
            )

    return {
        1: {
            "sun_info": sun_info_by_floor[1],
            "view_info": [
                {
                    "label": "Sky",
                    "dimension": "sky",
                    "mean": 1.6666666666666667,
                    "min": 0,
                    "max": 3,
                },
                {
                    "label": "Water",
                    "dimension": "water",
                    "mean": 1.6666666666666667,
                    "min": 0,
                    "max": 3,
                },
                {
                    "label": "Streets",
                    "dimension": "streets",
                    "mean": 1.6666666666666667,
                    "min": 0,
                    "max": 3,
                },
                {
                    "label": "Greenery",
                    "dimension": "greenery",
                    "mean": 1.6666666666666667,
                    "min": 0,
                    "max": 3,
                },
            ],
            "unit_types": ["3.5", "2.5", "2.5"],
            "net_area": 6,
            "price": 900.0,
            "client_unit_ids": [CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3],
            "performance": 0.5,
            "number_of_units": 3,
        },
        2: {
            "sun_info": sun_info_by_floor[2],
            "view_info": [
                {
                    "label": "Sky",
                    "dimension": "sky",
                    "mean": 1.0,
                    "min": 1.0,
                    "max": 1.0,
                },
                {
                    "label": "Water",
                    "dimension": "water",
                    "mean": 1.0,
                    "min": 1.0,
                    "max": 1.0,
                },
                {
                    "label": "Streets",
                    "dimension": "streets",
                    "mean": 1.0,
                    "min": 1.0,
                    "max": 1.0,
                },
                {
                    "label": "Greenery",
                    "dimension": "greenery",
                    "mean": 1.0,
                    "min": 1.0,
                    "max": 1.0,
                },
            ],
            "unit_types": ["3.5"],
            "net_area": 1,
            "price": 150.0,
            "client_unit_ids": [CLIENT_ID_1],
            "performance": 0.5,
            "number_of_units": 1,
        },
    }


@pytest.fixture
def areas_accessible_areas(annotations_accessible_areas, plan):
    from handlers import AreaHandler
    from handlers.db import ReactPlannerProjectsDBHandler
    from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper

    ReactPlannerProjectsDBHandler.add(
        plan_id=plan["id"], data=annotations_accessible_areas
    )
    brooks_model = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_accessible_areas)
    )
    AreaHandler.recover_and_upsert_areas(plan_id=plan["id"], plan_layout=brooks_model)


@pytest.fixture
def site_with_3_units(
    site, building, plan, make_floor, make_classified_split_plans, site_coordinates
):
    from handlers.db import (
        AreaDBHandler,
        BuildingDBHandler,
        FloorDBHandler,
        PlanDBHandler,
        UnitAreaDBHandler,
        UnitDBHandler,
    )

    # recreate hierarchy for a sample plan
    make_classified_split_plans(
        plan, annotations_plan_id=5825, floor_number=1, building=building
    )
    PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values={
            "georef_x": site_coordinates["lon"],
            "georef_y": site_coordinates["lat"],
            "georef_rot_x": 619.908070026149,
            "georef_rot_y": -377.449287221441,
            "georef_rot_angle": 219.115103841475,
        },
    )
    units = UnitDBHandler.find(plan_id=plan["id"])

    # In order to add some deterministic state to the units, we will add a client_id based on their position
    areas_x = {a["id"]: a["coord_x"] for a in AreaDBHandler.find()}

    unit_areas = {}
    for unit in units:
        unit_areas[unit["id"]] = max(
            [
                areas_x[unit_area["area_id"]]
                for unit_area in UnitAreaDBHandler.find_in(
                    unit_id=[unit["id"]],
                    output_columns=["area_id"],
                )
            ]
        )

    for unit_id, max_x in unit_areas.items():
        UnitDBHandler.update(
            item_pks={"id": unit_id}, new_values={"client_id": str(max_x)}
        )
    return {
        "site": site,
        "building": BuildingDBHandler.find()[0],
        "plan": PlanDBHandler.find()[0],
        "floor": FloorDBHandler.find()[0],
        "units": UnitDBHandler.find(),
        "areas": AreaDBHandler.find(),
    }


@pytest.fixture
def plan_7641_classified(
    make_classified_plans, populate_plan_areas_db, plan, site_coordinates
):
    from handlers.db import PlanDBHandler

    fixture_plan_id = 7641
    make_classified_plans(plan, annotations_plan_id=fixture_plan_id)
    return PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values={
            "georef_y": site_coordinates["lat"],
            "georef_rot_angle": 78.8484917824914,
            "georef_rot_x": 2383.69635750003,
            "georef_rot_y": -1057.29354085503,
            "georef_x": site_coordinates["lon"],
            "georef_scale": 7.12961037842059e-05,
        },
    )


@pytest.fixture
def site_with_1_unit(site_with_3_units):
    from handlers.db import UnitDBHandler

    units = sorted(
        UnitDBHandler.find(plan_id=site_with_3_units["plan"]["id"]),
        key=itemgetter("client_id"),
    )
    UnitDBHandler.delete_in(id=[x["id"] for x in units[1:]])

    site_with_3_units["units"] = [units[0]]
    return site_with_3_units


@pytest.fixture
def fake_competitions(
    client_db,
    make_sites,
    competition_configuration,
):

    from handlers.db import CompetitionDBHandler

    COMPETITIONS_TO_CREATE = [
        "Architekturwettbewerb Küngenmatt",
        "Architekturwettbewerb of Payasos",
        "Architekturwettbewerb of Kartoffen",
        "Architekturwettbewerb of Mojo",
    ]

    site_1, site_2 = make_sites(
        client_db,
        client_db,
        get_name=lambda client, index: client["name"] + str(index),
    )
    return [
        CompetitionDBHandler.add(
            competitors=[site_1["id"], site_2["id"]],
            name=name,
            client_id=client_db["id"],
            weights={
                "architecture_usage": 0.27,
                "architecture_room_programme": 0.38,
                "environmental": 0.2,
                "further_key_figures": 0.15,
            },
            configuration_parameters=competition_configuration,
        )
        for name in COMPETITIONS_TO_CREATE
    ]


@pytest.fixture
def competition_with_fake_feature_values(
    client_db,
    make_sites,
    expected_competition_features_site_1,
    expected_competition_features_site_2,
    competition_configuration,
    fixtures_path,
    random_plain_floorplan_link,
):
    from handlers.db import (
        CompetitionDBHandler,
        CompetitionFeaturesDBHandler,
        SlamSimulationDBHandler,
    )

    run_id_1 = str(uuid.uuid4())
    run_id_2 = str(uuid.uuid4())
    site_1, site_2 = make_sites(
        client_db, client_db, get_name=lambda client, index: client["name"] + str(index)
    )
    prepare_for_competition(
        site_id=site_1["id"],
        fixtures_path=fixtures_path.joinpath("competition"),
        random_plain_floorplan_link=random_plain_floorplan_link,
    )
    prepare_for_competition(
        site_id=site_2["id"],
        fixtures_path=fixtures_path.joinpath("competition"),
        random_plain_floorplan_link=random_plain_floorplan_link,
    )
    SlamSimulationDBHandler.add(
        site_id=site_1["id"],
        run_id=run_id_1,
        type=TASK_TYPE.COMPETITION.name,
        state=ADMIN_SIM_STATUS.SUCCESS.name,
    )
    SlamSimulationDBHandler.add(
        site_id=site_2["id"],
        run_id=run_id_2,
        type=TASK_TYPE.COMPETITION.name,
        state=ADMIN_SIM_STATUS.SUCCESS.name,
    )
    CompetitionFeaturesDBHandler.add(
        run_id=run_id_1, results=expected_competition_features_site_1
    )
    CompetitionFeaturesDBHandler.add(
        run_id=run_id_2, results=expected_competition_features_site_2
    )
    return CompetitionDBHandler.add(
        competitors=[site_1["id"], site_2["id"]],
        name="Architekturwettbewerb Küngenmatt",
        client_id=client_db["id"],
        weights={
            "architecture_usage": 0.27,
            "architecture_room_programme": 0.38,
            "environmental": 0.2,
            "further_key_figures": 0.15,
        },
        configuration_parameters=competition_configuration,
        red_flags_enabled=True,
    )


@pytest.fixture
def competition_with_fake_feature_values_selected_features(
    competition_with_fake_feature_values,
):
    from handlers.db import CompetitionDBHandler

    removed_features = {
        CompetitionFeatures.NOISE_STRUCTURAL,
        CompetitionFeatures.NOISE_INSULATED_ROOMS,
    }
    features_selected = [f for f in CompetitionFeatures if f not in removed_features]
    return CompetitionDBHandler.update(
        item_pks={"id": competition_with_fake_feature_values["id"]},
        new_values={"features_selected": features_selected},
    )


@pytest.fixture
def competition_first_client_features_input(
    competition_with_fake_feature_values, overwritten_client_features
):
    from handlers.db.competition.competition_client_input import (
        CompetitionManualInputDBHandler,
    )

    return CompetitionManualInputDBHandler.add(
        competitor_id=competition_with_fake_feature_values["competitors"][0],
        competition_id=competition_with_fake_feature_values["id"],
        features=overwritten_client_features,
    )


@pytest.fixture
def slam_simulation_with_results(
    view_sun_simulation_finished, plan_classified_scaled, unit
):
    from handlers.db import AreaDBHandler, UnitAreaDBHandler, UnitSimulationDBHandler

    areas = sorted(
        AreaDBHandler.find(plan_id=plan_classified_scaled["id"]),
        key=lambda row: row["id"],
    )[0:2]
    UnitAreaDBHandler.bulk_insert(
        [{"unit_id": unit["id"], "area_id": area["id"]} for area in areas]
    )
    AreaDBHandler.update(
        item_pks=dict(id=areas[1]["id"]),
        new_values={"area_type": AreaType.BALCONY.name},
    )
    UnitSimulationDBHandler.bulk_insert(
        [
            dict(
                unit_id=unit["id"],
                run_id=view_sun_simulation_finished["run_id"],
                results=fake_unit_simulation_results(
                    area_id_1=areas[0]["id"],
                    area_id_2=areas[1]["id"],
                ),
            )
        ]
    )
    return view_sun_simulation_finished, areas


@pytest.fixture
def insert_react_planner_data(react_planner_background_image_one_unit, plan):
    from handlers.db import ReactPlannerProjectsDBHandler

    return ReactPlannerProjectsDBHandler.add(
        plan_id=plan["id"],
        data=react_planner_background_image_one_unit,
    )


@pytest.fixture
def units_db(site, plan, floor, floor2):
    from handlers.db import UnitDBHandler

    unit1_floor1 = UnitDBHandler.add(
        id=UNIT_ID_1,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=1,
        unit_type="3.5",
        client_id=CLIENT_ID_1,
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
        ph_final_sale_price_adj_factor=2,
        ph_final_sale_price_m2=100000.00,
        representative_unit_client_id=CLIENT_ID_1,
    )
    unit1_floor2 = UnitDBHandler.add(
        id=UNIT_ID_2,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor2["id"],
        apartment_no=1,
        unit_type="3.5",
        client_id=CLIENT_ID_1,
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
        ph_final_sale_price_adj_factor=2,
        ph_final_sale_price_m2=100000.00,
        representative_unit_client_id=CLIENT_ID_1,
    )
    unit2 = UnitDBHandler.add(
        id=UNIT_ID_3,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=2,
        unit_type="2.5",
        client_id=CLIENT_ID_2,
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
        ph_final_sale_price_adj_factor=2,
        ph_final_sale_price_m2=100000.00,
        representative_unit_client_id=CLIENT_ID_1,
    )
    unit3 = UnitDBHandler.add(
        id=UNIT_ID_4,
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=3,
        client_id=CLIENT_ID_3,
        unit_type="2.5",
        ph_final_gross_rent_adj_factor=1,
        ph_final_gross_rent_annual_m2=1000.00,
        ph_final_sale_price_adj_factor=2,
        ph_final_sale_price_m2=100000.00,
        representative_unit_client_id=CLIENT_ID_1,
    )
    return [unit1_floor1, unit1_floor2, unit2, unit3]


@pytest.fixture
def unit_areas_db(units_db, areas_db):
    from handlers.db import UnitAreaDBHandler

    unit_areas = [
        {"unit_id": unit["id"], "area_id": area["id"]}
        for unit in units_db
        for area in areas_db
    ]
    UnitAreaDBHandler.bulk_insert(unit_areas)

    return unit_areas


@pytest.fixture
def non_residential_units(site, floor):
    from handlers.db import UnitDBHandler

    units = []
    for apartment_number, (client_unit_id, unit_usage) in enumerate(
        [
            ("Janitor_Office", UNIT_USAGE.JANITOR),
            ("Gewerbe_Office", UNIT_USAGE.COMMERCIAL),
            ("placeholder", UNIT_USAGE.PLACEHOLDER),
        ],
        start=999,
    ):
        units.append(
            UnitDBHandler.add(
                site_id=site["id"],
                client_id=client_unit_id,
                floor_id=floor["id"],
                unit_usage=unit_usage.name,
                apartment_no=apartment_number,
                plan_id=floor["plan_id"],
            )
        )
    return units


@pytest.fixture
def gereferenced_annotation_for_plan_5797(
    annotation_plan_5797, floor, plan, georef_plan_values
):
    from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler

    # This generates an area of 1 meter
    ReactPlannerProjectsDBHandler.add(plan_id=plan["id"], data=annotation_plan_5797)
    PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values=georef_plan_values[5797],
    )


@pytest.fixture
def two_potential_simulations_success_and_failed(zurich_location):
    from handlers.db import PotentialSimulationDBHandler

    building_footprint = Point(zurich_location["lon"], zurich_location["lat"]).buffer(
        0.01
    )
    PotentialSimulationDBHandler.add(
        type=SIMULATION_TYPE.SUN,
        status=POTENTIAL_SIMULATION_STATUS.FAILURE,
        result={},
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        building_footprint=building_footprint,
        floor_number=zurich_location["floor_number"],
    )
    PotentialSimulationDBHandler.add(
        type=SIMULATION_TYPE.VIEW,
        status=POTENTIAL_SIMULATION_STATUS.SUCCESS,
        result={},
        region=REGION.CH.name,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
        building_footprint=building_footprint,
        floor_number=zurich_location["floor_number"] + 1,
    )


@pytest.fixture(params=[SIMULATION_VERSION.PH_01_2021, SIMULATION_VERSION.EXPERIMENTAL])
def site_with_simulation_results(request, site, plan_classified_scaled, unit) -> Dict:
    from handlers import SlamSimulationHandler
    from handlers.db import (
        AreaDBHandler,
        SiteDBHandler,
        SlamSimulationDBHandler,
        UnitAreaDBHandler,
    )

    sim_version = request.param
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"simulation_version": sim_version.value},
    )
    site["simulation_version"] = sim_version.value

    areas = sorted(
        AreaDBHandler.find(plan_id=plan_classified_scaled["id"]),
        key=lambda a: wkt.loads(a["scaled_polygon"]).area,
    )
    AreaDBHandler.bulk_update(
        area_type={a["id"]: AreaType.BALCONY.name for a in areas[:2]}
    )
    UnitAreaDBHandler.bulk_insert(
        [dict(unit_id=unit["id"], area_id=area["id"]) for area in areas]
    )

    # Basic Features
    basic_features_run_id = "my-fake-basic-features-id"
    SlamSimulationDBHandler.add(
        run_id=basic_features_run_id,
        site_id=site["id"],
        type=TASK_TYPE.BASIC_FEATURES.name,
        state=ADMIN_SIM_STATUS.SUCCESS.name,
    )
    SlamSimulationHandler.store_results(
        run_id=basic_features_run_id, results={unit["id"]: [{"FakeBasicFeature": 1}]}
    )

    sun_v2_dimensions = {
        SuntimesHandler.get_sun_key_from_datetime(dt=sun_obs_date)
        for sun_obs_date in SuntimesHandler.get_sun_times_v2(site_id=site["id"])
    }
    if sim_version == SIMULATION_VERSION.PH_01_2021:
        view_sun_dimensions = {
            dimension.value for dimension in chain(VIEW_DIMENSION, SUN_DIMENSION)
        }
    else:
        view_sun_dimensions = {
            dimension.value for dimension in chain(VIEW_DIMENSION_2, SUN_DIMENSION)
        }

    for task_type, run_id, dimensions in [
        (
            TASK_TYPE.SUN_V2.name,
            "my-fake-sun-id",
            sun_v2_dimensions,
        ),
        (
            TASK_TYPE.VIEW_SUN.name,
            "my-fake-view-sun-id",
            view_sun_dimensions,
        ),
        (
            TASK_TYPE.NOISE.name,
            "my-fake-noise-id",
            {n.value for n in NOISE_SURROUNDING_TYPE},
        ),
        (
            TASK_TYPE.NOISE_WINDOWS.name,
            "my-fake-noise-widows-id",
            {n.value for n in NOISE_SURROUNDING_TYPE},
        ),
        (
            TASK_TYPE.BIGGEST_RECTANGLE.name,
            "my-fake-biggest-rectangle-id",
            None,
        ),
        (
            TASK_TYPE.CONNECTIVITY.name,
            "my-fake-conn-id",
            # Removing eigen_centrality to test the optional dimensions
            CONNECTIVITY_DIMENSIONS - {"eigen_centrality"},
        ),
    ]:
        SlamSimulationDBHandler.add(
            run_id=run_id,
            site_id=site["id"],
            type=task_type,
            state=ADMIN_SIM_STATUS.SUCCESS.name,
        )
        if task_type == TASK_TYPE.BIGGEST_RECTANGLE.name:
            fake_area_sim_results = {area["id"]: box(0, 0, 1, 1).wkt for area in areas}
        else:
            fake_area_sim_results = {
                area["id"]: {
                    "observation_points": [[1, 1, 1], [2, 2, 1], [3, 3, 1]],
                    **{dimension: [1, 2, 3] for dimension in dimensions},
                }
                for area in areas
            }

        SlamSimulationHandler.store_results(
            run_id=run_id, results={unit["id"]: fake_area_sim_results}
        )

    return site


@pytest.fixture()
def heavy_annotations(plan, annotations_plan_3213_heavy):
    """Plan 3213 pulled the 10/05/2020 and modified 2 staircases that were invalid with the new restrictions"""
    from handlers.db import ReactPlannerProjectsDBHandler

    ReactPlannerProjectsDBHandler.add(
        plan_id=plan["id"], data=annotations_plan_3213_heavy
    )
    return annotations_plan_3213_heavy


@pytest.fixture
def prepare_plans_for_basic_features_or_qa(unit):
    def _internal(plan_id: int, annotations_data, area_type=None):
        ReactPlannerProjectsDBHandler.add(
            plan_id=plan_id,
            data=annotations_data,
        )
        AreaHandler.recover_and_upsert_areas(plan_id=plan_id)
        area_ids = list(AreaDBHandler.find_ids(plan_id=plan_id))
        AreaHandler.update_relationship_with_units(
            plan_id=plan_id,
            area_ids=area_ids,
            apartment_no=unit["apartment_no"],
        )
        if area_type:
            AreaDBHandler.bulk_update(
                area_type={
                    area_id: area_type.name
                    for area_id in AreaDBHandler.find_ids(plan_id=plan_id)
                },
            )

    return _internal
