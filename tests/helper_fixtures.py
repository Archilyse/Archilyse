import json
import math
import mimetypes
import uuid
from itertools import cycle
from pathlib import Path
from typing import Collection, Dict, List, Optional, Type

import pytest
from contexttimer import timer
from shapely.geometry import Polygon

from brooks.types import AreaType
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_BUILDING_SURROUNDINGS,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS,
    NOISE_SURROUNDING_TYPE,
    SUN_DIMENSION,
    TASK_TYPE,
    VIEW_DIMENSION,
)
from common_utils.logger import logger
from handlers import PlanLayoutHandler, SiteHandler, SlamSimulationHandler, StatsHandler
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    FolderDBHandler,
    PlanDBHandler,
    PotentialSimulationDBHandler,
    QADBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
    UnitSimulationDBHandler,
    UserDBHandler,
)
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from simulations.suntimes.suntimes_handler import SuntimesHandler
from slam_api.utils import get_entities
from surroundings.v2.base import BaseSurroundingHandler
from tasks.deliverables_tasks import task_site_zip_deliverable
from tests.constants import USERS
from tests.db_fixtures import create_user_context
from tests.utils import (
    add_plan_image_to_gcs,
    load_plan_helper,
    recreate_test_gcp_client_bucket_method,
)


@pytest.fixture
@timer(logger=logger)
def recreate_test_gcp_bucket():
    from handlers import GCloudStorageHandler

    GCloudStorageHandler().delete_bucket_if_exists(bucket_name=GOOGLE_CLOUD_BUCKET)
    GCloudStorageHandler().create_bucket_if_not_exists(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        location=GOOGLE_CLOUD_LOCATION,
        predefined_acl="public-read",
        predefined_default_object_acl="public-read",
    )


@pytest.fixture
@timer(logger=logger)
def recreate_test_gcp_client_bucket(client_db):
    recreate_test_gcp_client_bucket_method(client_id=client_db["id"])


@pytest.fixture
def make_clients(random_text):
    def _make(quantity: int = 1):
        return [ClientDBHandler.add(name=random_text()) for _ in range(quantity)]

    return _make


@pytest.fixture
def make_sites(
    site_coordinates,
    random_text,
    site_region_proj_ch,
):
    def _make(
        *clients,
        priority=1,
        client_site_id=None,
        group_id=None,
        full_slam_results=ADMIN_SIM_STATUS.UNPROCESSED,
        delivered=False,
        get_name=None,
    ):

        return [
            SiteDBHandler.add(
                client_id=client["id"],
                name=get_name(client, index) if get_name else random_text(),
                region="Switzerland",
                priority=priority,
                client_site_id=client_site_id or random_text(),
                group_id=group_id,
                full_slam_results=full_slam_results,
                delivered=delivered,
                **site_region_proj_ch,
                **site_coordinates,
            )
            for index, client in enumerate(clients)
        ]

    return _make


@pytest.fixture
def make_qa_data(qa_rows):
    def _make(*sites):
        return [
            QADBHandler.add(
                client_id=site["client_id"],
                client_site_id=site["client_site_id"],
                site_id=site["id"],
                data=qa_rows,
            )
            for site in sites
        ]

    return _make


@pytest.fixture
def make_buildings(random_text):
    def _make(*sites, street_name: Optional[str] = None):
        return [
            BuildingDBHandler.add(
                site_id=site["id"],
                housenumber="20-22",
                city="Zurich",
                zipcode="8000",
                street=street_name or random_text(),
                elevation=100.0,
            )
            for site in sites
        ]

    return _make


@pytest.fixture
def make_floor():
    def _make(building, plan, floornumber):
        return FloorDBHandler.add(
            plan_id=plan["id"], building_id=building["id"], floor_number=floornumber
        )

    return _make


