import json
from collections import Counter, defaultdict
from typing import Dict, List, Optional

import pytest
from deepdiff import DeepDiff

from brooks.models.layout import PotentialLayoutWithWindows
from brooks.util.projections import project_geometry
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION,
    DEFAULT_OBSERVATION_HEIGHT,
    DEFAULT_SUN_TIMES,
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
)
from handlers import SiteHandler
from handlers.db import SlamSimulationDBHandler, UnitAreaDBHandler, UnitDBHandler
from handlers.quavis import SLAMQuavisHandler
from tasks.simulations_tasks import simulation_error
from tasks.workflow_tasks import WorkflowGenerator
from tests.utils import quavis_test


@pytest.fixture
def mocked_surroundings_slam(mocker, fixtures_path):
    from surroundings.surrounding_handler import SurroundingStorageHandler

    surroundings = SurroundingStorageHandler.load(
        filepath=fixtures_path.joinpath("surroundings_view_fixtures/surroundings.csv")
    )
    return mocker.patch.object(
        SiteHandler, "get_view_surroundings", return_value=surroundings
    )


@pytest.fixture
def expected_vectors(fixtures_path):
    from tests.utils import load_json_from_zip_file

    return load_json_from_zip_file(
        fixtures_path=fixtures_path.joinpath("view_simulation"), file_name="vectors"
    )


@pytest.fixture
def expected_potential_view_results(fixtures_path) -> Dict:
    with fixtures_path.joinpath(
        "view_simulation/potential_view_result.json"
    ).open() as f:
        return json.load(f)


@pytest.fixture
def expected_slam_sunv2_results(fixtures_path):
    from tests.utils import load_json_from_zip_file

    return load_json_from_zip_file(
        fixtures_path=fixtures_path.joinpath("view_simulation"),
        file_name="slam_sunv2_view_result",
    )


def assert_quavis_input(
    quavis_input: Dict,
    site_id: int,
    expected_nbr_of_positions: int,
    expected_nbr_of_vertexes: int,
    expected_nbr_of_indices: int,
    expected_positions: Optional[List[float]] = None,
    sun_version: Optional[str] = "sun",
):
    def assert_observation_points(site_id: int, quavis_input: Dict):
        obs_points = SiteHandler.get_obs_points_by_unit_and_area(
            site_id=site_id,
            grid_resolution=DEFAULT_GRID_RESOLUTION,
            grid_buffer=DEFAULT_GRID_BUFFER,
            obs_height=DEFAULT_OBSERVATION_HEIGHT,
        )

        num_observation_per_unit_id = Counter()
        area_ids_in_obs = set()

        for unit_id, area_obs in obs_points.items():
            for area_id, obs in area_obs.items():
                num_observation_per_unit_id[unit_id] += len(obs)
                area_ids_in_obs.add(area_id)

        db_area_ids = list(
            UnitAreaDBHandler.find_in(
                unit_id=list(UnitDBHandler.find_ids(site_id=site_id)),
            )
        )
        assert {x["area_id"] for x in db_area_ids} == area_ids_in_obs
        # Observation points are a flat list in quavis so we divide it by 3
        assert len(
            quavis_input["quavis"]["observationPoints"]["positions"]
        ) / 3.0 == sum(num_observation_per_unit_id.values())

    def assert_metadata(quavis_input: Dict):
        assert quavis_input["quavis"]["metaData"]["_geom_groups"] == ["site", "LAKES"]

        assert quavis_input["quavis"]["computeStages"] == [
            {"type": "volume", "name": "volume"},
            {"type": "groups", "name": "groups", "max_groups": 512},
            {"type": sun_version, "name": "sun"},
        ]

    def assert_triangles(
        quavis_input: Dict,
        expected_positions: List[float],
        nbr_of_positions: int,
        nbr_of_vertexes: int,
        nbr_of_indices: int,
    ):
        if expected_positions:
            assert not DeepDiff(
                quavis_input["quavis"]["sceneObjects"][0]["positions"],
                expected_positions,
                significant_digits=3,
            )

        expected = {
            "positions": nbr_of_positions,
            "indices": nbr_of_indices,
            "vertexData": nbr_of_vertexes,
        }
        assert not DeepDiff(
            expected,
            {
                "positions": len(
                    quavis_input["quavis"]["sceneObjects"][0]["positions"]
                ),
                "indices": len(quavis_input["quavis"]["sceneObjects"][0]["indices"]),
                "vertexData": len(
                    quavis_input["quavis"]["sceneObjects"][0]["vertexData"]
                ),
            },
        )

    assert_metadata(quavis_input=quavis_input)
    assert_observation_points(site_id=site_id, quavis_input=quavis_input)
    assert_triangles(
        quavis_input=quavis_input,
        expected_positions=expected_positions,
        nbr_of_positions=expected_nbr_of_positions,
        nbr_of_vertexes=expected_nbr_of_vertexes,
        nbr_of_indices=expected_nbr_of_indices,
    )


