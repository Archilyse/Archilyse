import json
from itertools import product

import pytest
from deepdiff import DeepDiff
from shapely import wkt
from shapely.geometry import box

from brooks.util.projections import project_geometry
from common_utils.constants import (
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
    SurroundingType,
)
from handlers import PotentialSimulationHandler
from handlers.db import PotentialSimulationDBHandler
from tests.utils import quavis_test


@pytest.fixture
def mocked_surroundings(mocker, fixtures_path):
    with fixtures_path.joinpath(
        "potential_simulations/potential_view_surroundings.json"
    ).open() as f:
        triangles = json.load(f)
    mocker.patch.object(
        PotentialSimulationHandler,
        "generate_view_surroundings",
        return_value=((SurroundingType.GROUNDS, t) for t in triangles),
    )


def test_get_full_potential_chain_for_building_footprint_creates_simulations():
    from tasks.potential_view_tasks import (
        get_full_potential_chain_for_building_footprint,
    )

    building_footprint_lv95 = box(2600000, 1200000, 2600050, 1200050)
    number_of_floors = 2

    get_full_potential_chain_for_building_footprint(
        building_footprint=building_footprint_lv95, number_of_floors=number_of_floors
    )

    simulations = PotentialSimulationDBHandler.find()

    expected_footprint_lat_lon = project_geometry(
        building_footprint_lv95, crs_from=REGION.CH, crs_to=REGION.LAT_LON
    )
    expected_values = dict(
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS.name,
        status=POTENTIAL_SIMULATION_STATUS.PENDING.name,
        simulation_version=SIMULATION_VERSION.PH_2022_H1.name,
        source_surr=SURROUNDING_SOURCES.SWISSTOPO.name,
        region=REGION.CH.name,
        result=None,
        identifier=None,
    )

    assert len(simulations) == 4
    for simulation, (expected_floor, expected_type) in zip(
        sorted(simulations, key=lambda s: (s["floor_number"], s["type"])),
        product(range(number_of_floors), SIMULATION_TYPE),
    ):
        expected_values.update(floor_number=expected_floor, type=expected_type.value)
        assert wkt.loads(simulation["building_footprint"]).almost_equals(
            expected_footprint_lat_lon
        )
        assert not (expected_values.items() - simulation.items())


@pytest.mark.slow
@quavis_test
def test_potential_view_task_with_surrounding_generation_quavis(
    mocker,
    celery_eager,
    mocked_swisstopo_esri_ascii_grid,
    mocked_surroundings,
    mocked_surrounding_storage_handler,
    mocked_quavis_gcp_handler,
    potential_view_results_test_potential_view_task,
):
    # todo run quavis version
    from surroundings.surrounding_handler import SurroundingStorageHandler
    from tasks import potential_view_tasks

    mocker.patch.object(
        potential_view_tasks,
        "SIMULATION_TYPES_TO_RUN",
        {SIMULATION_TYPE.SUN},
    )
    spy_upload_path = mocker.spy(PotentialSimulationHandler, "upload_view_surroundings")
    spy_download_path = mocker.spy(SurroundingStorageHandler, "read_from_cloud")

    number_of_floors = 1
    building_footprint = wkt.loads(
        "POLYGON ((2623242 1193073, 2623242 1193063, 2623232 1193063, 2623232 1193073, 2623242 1193073))"
    )

    # task workflow
    with mocked_swisstopo_esri_ascii_grid("swiss_1168_3", "swiss_1188_1"):
        potential_view_tasks.get_full_potential_chain_for_building_footprint(
            building_footprint=building_footprint, number_of_floors=number_of_floors
        ).delay().get()

    (simulation,) = PotentialSimulationDBHandler.find()

    assert not DeepDiff(
        simulation["result"],
        potential_view_results_test_potential_view_task,
        significant_digits=3,
    )
    # tests the path for the surroundings to upload and download are the same
    assert (
        spy_upload_path.call_args.kwargs["path"].name
        == spy_download_path.call_args.kwargs["remote_path"].name
    )


@pytest.fixture()
def monaco_sea_location_lat_lon():
    return {"lat": 43.734765, "lon": 7.4208953, "floor_number": 2}


@pytest.fixture
def mocked_geolocator_mc(monkeypatch, requests_mock):
    from handlers.geo_location import GeoLocator

    monkeypatch.setenv("TEST_ENVIRONMENT", "False")

    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 293958087,
            "osm_id": 28468412,
            "lat": "43.734765",
            "lon": "7.4208953",
            "display_name": "Somewhere in Monaco",
            "address": {
                "state": "Monaco",
                "postcode": "8952",
                "country": "Monaco",
                "country_code": "mc",
            },
            "boundingbox": ["50.0", "50.2", "14.1", "14.3"],
        },
    )


def test_priority_store(mocker):
    from tasks import potential_view_tasks

    mocked_parent_class = mocker.patch.object(
        potential_view_tasks.Task,
        "apply_async",
    )

    signature = potential_view_tasks.store_quavis_results_potential_task.si(
        simulation_id=999
    ).set(priority=1)

    signature.delay()
    assert mocked_parent_class.call_args.kwargs == {"priority": 10}
