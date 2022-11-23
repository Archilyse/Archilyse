from brooks.util.projections import project_geometry
from common_utils.constants import REGION
from handlers.db import PotentialSimulationDBHandler
from tasks import potential_view_tasks, quavis_tasks, surroundings_tasks
from tasks.potential_view_tasks import potential_simulate_area


def test_potential_simulate_area(
    mocker,
    celery_eager,
    mocked_geolocator,
    mocked_swiss_topo_building_files_and_location,
    potential_sim_location,
):
    NUM_UNIQUE_BUILDINGS = 3
    NUM_FLOORS = [4, 6, 5]
    SIM_TYPES = 2  # VIEW and SUN simulations

    mocked_surr_gen = mocker.patch.object(
        surroundings_tasks.generate_surroundings_for_potential_task,
        "run",
        return_value=True,
    )
    mocked_tasks = [
        mocker.patch.object(task, "run", return_value=True)
        for task in (
            potential_view_tasks.configure_quavis_potential_task,
            quavis_tasks.run_quavis_task,
            potential_view_tasks.store_quavis_results_potential_task,
            potential_view_tasks.delete_potential_simulation_artifacts,
        )
    ]

    lon, lat = map(
        lambda x: x[0],
        project_geometry(
            geometry=potential_sim_location,
            crs_from=REGION.CH,
            crs_to=REGION.LAT_LON,
        ).xy,
    )
    potential_simulate_area.delay(lat=lat, lon=lon, bounding_box_extension=30)

    assert mocked_surr_gen.call_count == NUM_UNIQUE_BUILDINGS
    for mocked_task in mocked_tasks:
        assert mocked_task.call_count == sum(NUM_FLOORS) * SIM_TYPES

    sims = PotentialSimulationDBHandler.find()
    assert len(sims) == sum(NUM_FLOORS) * SIM_TYPES
    assert len({s["building_footprint"] for s in sims}) == NUM_UNIQUE_BUILDINGS
    assert max({s["floor_number"] for s in sims}) == max(NUM_FLOORS) - 1  # starts at 0
    assert min({s["floor_number"] for s in sims}) == 0