class TestSlamQuavisSim:
    expected_nbr_of_positions = 6201
    expected_nbr_of_indices = 11232
    expected_nbr_of_vertexes = 8268

    @quavis_test
    def test_simulation_chain_sun_v2_slam(
        self,
        first_pipeline_complete_db_models,
        mocked_surroundings_slam,
        celery_eager,
        mocked_quavis_gcp_handler,
        run_ids,
        expected_vectors,
        fixtures_path,
        expected_slam_sunv2_results,
    ):
        site_id = first_pipeline_complete_db_models["site"]["id"]
        pipeline_units = {
            u["id"]: u for u in first_pipeline_complete_db_models["units"]
        }
        areas_by_unit_id = defaultdict(list)
        for area_unit in UnitAreaDBHandler.find_in(
            unit_id=[u["id"] for u in pipeline_units.values()]
        ):
            matching_unit = pipeline_units[area_unit["unit_id"]]
            areas_by_unit_id[matching_unit["client_id"]].append(area_unit["area_id"])

        WorkflowGenerator(site_id=site_id).get_sun_v2_task_chain().delay()

        assert_quavis_input(
            quavis_input=mocked_quavis_gcp_handler.quavis_input,
            site_id=first_pipeline_complete_db_models["site"]["id"],
            expected_nbr_of_positions=self.expected_nbr_of_positions,
            expected_nbr_of_indices=self.expected_nbr_of_indices,
            expected_nbr_of_vertexes=self.expected_nbr_of_vertexes,
            sun_version="sunv2",
        )

        simulation = SlamSimulationDBHandler.get_by(run_id=run_ids[0])
        assert simulation["state"] == ADMIN_SIM_STATUS.SUCCESS.value

    @quavis_test
    def test_simulation_chain_quavis_slam(
        self,
        first_pipeline_complete_db_models,
        mocked_surroundings_slam,
        celery_eager,
        mocked_quavis_gcp_handler,
        expected_vectors,
        run_ids,
    ):
        # TODO here fails
        site_id = first_pipeline_complete_db_models["site"]["id"]
        WorkflowGenerator(site_id=site_id).get_view_task_chain().delay()

        assert_quavis_input(
            quavis_input=mocked_quavis_gcp_handler.quavis_input,
            expected_nbr_of_positions=self.expected_nbr_of_positions,
            expected_nbr_of_indices=self.expected_nbr_of_indices,
            expected_nbr_of_vertexes=self.expected_nbr_of_vertexes,
            site_id=first_pipeline_complete_db_models["site"]["id"],
        )

        view_sun_db = SlamSimulationDBHandler.get_by(run_id=run_ids[0])
        assert view_sun_db["state"] == ADMIN_SIM_STATUS.SUCCESS.value

    def test_quavis_input_experimental(
        self,
        site,
        building,
        plan,
        make_classified_split_plans,
        mocked_surroundings_slam,
        celery_eager,
        mocked_quavis_gcp_handler,
        fixtures_path,
        update_fixture: bool = False,
    ):
        make_classified_split_plans(
            plan,
            building=building,
            annotations_plan_id=863,
            floor_number=0,
        )

        quavis_input = SLAMQuavisHandler.get_quavis_input(
            entity_info=site,
            grid_resolution=DEFAULT_GRID_RESOLUTION,
            grid_buffer=DEFAULT_GRID_BUFFER,
            obs_height=DEFAULT_OBSERVATION_HEIGHT,
            datetimes=DEFAULT_SUN_TIMES,
            simulation_version=SIMULATION_VERSION.EXPERIMENTAL,
        )
        if update_fixture:
            with fixtures_path.joinpath("quavis_input/view_v3.json").open("w") as f:
                json.dump(quavis_input["quavis"]["sceneObjects"][0]["positions"], f)
        with fixtures_path.joinpath("quavis_input/view_v3.json").open("r") as f:
            expected_positions = json.load(f)

        assert_quavis_input(
            quavis_input=quavis_input,
            site_id=site["id"],
            expected_nbr_of_positions=6255,
            expected_nbr_of_indices=11244,
            expected_nbr_of_vertexes=8340,
            expected_positions=expected_positions,
        )


