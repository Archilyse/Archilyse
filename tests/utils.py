import functools
import hashlib
import inspect
import io
import itertools
import json
import os
import random
import uuid
from collections import Counter, defaultdict
from contextlib import contextmanager
from csv import DictReader
from distutils.util import strtobool
from functools import wraps
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory, mkdtemp
from types import FunctionType
from typing import Dict, List, Optional, Set, Tuple
from zipfile import ZipFile

import numpy as np
import pytest
from ezdxf.document import Drawing
from PIL import Image, ImageChops
from redis.client import Redis
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from shapely import wkt
from shapely.geometry import LineString, Point, Polygon, box
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_fixed

from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.types import (
    AreaType,
    FeatureType,
    OpeningSubType,
    OpeningType,
    SeparatorType,
)
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    GOOGLE_CLOUD_LOCATION,
    GOOGLE_CLOUD_PLAN_IMAGES,
    PLOT_DIR,
    SIMULATION_VERSION,
    TASK_TYPE,
    UNIT_BASICS_DIMENSION,
)
from common_utils.logger import logger
from common_utils.utils import pairwise
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    GroupDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
    RoleDBHandler,
    SlamSimulationDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
    UnitSimulationDBHandler,
    UserDBHandler,
)
from handlers.utils import get_client_bucket_name, get_simulation_name
from tests.constants import (
    GECKODRIVER_LOG_FILE,
    INTEGRATION_IMAGE_DIFF_DIR,
    TEST_CLIENT_NAME,
    TIME_TO_WAIT,
)


def check_immo_response_precision(results_data, precision):
    num_observation_points = len(results_data["observation_points"])
    for key, values in results_data.items():
        if key.startswith("observation"):
            continue

        assert len(values) == num_observation_points, key
        for val in values:
            assert len(str(val).split(".")[-1]) <= precision


class TestRetryException(Exception):
    pass


def get_area_types_counter(layout: SimLayout) -> Counter:
    area_types = Counter()
    for space in layout.spaces:
        for area in space.areas:
            area_types[area.type] += 1
    return area_types


@retry(stop=stop_after_delay(20), wait=wait_fixed(wait=0.25), reraise=True)
def get_wait_downloaded_file(folder: Path) -> Path:
    """Chrome creates a .crdownload file until the file is completely downloaded.
    Wait's up to 5 seconds for the file to be downloaded
    """
    file = list(folder.iterdir())[0]
    if file.suffix == ".crdownload":
        raise Exception("File still not fully downloaded")
    return file


def load_plan_helper(floorplan_path, site, building, **kwargs):
    from handlers import PlanHandler

    with floorplan_path.open("rb") as fp:
        content_type = "image/jpg"
        return PlanHandler.add(
            site_id=site["id"],
            building_id=building["id"],
            plan_mime_type=content_type,
            plan_content=fp.read(),
            **kwargs,
        )


def assert_areas_intersect_only_with_1_space(layout: SimLayout):
    for area in layout.areas:
        intersecting_spaces = {
            space
            for space in layout.spaces
            if space.footprint.intersects(area.footprint)
        }
        assert len(intersecting_spaces) == 1

    assert len([area for space in layout.spaces for area in space.areas]) == len(
        layout.areas
    )


def _get_or_create(DBHandler, data):
    row = DBHandler.find(name=data["name"])
    return DBHandler.add(**data) if not row else row[0]


def create_user_context(user):
    """Create the user, roles and groups if necessary"""
    roles = {r: _get_or_create(RoleDBHandler, dict(name=r)) for r in user["roles"]}

    if "group" in user:
        group = _get_or_create(GroupDBHandler, dict(name=user["group"]))
    else:
        group = {}

    if not user.get("client_id"):
        client = ClientDBHandler.find(name=TEST_CLIENT_NAME) or {}
        client = client[0] if client else {}
    else:
        client = ClientDBHandler.get_by(id=user.get("client_id"))

    user = {
        **_get_or_create(
            UserDBHandler,
            dict(
                name=user.get("name", user["login"]),
                login=user["login"],
                password=user["password"],
                roles=user["roles"],
                group_id=group.get("id"),
                client_id=client.get("id"),
                email=user.get("email"),
            ),
        ),
        **user,
    }
    return {"user": user, "group": group, "roles": roles}