@pytest.fixture
def make_units():
    def _make(*floors):
        return [
            UnitDBHandler.add(
                plan_id=floor["plan_id"],
                site_id=BuildingDBHandler.get_by(id=floor["building_id"])["site_id"],
                floor_id=floor["id"],
                apartment_no=apartment_no,
            )
            for apartment_no, floor in enumerate(floors)
        ]

    return _make


@pytest.fixture
def make_plans(fixtures_path, mocked_plan_image_upload_to_gc, random_image):
    content_type = "image/jpg"
    from handlers import PlanHandler

    def _make(*buildings):
        return [
            PlanHandler.add(
                plan_content=random_image(),
                plan_mime_type=content_type,
                site_id=building["site_id"],
                building_id=building["id"],
            )
            for building in buildings
        ]

    return _make


@pytest.fixture
def make_users():
    def _make(*clients):
        return [
            UserDBHandler.add(
                name=str(i),
                login=str(i),
                email=f"{i}@{i}.com",
                password="changeme",
                client_id=client["id"],
            )
            for i, client in enumerate(clients)
        ]

    return _make


@pytest.fixture
def make_annotations(annotations_path):
    def _make(*plans: Dict, annotation_plan_id: int = None):
        annotation_plan_id = annotation_plan_id or 2016
        with annotations_path.joinpath(f"plan_{annotation_plan_id}.json").open() as f:
            default_annotations = json.load(f)

        for plan in plans:
            ReactPlannerProjectsDBHandler.add(
                plan_id=plan["id"],
                data=default_annotations,
            )
            PlanDBHandler.update(
                item_pks=dict(id=plan["id"]), new_values=dict(annotation_finished=True)
            )
        return [default_annotations] * len(plans)

    return _make


@pytest.fixture
def make_classified_plans(annotations_path, populate_plan_areas_db, make_annotations):
    def _make(
        *plans,
        annotations_plan_id: int = 1478,
        db_fixture_ids=True,
    ) -> List[Dict]:
        make_annotations(*plans, annotation_plan_id=annotations_plan_id)
        areas = []
        if len(plans) > 1:
            db_fixture_ids = False
        for plan in plans:
            areas.extend(
                populate_plan_areas_db(
                    fixture_plan_id=annotations_plan_id,
                    populate=True,
                    db_plan_id=plan["id"],
                    db_fixture_ids=db_fixture_ids,
                )
            )
        return areas

    return _make


@pytest.fixture
def make_classified_split_plans(annotations_path, make_classified_plans, make_floor):
    from tasks.pipeline_tasks import split_plan_task

    def _make(
        *plans,
        building,
        annotations_plan_id: int = 1478,
        db_fixture_ids=True,
        floor_number: int = 0,
    ) -> List[Dict]:
        areas = []
        for i, plan in enumerate(plans, start=floor_number):
            plan_areas = make_classified_plans(
                plan,
                annotations_plan_id=annotations_plan_id,
                db_fixture_ids=db_fixture_ids,
            )
            areas.extend(plan_areas)
            make_floor(plan=plan, floornumber=i, building=building)
            split_plan_task(plan_id=plan["id"])
        return areas

    return _make


@pytest.fixture
def populate_plan_areas_db(fixtures_path: Path):
    def _internal(
        fixture_plan_id: int,
        populate: bool = False,
        db_fixture_ids=True,
        db_plan_id: Optional[int] = None,
    ):
        with fixtures_path.joinpath(
            f"areas/areas_plan_{fixture_plan_id}.json"
        ).open() as areas_file:
            areas = json.load(areas_file)
            if populate:
                if not db_fixture_ids:
                    area_ids = [
                        a["id"] for a in AreaDBHandler.find(output_columns=["id"])
                    ]
                    for i, area in enumerate(areas, start=max(area_ids, default=0)):
                        area["id"] = i + 1
                for area in areas:
                    area["plan_id"] = db_plan_id or fixture_plan_id
                AreaDBHandler.bulk_insert(areas)
            return areas

    return _internal