@quavis_test
def test_simulation_chain_quavis_potential(
    mocker,
    mocked_quavis_gcp_handler,
    mocked_gcp_upload_file_to_bucket,
    celery_eager,
    expected_potential_view_results,
    mock_elevation,
    mocked_geolocator,
):
    from shapely.affinity import translate
    from shapely.geometry import box

    from common_utils.constants import SIMULATION_TYPE
    from handlers.db import PotentialSimulationDBHandler
    from surroundings.surrounding_handler import SurroundingStorageHandler
    from tasks import potential_view_tasks

    # mocks
    original_box = translate(
        box(0, 0, 10, 10), xoff=2679383.1436561393, yoff=1247282.5485680234
    )
    translated_box = project_geometry(
        geometry=original_box,
        crs_from=REGION.CH,
        crs_to=REGION.LAT_LON,
    )

    sim = PotentialSimulationDBHandler.add(
        type=SIMULATION_TYPE.SUN,
        building_footprint=translated_box,
        floor_number=2,
        layout_mode=POTENTIAL_LAYOUT_MODE.WITH_WINDOWS,
        status=POTENTIAL_SIMULATION_STATUS.PENDING,
        simulation_version=SIMULATION_VERSION.PH_2022_H1,
        source_surr=SURROUNDING_SOURCES.SWISSTOPO,
        region=REGION.CH.name,
    )

    mock_elevation(100)

    mocker.patch.object(
        SurroundingStorageHandler,
        SurroundingStorageHandler._download_uncompress_surroundings_to_folder.__name__,
    )

    spy_add_windows_and_walls = mocker.spy(
        PotentialLayoutWithWindows, "_add_perimeter_windows_and_walls"
    )

    # run potential view
    potential_view_tasks.get_potential_quavis_simulation_chain(
        simulation_id=sim["id"]
    ).delay().get()

    # results
    simulation = PotentialSimulationDBHandler.get_by(id=sim["id"])
    assert simulation["status"] == POTENTIAL_SIMULATION_STATUS.SUCCESS.value

    assert spy_add_windows_and_walls.called

    assert not DeepDiff(
        simulation["result"],
        expected_potential_view_results,
        significant_digits=2,
    )
    assert mocked_quavis_gcp_handler.delete_counter == 1


def test_simulation_error(pending_simulation):
    exc = Exception("Bla Bla Bla")
    simulation_error(None, exc, None, pending_simulation["run_id"])
    simulation_db = SlamSimulationDBHandler.get_by(run_id=pending_simulation["run_id"])
    assert simulation_db["state"] == ADMIN_SIM_STATUS.FAILURE.value
    assert simulation_db["errors"] == {"msg": str(exc), "code": type(exc).__name__}