def login_with(client, user):
    context = create_user_context(user)
    resp = client.post(
        "/auth/login", json=dict(user=user["login"], password=user["password"])
    ).get_json()
    context["access_token"] = resp["access_token"]
    return context


def check_deduplicated_triangles_by_type(triangles):
    # regression check to make sure we don't duplicate triangles
    # In the case of OSM water we have to ignore the overlap between polygons of different types
    counter = defaultdict(Counter)
    for triangle in triangles:
        counter[triangle[0]][tuple(itertools.chain(*triangle[1]))] += 1

    total_sum = sum([sum(sub_counter.values()) for sub_counter in counter.values()])

    assert total_sum == len(
        triangles
    ), f"expected: {total_sum}, created: {len(triangles)}"


def check_polygons_z(
    expected_area: float,
    expected_num_polygons: int,
    polygons_z,
    first_elem_height: Optional[float] = None,
):
    check_surr_triangles(
        expected_area=expected_area,
        expected_num_triangles=expected_num_polygons,
        first_elem_height=first_elem_height,
        surr_triangles=[("some bs", t.exterior.coords[:3]) for t in polygons_z],
        expected_surr_type={"some bs"},
    )


def check_surr_triangles(
    expected_area: float,
    expected_num_triangles: int,
    surr_triangles,
    expected_surr_type: Set,
    first_elem_height: Optional[float] = None,
):
    check_deduplicated_triangles_by_type(triangles=surr_triangles)
    triangles = [element[1] for element in surr_triangles]
    total_area = sum([Polygon(triangle).area for triangle in triangles])

    assert expected_area == pytest.approx(total_area, abs=2), (
        expected_area,
        total_area,
    )
    assert expected_surr_type == {element[0] for element in surr_triangles}
    assert (
        first_elem_height == pytest.approx(float(triangles[0][0][2]), rel=1e-3)
        if first_elem_height is not None
        else None
    ), (first_elem_height, triangles[0][0][2])

    assert len(surr_triangles) == pytest.approx(expected_num_triangles, abs=2), (
        expected_num_triangles,
        len(surr_triangles),
    )
    assert len(triangles[0]) == 3
    assert all(isinstance(dimension, float) for dimension in triangles[0][0])


def check_3d_mesh_format(
    meshes,
    expected_dimensions,
    expected_nbr_of_meshes: int,
    expected_mesh_names: Set[str],
    expected_bounds: Tuple[float, float, float, float] = None,
):

    assert len(meshes) == expected_nbr_of_meshes

    actual_mesh_names = {id for id, _ in meshes}
    assert expected_mesh_names == actual_mesh_names

    actual_dimensions = {triangles.shape for _, triangles in meshes}

    assert actual_dimensions == expected_dimensions, (
        actual_dimensions,
        expected_dimensions,
    )

    actual_dtypes = {triangles.dtype.type for _, triangles in meshes}
    expected_dtypes = {np.float64}
    assert actual_dtypes == expected_dtypes

    if expected_bounds:
        x_coords = [
            point[0]
            for _, triangles in meshes
            for triangle in triangles
            for point in triangle
        ]
        y_coords = [
            point[1]
            for _, triangles in meshes
            for triangle in triangles
            for point in triangle
        ]
        bounds = (
            min(x_coords),
            min(y_coords),
            max(x_coords),
            max(y_coords),
        )
        assert bounds == pytest.approx(expected=expected_bounds, abs=0.001), bounds


def load_csv_as_dict(filepath: Path):
    with filepath.open() as csvfile:
        return [row for row in DictReader(csvfile)]


def load_dataframe_from_zip_file(fixtures_path: Path, file_name: str):
    import pandas as pd

    with ZipFile(fixtures_path.joinpath(f"{file_name}.zip")) as zip_file:
        with zip_file.open(f"{file_name}.csv") as csv_file:
            return pd.read_csv(csv_file)


def save_dataframe_to_zip_file(fixtures_path: Path, file_name: str, data):
    with ZipFile(fixtures_path.joinpath(f"{file_name}.zip"), "w") as zip_file:
        with zip_file.open(f"{file_name}.csv", "w") as csv_file:
            data.to_csv(csv_file, index=None)