@pytest.fixture
def populate_plan_annotations(annotations_path, login):
    def _plan_annotations(fixture_plan_id, db_plan_id):
        with annotations_path.joinpath(f"plan_{fixture_plan_id}.json").open() as f:
            _ = ReactPlannerProjectsDBHandler.add(plan_id=db_plan_id, data=json.load(f))

    return _plan_annotations


@pytest.fixture
def upload_building_surroundings_to_google_cloud():
    from handlers.gcloud_storage import GCloudStorageHandler

    def _make(filepath: Path, site_id: int):
        gcs_buildings_link = GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_folder=GOOGLE_CLOUD_BUILDING_SURROUNDINGS,
            local_file_path=filepath,
            delete_local_after_upload=False,
        )
        Path(filepath.as_posix() + ".checksum").unlink(missing_ok=True)
        SiteDBHandler.update(
            item_pks=dict(id=site_id),
            new_values=dict(gcs_buildings_link=gcs_buildings_link),
        )

    return _make


@pytest.fixture
def upload_sample_surroundings_to_google_cloud():
    from handlers import SiteHandler
    from handlers.gcloud_storage import GCloudStorageHandler

    def _make(site_id: int):
        GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_folder=GOOGLE_CLOUD_VIEW_SAMPLE_SURROUNDINGS,
            # any file will do really
            local_file_path=Path("tests/fixtures/unit_vector_with_balcony.json"),
            destination_file_name=SiteHandler.get_surroundings_sample_path(
                site_id=site_id
            ),
        )

    return _make


@pytest.fixture
def add_background_plan_image_to_gcloud(
    fixtures_path, background_floorplan_image, client_db
):
    def add_image(
        plan_info: Dict,
        client_id: int = client_db["id"],
        image_content: bytes = background_floorplan_image,
    ) -> Dict:
        plan_gcs_metadata = add_plan_image_to_gcs(
            client_id=client_id, image_content=image_content
        )
        return PlanDBHandler.update(
            item_pks={"id": plan_info["id"]},
            new_values=plan_gcs_metadata,
        )

    return add_image


@pytest.fixture
def upload_deliverable_zip_file_to_gcs(
    mocker,
    recreate_test_gcp_client_bucket,
    client_db,
    site,
    fixtures_path,
    celery_eager,
):
    """Uploads an empty zipped folder to gcs"""
    from tasks.utils import deliverable_utils

    mocker.patch.object(
        deliverable_utils,
        deliverable_utils.generate_results_for_client_and_site.__name__,
        return_value=True,
    )
    task_site_zip_deliverable.run(site_id=site["id"])


@pytest.fixture
def make_folder(fixtures_path, mocked_plan_image_upload_to_gc, random_image):
    def _make(
        user_id: int,
        name: str = "TESTFOLDER",
        labels: List[str] = None,
        **kwargs,
    ):
        kwargs.update(get_entities(**kwargs))
        return FolderDBHandler.add(
            name=name, creator_id=user_id, labels=labels or [], **kwargs
        )

    return _make


@pytest.fixture
def make_files(fixtures_path):
    from handlers.db import FileDBHandler

    def _make(user_id: int, n: int = 1, **kwargs):
        kwargs.update(get_entities(**kwargs))
        return [
            FileDBHandler.add(
                creator_id=user_id,
                name=kwargs.pop("name", None) or f"file_{i}",
                content_type=mimetypes.types_map[".pdf"],
                size=6,
                checksum=f"{i}",
                **kwargs,
            )
            for i in range(n)
        ]

    return _make


