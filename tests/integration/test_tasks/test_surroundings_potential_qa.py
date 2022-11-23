from common_utils.constants import REGION, SURROUNDING_SOURCES
from handlers.db import PotentialSimulationDBHandler
from tests.db_fixtures import login_as


@login_as(["POTENTIAL_NIGHTLY"])
def test_task_potential_nightly_call(
    client_db, mocker, celery_eager, login, mocked_geolocator, overpass_api_mocked
):
    from tasks import (
        potential_view_tasks,
        quavis_tasks,
        surroundings_nightly_tasks,
        surroundings_tasks,
    )

    footprint = "010300000001000000050000008677D01560B020403BC7BB3BE1AB4740251E799B72B020407672F361E4AB4740BE59BB7C7EB02040CE10885DE2AB47403B124F436EB02040BC4677D3DEAB47408677D01560B020403BC7BB3BE1AB4740"

    places_for_test = {
        "place1": (
            footprint,
            [3],
            REGION.CH,
            SURROUNDING_SOURCES.SWISSTOPO,
        ),
        "place2": (
            footprint,
            [3],
            REGION.CH,
            SURROUNDING_SOURCES.OSM,
        ),
    }
    mocker.patch.object(
        surroundings_nightly_tasks,
        "SURROUNDINGS_LOCATIONS_PERIODIC_QA",
        places_for_test,
    )

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
    surroundings_nightly_tasks.run_potential_surrounding_quality()

    num_simulation_types = 2
    num_simulation_versions = 2
    expected_count = len(places_for_test) * num_simulation_versions

    # Surr generation does not change for the diff simulation types
    assert expected_count == mocked_surr_gen.call_count
    for task in mocked_tasks:
        assert task.call_count == expected_count * num_simulation_types

    assert (
        len(PotentialSimulationDBHandler.find())
        == len(places_for_test) * num_simulation_types * num_simulation_versions
    )