def load_json_from_zip_file(fixtures_path: Path, file_name: str):
    with ZipFile(fixtures_path.joinpath(f"{file_name}.zip")) as zip_file:
        with zip_file.open(f"{file_name}.json") as json_file:
            return json.load(json_file)


def save_json_to_zip_file(fixtures_path: Path, file_name: str, data: Dict):
    with ZipFile(fixtures_path.joinpath(f"{file_name}.zip"), "w") as zip_file:
        with zip_file.open(f"{file_name}.json", "w") as json_file:
            json_file.write(json.dumps(data).encode())


@contextmanager
def get_temp_path_of_extracted_file(
    fixtures_path: Path, filename: str, extension=".ifc"
) -> Path:
    try:
        with TemporaryDirectory() as directory:
            with ZipFile(fixtures_path.joinpath(f"{filename}.zip"), "r") as zip_ref:
                zip_ref.extractall(directory)
                yield Path(directory).joinpath(f"{filename}").with_suffix(extension)
    except Exception:
        raise
    finally:
        pass


@contextmanager
def do_while_pressing(browser, key: Keys):
    ActionChains(browser.driver).key_down(key).perform()
    yield
    ActionChains(browser.driver).key_up(key).perform()


def wait_for_url(browser, desired_url):
    WebDriverWait(browser.driver, TIME_TO_WAIT).until(
        expected_conditions.url_contains(desired_url)
    )
    assert desired_url in browser.url


def switch_to_opened_tab(browser):
    opened_tab = browser.driver.window_handles[-1]
    browser.driver.switch_to.window(opened_tab)


def quavis_test(func):
    """
    Decorator for running tests using ViewWrapper.execute_quavis:
     * pytest --generate-quavis-fixtures: executes quavis, stores
         the output as zip file
     * pytest --quavis: executes quavis normally, using the GPU
     * pytest w/o flags: mocks quavis output
    """
    from simulations.view import ViewWrapper
    from tests.file_fixtures import QUAVIS_OUTPUTS_PATH

    # NOTE: Needed because the original execute_quavis method is
    #       patched to save the output / return the fixture
    execute_quavis_copy = FunctionType(
        code=ViewWrapper.execute_quavis.__code__,
        globals=ViewWrapper.execute_quavis.__globals__,
        name=ViewWrapper.execute_quavis.__name__,
        argdefs=ViewWrapper.execute_quavis.__defaults__,
        closure=ViewWrapper.execute_quavis.__closure__,
    )

    quavis_fixture_filename = f"quavis_output_{func.__name__}.json"

    def _save_quavis_output(*args, **kwargs):
        output_data = execute_quavis_copy(cls=ViewWrapper, *args, **kwargs)
        save_json_to_zip_file(
            fixtures_path=QUAVIS_OUTPUTS_PATH,
            file_name=quavis_fixture_filename,
            data=output_data,
        )
        return output_data

    def _load_quavis_output(*args, **kwargs):
        return load_json_from_zip_file(
            fixtures_path=QUAVIS_OUTPUTS_PATH, file_name=quavis_fixture_filename
        )

    @pytest.fixture()
    def mocked_quavis_output(pytestconfig, monkeypatch):
        if pytestconfig.getoption("--generate-quavis-fixtures"):
            monkeypatch.setattr(ViewWrapper, "execute_quavis", _save_quavis_output)
        elif not pytestconfig.getoption("--quavis"):
            monkeypatch.setattr(ViewWrapper, "execute_quavis", _load_quavis_output)

    inspect.getmodule(func).__dict__[
        f"mocked_quavis_output_{func.__name__}"
    ] = mocked_quavis_output

    @wraps(func)
    @pytest.mark.usefixtures(f"mocked_quavis_output_{func.__name__}")
    @pytest.mark.quavis_test
    def test_run_quavis(*args, **kwargs):
        return func(*args, **kwargs)

    return test_run_quavis