@pytest.fixture
def generate_plan_related_data_helper(
    building,
    site,
    fixtures_path,
    make_floor,
    georef_plan_values,
    mocked_plan_image_upload_to_gc,
    make_classified_plans,
    make_classified_split_plans,
):
    """
    Generates plan, floor, areas and units for a given fixture_plan_id.
    Accepts floorplan_path, fixture_plan_id, floor number and scale
    It attaches to default site and building
    IMPORTANT: Remember if not passing a floorplan_path, the plan will be the same,
      so if making several plans be sure to pass a different floorplan_path
    """

    def _make(
        fixture_plan_id,
        floorplan_path="images/image_plan_332.jpg",
        floor_number=1,
        scale=0.000725269,
    ):
        floorplan_path = fixtures_path.joinpath(floorplan_path)
        plan = load_plan_helper(
            floorplan_path,
            site,
            building,
            georef_x=georef_plan_values[fixture_plan_id]["georef_x"],
            georef_y=georef_plan_values[fixture_plan_id]["georef_y"],
            georef_scale=scale,
            georef_rot_x=0.0,
            georef_rot_y=0.0,
            georef_rot_angle=0.0,
        )
        make_classified_split_plans(
            plan,
            annotations_plan_id=fixture_plan_id,
            building=building,
            floor_number=floor_number,
        )
        floor = FloorDBHandler.get_by(plan_id=plan["id"])
        # give a client_id to the units
        unit_layouts = PlanLayoutHandler(plan_id=plan["id"]).get_unit_layouts(
            floor_id=floor["id"]
        )

        # Consistently define the
        UnitDBHandler.bulk_update(
            client_id={
                unit_info["id"]: f"competition_{fixture_plan_id}_{i}"
                for i, (unit_info, unit_layout) in enumerate(
                    sorted(unit_layouts, key=lambda x: x[1].footprint.centroid.x)
                )
            }
        )

        return plan

    return _make


@pytest.fixture
def simulate_with_results(site):
    def _internal(unit_area_sim_values, task_type: TASK_TYPE, run_id):
        from handlers import SlamSimulationHandler

        # register simulation for site
        SlamSimulationHandler.register_simulation(
            site_id=site["id"],
            run_id=run_id,
            task_type=task_type,
            state=ADMIN_SIM_STATUS.SUCCESS,
        )
        # get all areas, sorted by x,y and add simulations stats:
        areas = sorted(
            AreaDBHandler.find(),
            key=lambda x: (x["plan_id"], x["coord_x"], x["coord_y"]),
        )
        areas_fake_stats = {
            a["id"]: stat_val for a, stat_val in zip(areas, cycle(unit_area_sim_values))
        }
        fake_simulation_results = {
            unit["id"]: {
                str(unit_area["area_id"]): areas_fake_stats[unit_area["area_id"]]
                for unit_area in UnitAreaDBHandler.find(unit_id=unit["id"])
            }
            for unit in UnitDBHandler.find()
        }
        # save stats per area for all units
        UnitSimulationDBHandler.bulk_insert(
            [
                dict(
                    unit_id=unit_id,
                    run_id=run_id,
                    results=simulation_results,
                )
                for unit_id, simulation_results in fake_simulation_results.items()
            ]
        )
        if task_type in [
            TASK_TYPE.VIEW_SUN,
            TASK_TYPE.SUN_V2,
            TASK_TYPE.NOISE,
            TASK_TYPE.CONNECTIVITY,
        ]:
            StatsHandler(
                run_id=run_id, results=fake_simulation_results
            )._compute_and_store_area_stats()

    return _internal


@pytest.fixture
def site_prepared_for_competition(
    generate_plan_related_data_helper, simulate_with_results, site
):
    """Adds a couple of plans to site and all the stuff needed to compute competition features on it"""
    generate_plan_related_data_helper(fixture_plan_id=5825, floor_number=0)
    generate_plan_related_data_helper(
        fixture_plan_id=5797, floorplan_path="images/floorplan_b.jpg", floor_number=-1
    )

    # add sun view simulation values
    view_values = {
        dimension.value: [1.0, 3.0, 5.0]
        for dimension in (
            VIEW_DIMENSION.VIEW_SKY,
            VIEW_DIMENSION.VIEW_WATER,
            VIEW_DIMENSION.VIEW_BUILDINGS,
            VIEW_DIMENSION.VIEW_GREENERY,
            VIEW_DIMENSION.VIEW_RAILWAY_TRACKS,
            VIEW_DIMENSION.VIEW_STREETS,
        )
    }
    # Add stats to all unit areas. Will cycle on this 2 values for all sorted areas
    simulate_with_results(
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.VIEW_SUN,
        unit_area_sim_values=[
            {
                SUN_DIMENSION.SUN_JUNE_MIDDAY.value: [100, 200, 300],
                SUN_DIMENSION.SUN_DECEMBER_MIDDAY.value: [400, 500, 600],
                **view_values,
            },
            {
                SUN_DIMENSION.SUN_JUNE_MIDDAY.value: [500, 100, 200],
                SUN_DIMENSION.SUN_DECEMBER_MIDDAY.value: [600, 600, 600],
                **view_values,
            },
        ],
    )

    # Add noise vals
    simulate_with_results(
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.NOISE,
        unit_area_sim_values=[
            {noise_type.value: [50] for noise_type in NOISE_SURROUNDING_TYPE},
            {noise_type.value: [30] for noise_type in NOISE_SURROUNDING_TYPE},
        ],
    )
    # Add noise windows vals
    obs_points = {"observation_points": [(1, 1, 1)]}
    simulate_with_results(
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.NOISE_WINDOWS,
        unit_area_sim_values=[
            {
                **{noise_type.value: [70] for noise_type in NOISE_SURROUNDING_TYPE},
                **obs_points,
            },
            {
                **{noise_type.value: [70] for noise_type in NOISE_SURROUNDING_TYPE},
                **obs_points,
            },
        ],
    )

    simulate_with_results(
        run_id=str(uuid.uuid4()),
        task_type=TASK_TYPE.SUN_V2,
        unit_area_sim_values=[
            {
                SuntimesHandler.get_sun_key_from_datetime(dt=sun_obs_date): [
                    100,
                    200,
                    300,
                ]
                for sun_obs_date in SuntimesHandler.get_sun_times_v2(site_id=site["id"])
            }
        ],
    )

    run_id = str(uuid.uuid4())
    SlamSimulationHandler.register_simulation(
        run_id=run_id,
        site_id=site["id"],
        task_type=TASK_TYPE.BIGGEST_RECTANGLE,
        state=ADMIN_SIM_STATUS.SUCCESS,
    )
    SlamSimulationHandler.store_results(
        run_id=run_id,
        results={
            unit_info["id"]: {
                area.db_area_id: (
                    area.footprint
                    if math.isclose(
                        area.footprint.area,
                        area.footprint.minimum_rotated_rectangle.area,
                    )
                    else Polygon(
                        ((0.0, 0.0), (3.3075, 0.0), (3.3075, 3.3075), (0.0, 3.3075)),
                    )
                ).wkt
                for area in unit_layout.areas
            }
            for unit_info, unit_layout in SiteHandler.get_unit_layouts(
                site_id=site["id"], georeferenced=True, scaled=True
            )
        },
    )


@pytest.fixture
def potential_view_simulations_list(fixtures_path):
    context = create_user_context(USERS["ADMIN"])

    with fixtures_path.joinpath(
        "potential_simulations/simulations_list.json"
    ).open() as f:
        for simulation in json.load(f):
            simulation["user_id"] = context["user"]["id"]
            PotentialSimulationDBHandler.bulk_insert([simulation])