def generate_image_difference(
    path_a: Path,
    path_b_expected: Path,
):
    im1 = Image.open(path_a.as_posix()).convert("RGB")
    im2 = Image.open(path_b_expected.as_posix()).convert("RGB")

    diff_image = ImageChops.difference(im1, im2)

    output_path = INTEGRATION_IMAGE_DIFF_DIR.joinpath(path_b_expected.name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Writing image to {output_path}")

    diff_image.save(output_path.as_posix())


def assert_image_phash(
    new_image_content: Image,
    expected_image_file: Path,
    hash_size: int = 16,
    update_fixtures: bool = False,
    force_update: bool = False,
):
    import imagehash

    image_hash_function = imagehash.phash
    new_hash = image_hash_function(new_image_content, hash_size=hash_size)

    if update_fixtures and not expected_image_file.exists():
        new_image_content.save(expected_image_file.as_posix())

    with Image.open(expected_image_file.as_posix()) as img:
        expected_hash = image_hash_function(img, hash_size=hash_size)

    perception_hash = new_hash - expected_hash
    if perception_hash != 0.0 and update_fixtures or force_update:
        new_image_content.save(expected_image_file.as_posix())
        assert_image_phash(
            new_image_content=new_image_content,
            expected_image_file=expected_image_file,
            hash_size=hash_size,
            update_fixtures=False,
            force_update=False,
        )
    else:
        if perception_hash:
            with NamedTemporaryFile() as f:
                new_image_content.save(f.name, format="png")
                generate_image_difference(
                    path_a=Path(f.name), path_b_expected=expected_image_file
                )

        assert perception_hash == 0.0


def random_simulation_version():
    """Used to indicate that the simulation version shouldn't affect the results"""
    return random.choice(list(SIMULATION_VERSION))


def javascript_click_by_data_value(browser, data_value):
    browser.execute_script(
        f"document.querySelector('[data-value=\"{data_value}\"]').click();"
    )


def prepare_for_competition(
    site_id: int, fixtures_path: Path, random_plain_floorplan_link
):
    with fixtures_path.joinpath("building.json").open() as f:
        building = json.load(f)
        building["site_id"] = site_id
        BuildingDBHandler.add(**building)

    building = BuildingDBHandler.get_by(site_id=site_id)

    with fixtures_path.joinpath("plan.json").open() as f:
        entity = json.load(f)
        entity["site_id"] = site_id
        entity["building_id"] = building["id"]
        entity["image_gcs_link"] = random_plain_floorplan_link
        PlanDBHandler.add(**entity)

    plan = PlanDBHandler.get_by(site_id=site_id)

    with fixtures_path.joinpath("annotation.json").open() as f:
        entity = json.load(f)
        entity["plan_id"] = plan["id"]
        ReactPlannerProjectsDBHandler.add(**entity)

    with fixtures_path.joinpath("areas.json").open() as f:
        for entity in json.load(f):
            entity["plan_id"] = plan["id"]
            AreaDBHandler.add(**entity)

    areas = AreaDBHandler.find(plan_id=plan["id"])

    with fixtures_path.joinpath("floor.json").open() as f:
        entity = json.load(f)
        entity["plan_id"] = plan["id"]
        entity["building_id"] = building["id"]
        FloorDBHandler.add(**entity)

    floor = FloorDBHandler.get_by(building_id=building["id"])

    with fixtures_path.joinpath("unit.json").open() as f:
        entity = json.load(f)
        entity["site_id"] = site_id
        entity["plan_id"] = plan["id"]
        entity["floor_id"] = floor["id"]
        UnitDBHandler.add(**entity)

    unit = UnitDBHandler.get_by(site_id=site_id)

    for area in areas:
        entity = dict()
        entity["unit_id"] = unit["id"]
        entity["area_id"] = area["id"]
        UnitAreaDBHandler.add(**entity)

    # View Sun
    for sim_fixture, task_type in (
        ("view_sun_sim_values.json", TASK_TYPE.VIEW_SUN),
        ("basic_features.json", TASK_TYPE.BASIC_FEATURES),
    ):
        add_simulation(
            fixtures_path=fixtures_path.joinpath(sim_fixture),
            task_type=task_type,
            site_id=site_id,
            units_ids=[unit["id"]],
        )


def add_simulation(fixtures_path, task_type, site_id, units_ids):
    with fixtures_path.open() as f:
        run_id = str(uuid.uuid4())
        SlamSimulationDBHandler.add(
            site_id=site_id,
            run_id=run_id,
            type=task_type.name,
            state=ADMIN_SIM_STATUS.SUCCESS.name,
            created="2020-09-01 10:42:33.890082",
        )

        with fixtures_path.open() as f:
            sim_vales = json.load(f)
        for unit_id in units_ids:
            UnitSimulationDBHandler.bulk_insert(
                [{"run_id": run_id, "unit_id": unit_id, "results": sim_vales}]
            )


def convert_dxf_to_jpeg(ezdxf_doc: Drawing) -> io.BytesIO:
    from ezdxf.addons.drawing import matplotlib as ezdxf_matplotlib

    # Exception handling left out for compactness:
    with NamedTemporaryFile(suffix=".jpeg") as temp_file:
        ezdxf_matplotlib.qsave(
            layout=ezdxf_doc.modelspace(),
            filename=temp_file.name,
            bg="#FFFFFF",
        )
        temp_file.seek(0)
        io_file = io.BytesIO()
        io_file.write(temp_file.read())
        io_file.seek(0)
    return io_file


def add_sun_simulation_to_units(units):
    sun_data = {
        "Sun.v2.mean.sun-2018-03-21 08:00:00+01:00": 1,
        "Sun.v2.mean.sun-2018-03-21 10:00:00+01:00": 1,
        "Sun.v2.mean.sun-2018-03-21 12:00:00+01:00": 2,
        "Sun.v2.mean.sun-2018-03-21 14:00:00+01:00": 2,
        "Sun.v2.mean.sun-2018-03-21 16:00:00+01:00": 2,
        "Sun.v2.mean.sun-2018-03-21 18:00:00+01:00": 3,
        "Sun.v2.mean.sun-2018-06-21 06:00:00+02:00": 1,
        "Sun.v2.mean.sun-2018-06-21 08:00:00+02:00": 1,
        "Sun.v2.mean.sun-2018-06-21 10:00:00+02:00": 1,
        "Sun.v2.mean.sun-2018-06-21 12:00:00+02:00": 2,
        "Sun.v2.mean.sun-2018-06-21 14:00:00+02:00": 2,
        "Sun.v2.mean.sun-2018-06-21 16:00:00+02:00": 2,
        "Sun.v2.mean.sun-2018-06-21 18:00:00+02:00": 3,
        "Sun.v2.mean.sun-2018-06-21 20:00:00+02:00": 3,
        "Sun.v2.mean.sun-2018-12-21 10:00:00+01:00": 1,
        "Sun.v2.mean.sun-2018-12-21 12:00:00+01:00": 2,
        "Sun.v2.mean.sun-2018-12-21 14:00:00+01:00": 2,
        "Sun.v2.mean.sun-2018-12-21 16:00:00+01:00": 2,
    }
    return add_sun_and_view_simulation_to_room_and_unit_vector(
        units=units, sun_and_view_values=sun_data
    )


def add_sun_and_view_simulation_to_room_and_unit_vector(
    units: List[Dict], sun_and_view_values: Dict
):
    for unit in units:
        unit["unit_vector_with_balcony"][0].update(sun_and_view_values)
        for vector in unit["room_vector_with_balcony"]:
            vector.update(sun_and_view_values)
        UnitDBHandler.update(
            item_pks={"id": unit["id"]},
            new_values={
                "unit_vector_with_balcony": unit["unit_vector_with_balcony"],
                "room_vector_with_balcony": unit["room_vector_with_balcony"],
            },
        )
    return units


def get_splinter_driver_kwargs(splinter_file_download_dir, splinter_webdriver):
    headless = bool(strtobool(os.environ.get("BROWSER_HEADLESS", "False")))
    if splinter_webdriver == "chrome":
        options = ChromeOptions()
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=2048,1152")
        options.add_argument(f"--log-path={GECKODRIVER_LOG_FILE}")
        options.add_experimental_option(
            "prefs",
            {
                "download.default_directory": splinter_file_download_dir,
                "download.prompt_for_download": False,
            },
        )
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        return {
            "headless": headless,
            "options": options,
        }
    options = FirefoxOptions()
    options.log.level = "error"
    options.set_preference("devtools.console.stdout.content", True)
    return {
        "headless": headless,
        "capabilities": options.capabilities,
        "firefox_options": options,
        "service_log_path": GECKODRIVER_LOG_FILE,
    }


def browser_console_logs_to_logger(browser):
    if strtobool(os.environ.get("LOG_JS_CONSOLE_OUTPUT", False)):
        if browser.driver_name != "Chrome":
            # clean up the geckodriver logs file
            with open(GECKODRIVER_LOG_FILE, "w"):
                pass
        yield
        if browser.driver_name != "Chrome":
            with open(GECKODRIVER_LOG_FILE) as f:
                logger.info(f.read())
        else:
            for entry in browser.driver.get_log("browser"):
                logger.info(entry)


def recreate_db():
    from connectors.db_connector import recreate_postgres_metadata
    from tests.celery_utils import confirm_no_tasks_unfinished

    confirm_no_tasks_unfinished()
    recreate_postgres_metadata()


def get_redis():
    from workers_config.celery_config import redis_conn_config

    return Redis(**redis_conn_config)


def clear_redis():
    get_redis().flushdb()


def retry_stale_element(func):
    @functools.wraps(func)
    @retry(
        retry=retry_if_exception_type(StaleElementReferenceException),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def retry_intercepted_click(func):
    @functools.wraps(func)
    @retry(
        retry=retry_if_exception_type(ElementClickInterceptedException),
        reraise=True,
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper


def fake_unit_simulation_results(area_id_1, area_id_2):
    return {
        str(area_id_1): {
            "observation_points": [[1, 1, 1], [2, 2, 1], [3, 3, 1]],
            "traffic_day": [100, 200, 300],
            "traffic_night": [1000, 2000, 3000],
        },
        str(area_id_2): {
            "observation_points": [[1, 1, 1], [2, 2, 1], [3, 3, 1]],
            "traffic_day": [400, 500, 600],
            "traffic_night": [4000, 5000, 6000],
        },
        "resolution": 0.25,
    }


def fake_area_simulation_result(
    areas: Set[SimArea], dimensions: Set[str], fake_value: float
):
    length = 10
    result = defaultdict(dict)
    for dimension in dimensions:
        for area in areas:
            result[area.db_area_id]["observation_points"] = [
                [area.footprint.centroid.y, area.footprint.centroid.x, 445.04681]
                * length
            ]
            result[area.db_area_id][dimension] = [fake_value for _ in range(0, length)]
    return result


def fake_basic_features(fake_value):
    unit_vector = dict()
    for dimension in UNIT_BASICS_DIMENSION:
        unit_vector[get_simulation_name(dimension=dimension)] = fake_value
    return [unit_vector]


def make_layout_square_4_windows(db_area_id, centroid: Point = None) -> SimLayout:
    if not centroid:
        centroid = Point(1.5, 1.5)
    """one square room with windows in all sides and 1sqm. """
    building_footprint = box(
        centroid.x - 0.5, centroid.y - 0.5, centroid.x + 0.5, centroid.y + 0.5
    )
    area = SimArea(footprint=building_footprint)
    area.db_area_id = db_area_id

    space = SimSpace(footprint=building_footprint)
    space.areas.add(area)

    walls = set()
    for point_a, point_b in pairwise(building_footprint.exterior.coords):
        # create wall
        wall_footprint = LineString([point_a, point_b]).buffer(0.1)
        wall = SimSeparator(
            separator_type=SeparatorType.WALL,
            height=(2.8, 0),
            footprint=wall_footprint,
        )
        walls.add(wall)

        # create opening
        min_x, min_y, max_x, max_y = wall_footprint.bounds
        if max_x - min_x > max_y - min_y:
            length = max_x - min_x
            window_footprint = box(
                min_x + length * 0.25, min_y, min_x + length * 0.75, max_y
            )
        else:
            length = max_y - min_y
            window_footprint = box(
                min_x, min_y + length * 0.25, max_x, min_y + length * 0.75
            )

        wall.add_opening(
            SimOpening(
                footprint=window_footprint,
                opening_type=OpeningType.WINDOW,
                height=(2.8, 0),
                separator=wall,
                separator_reference_line=get_center_line_from_rectangle(wall.footprint)[
                    0
                ],
            )
        )
    return SimLayout(spaces={space}, separators=walls)


def visualize_mesh_in_plotly(meshes):
    from surroundings.visualization.sourroundings_3d_figure import create_3d_figure

    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    local_file_name = PLOT_DIR.joinpath("test.html-3d.html").as_posix()

    create_3d_figure(
        triangles=[mesh[1] for mesh in meshes],
        identifiers=[mesh[0] for mesh in meshes],
        title="test",
        filename=local_file_name,
        opacity=1.0,
    )


def _generate_dummy_layout(
    area_type: Optional[AreaType] = AreaType.NOT_DEFINED,
    feature_type: Optional[FeatureType] = None,
    opening_types: Optional[List[OpeningType]] = None,
    opening_sub_types: Optional[List[OpeningSubType]] = None,
):
    area = SimArea(footprint=box(0, 0.2, 10, 10), area_type=area_type)
    area.area_db_id = 1
    space = SimSpace(footprint=area.footprint)
    space.add_area(area=area)
    separator = SimSeparator(
        footprint=box(0, -0.2, 10, 0.2), separator_type=SeparatorType.WALL
    )

    if feature_type:
        feature = SimFeature(
            footprint=box(0.5, 0.5, 1.2, 2.5), feature_type=feature_type
        )
        area.features.add(feature)

    if opening_types:
        for i, opening_type in enumerate(opening_types):
            opening = SimOpening(
                footprint=box(1, -0.2, 2, 0.2),
                height=(1, 2.5),
                separator=separator,
                opening_type=opening_type,
                opening_sub_type=opening_sub_types[i] if opening_sub_types else None,
                separator_reference_line=get_center_line_from_rectangle(
                    separator.footprint
                )[0],
            )
            separator.add_opening(opening=opening)

    return SimLayout(spaces={space}, separators={separator})


def recreate_test_gcp_client_bucket_method(client_id: int):
    from handlers import GCloudStorageHandler

    bucket_name = get_client_bucket_name(client_id=client_id)
    GCloudStorageHandler().delete_bucket_if_exists(bucket_name=bucket_name)
    GCloudStorageHandler().create_bucket_if_not_exists(
        bucket_name=bucket_name,
        location=GOOGLE_CLOUD_LOCATION,
        predefined_acl="public-read",
        predefined_default_object_acl="public-read",
    )


def add_plan_image_to_gcs(
    client_id: int,
    image_content: bytes,
) -> Dict:
    from handlers import GCloudStorageHandler, PlanHandler

    digest = hashlib.sha256(image_content).hexdigest()

    image_width, image_height = PlanHandler._extract_image_parameters_for_plan(
        image_data=image_content
    )

    image_gc_link = GCloudStorageHandler().upload_bytes_to_bucket(
        bucket_name=get_client_bucket_name(client_id=client_id),
        destination_folder=GOOGLE_CLOUD_PLAN_IMAGES,
        destination_file_name=str(uuid.uuid4()) + ".png",
        contents=image_content,
    )
    return {
        "image_width": image_width,
        "image_height": image_height,
        "image_gcs_link": image_gc_link,
        "image_mime_type": "image/png",
        "image_hash": digest,
    }


def db_areas_from_layout(layout, plan_id):
    return [
        dict(
            plan_id=plan_id,
            coord_x=float(area.footprint.representative_point().xy[0][0]),
            coord_y=float(area.footprint.representative_point().xy[1][0]),
            scaled_polygon=wkt.dumps(area.footprint),
            area_type=area.type.name,
        )
        for i, area in enumerate(layout.areas)
    ]


def assert_dxf_visual_differences(
    drawing: Drawing,
    expected_image_file: Path,
    hash_size: int = 7,
    save_dxf_to_tmp: bool = False,
):
    if save_dxf_to_tmp:
        tmp_dir = Path(mkdtemp())
        tmp_dir.mkdir(parents=True, exist_ok=True)
        file_name = tmp_dir.joinpath(f"{expected_image_file.name}.dxf")
        drawing.saveas(file_name)
        logger.debug(f"saved file to {file_name.as_posix()}")

    jpeg_image = convert_dxf_to_jpeg(ezdxf_doc=drawing)
    with Image.open(jpeg_image) as new_image_content:
        assert_image_phash(
            expected_image_file=expected_image_file,
            new_image_content=new_image_content,
            hash_size=hash_size,
        )


def assert_dxf_audit(drawing):
    auditor = drawing.audit()
    assert not auditor.errors, auditor.errors