@pytest.fixture
def make_react_annotation_fully_pipelined(
    celery_eager,
    plan,
    floor,
):
    def _make(react_planner_annotation, update_plan_rotation_point: bool = True):
        from handlers import AreaHandler, PlanHandler, ReactPlannerHandler
        from handlers.db import AreaDBHandler, PlanDBHandler, UnitDBHandler
        from handlers.plan_utils import create_areas_for_plan
        from tasks.pipeline_tasks import split_plan_task

        react_data = ReactPlannerHandler().store_plan_data(
            plan_id=plan["id"],
            plan_data=react_planner_annotation,
            validated=True,
        )
        PlanDBHandler.update(
            item_pks={"id": plan["id"]},
            new_values={
                "georef_rot_x": 0,
                "georef_rot_y": 0,
                "georef_rot_angle": 0,
                "georef_x": 0,
                "georef_y": 0,
            },
        )

        create_areas_for_plan(plan_id=plan["id"])
        if update_plan_rotation_point:
            PlanHandler(plan_id=plan["id"]).update_rotation_point()

        for area in AreaDBHandler.find(plan_id=plan["id"]):
            AreaDBHandler.update(
                item_pks={"id": area["id"]},
                new_values={"area_type": AreaType.ROOM.value},
            )

        # Classify the shaft as a shaft
        react_layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**react_data["data"]),
            scaled=True,
            post_processed=False,
        )

        index = AreaHandler.get_index_brooks_area_id_to_area_db_id(
            layout=react_layout,
            db_areas=PlanLayoutHandler(plan_id=plan["id"]).scaled_areas_db,
        )
        for shaft_brooks_id in [
            area.id for area in react_layout.areas if area.type == AreaType.SHAFT
        ]:
            AreaDBHandler.update(
                item_pks={"id": index[shaft_brooks_id]},
                new_values={"area_type": AreaType.SHAFT.value},
            )

        split_plan_task(plan_id=plan["id"])
        units = UnitDBHandler.find(plan_id=plan["id"])
        units = [
            UnitDBHandler.update(
                item_pks={"id": unit["id"]}, new_values={"client_id": f"apartment_{i}"}
            )
            for i, unit in enumerate(units)
        ]

        return {"plan": plan, "units": units}

    return _make


@pytest.fixture
def populate_unit_ph_price():
    units_ids = list(UnitDBHandler.find_ids())
    UnitDBHandler.bulk_update(
        ph_final_gross_rent_adj_factor={u_id: 0.03 for u_id in units_ids},
        ph_final_gross_rent_annual_m2={u_id: 100 for u_id in units_ids},
        ph_final_sale_price_m2={u_id: 500 for u_id in units_ids},
        ph_final_sale_price_adj_factor={u_id: 0.02 for u_id in units_ids},
    )


@pytest.fixture
def patch_geometry_provider_source_files(mocker, mocked_gcp_download):
    from surroundings.v2.osm.geometry_provider import OSMGeometryProvider
    from surroundings.v2.swisstopo.geometry_provider import (
        SwissTopoShapeFileGeometryProvider,
    )

    def _internal(
        geometry_provider_cls: Type[
            SwissTopoShapeFileGeometryProvider | OSMGeometryProvider
        ],
        filenames: Collection[str],
    ):
        mocker.patch.object(
            geometry_provider_cls,
            "file_templates",
            [Path(filename).with_suffix("").as_posix() for filename in filenames],
        )
        # NOTE: OSM tries to create the directory
        # which fails therefore patching mkdir ...
        mocker.patch.object(Path, "mkdir")

    return _internal


@pytest.fixture
def mock_surrounding_handlers(mocker):
    def _internal(
        module, surrounding_handler_types: Collection[Type[BaseSurroundingHandler]]
    ):
        fake_surrounding_handlers = []
        fake_triangles = set()

        for surrounding_handler_cls in surrounding_handler_types:
            fake_surrounding_handler = mocker.MagicMock()

            fake_triangle = mocker.MagicMock()
            fake_triangles.add(fake_triangle)
            fake_surrounding_handler.get_triangles.return_value = iter([fake_triangle])

            fake_surrounding_handlers.append(
                mocker.patch.object(
                    module,
                    surrounding_handler_cls.__name__,
                    return_value=fake_surrounding_handler,
                )
            )

        return fake_surrounding_handlers, fake_triangles

    return _internal
