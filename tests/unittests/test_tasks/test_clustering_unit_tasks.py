import pytest
from deepdiff import DeepDiff

from common_utils.constants import SIMULATION_VERSION
from common_utils.exceptions import DependenciesUnMetSimulationException
from handlers import UnitHandler
from handlers.db import (
    ClusteringSubsamplingDBHandler,
    FloorDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.ph_vector import PHResultVectorHandler
from tasks.clustering_units_tasks import (
    cluster_checks_fixer,
    clustering_units_task,
    get_number_of_clusters,
)


@pytest.mark.parametrize(
    "sub_sampling_number_of_clusters, total_number_of_units, expected_number_of_clusters",
    [
        (None, 10, 3),
        (5, 10, 5),
    ],
)
def test_get_number_of_clusters(
    mocker,
    sub_sampling_number_of_clusters,
    total_number_of_units,
    expected_number_of_clusters,
):
    mocker.patch.object(
        SiteDBHandler,
        "get_by",
        return_value={
            "sub_sampling_number_of_clusters": sub_sampling_number_of_clusters
        },
    )
    assert (
        get_number_of_clusters(
            site_id=mocker.ANY,
            total_number_of_units=total_number_of_units,
        )
        == expected_number_of_clusters
    )


def test_clustering_units_task_empty(mocker):
    mocker.patch.object(UnitDBHandler, "find", return_value=[])
    mocker.patch.object(
        FloorDBHandler,
        FloorDBHandler.find_by_site_id.__name__,
        return_value=[],
    )

    mocker.patch.object(
        SiteDBHandler,
        SiteDBHandler.get_by.__name__,
        return_value={"simulation_version": SIMULATION_VERSION.PH_01_2021.value},
    )
    mocker.patch.object(
        PHResultVectorHandler, "generate_apartment_vector", return_value={}
    )
    mocked_add = mocker.patch.object(ClusteringSubsamplingDBHandler, "add")
    clustering_units_task(site_id=1)
    mocked_add.assert_not_called()


def test_clustering_units_task_only_one_unit(mocker):
    mocker.patch.object(
        SiteDBHandler,
        SiteDBHandler.get_by.__name__,
        return_value={"simulation_version": SIMULATION_VERSION.PH_01_2021.value},
    )
    mocker.patch.object(
        FloorDBHandler,
        FloorDBHandler.find_by_site_id.__name__,
        return_value=[{"id": 1, "floor_number": 1}],
    )
    mocker.patch.object(
        UnitDBHandler, "find", return_value=[{"client_id": "1", "floor_id": 1}]
    )
    mocker.patch.object(
        PHResultVectorHandler,
        PHResultVectorHandler.generate_apartment_vector.__name__,
        return_value={
            "1": {"UnitBasics.number-of-rooms": 3.5, "UnitBasics.net-area": 100}
        },
    )
    mocked_add = mocker.patch.object(ClusteringSubsamplingDBHandler, "add")
    mocked_update_units = mocker.patch.object(
        UnitHandler, "update_units_representative"
    )
    clustering_units_task(site_id=1)
    results = {"1": ["1"]}
    mocked_add.assert_called_once_with(site_id=1, results=results)
    mocked_update_units.assert_called_once_with(
        site_id=1, clustering_subsampling=results
    )


def test_clustering_unlinked_unit(mocker):
    with pytest.raises(DependenciesUnMetSimulationException):
        mocker.patch.object(
            UnitDBHandler, "find", return_value=[{"client_id": None, "floor_id": None}]
        )
        mocker.patch.object(
            FloorDBHandler,
            FloorDBHandler.find_by_site_id.__name__,
            return_value=[],
        )
        clustering_units_task(site_id=1)


def test_cluster_checks_fixer():
    clustering = {
        "1.1": ["1.1", "3"],  # Floors too far away
        "1.2": ["1.2", "2"],  # Some floors far away but one is close
        "1.3": ["1.3", "4"],  # Different room count
        "1.4": ["1.4", "5"],  # net area too different
    }
    base_config = {"UnitBasics.net-area": 100, "UnitBasics.number-of-rooms": 3.5}
    unit_vectors = {
        "1.1": base_config,
        "1.2": base_config,
        "1.3": base_config,
        "1.4": base_config,
        "2": base_config,
        "3": base_config,
        "4": base_config | {"UnitBasics.number-of-rooms": 4},
        "5": base_config | {"UnitBasics.net-area": 50},
    }
    units_floor_numbers = {
        "1.1": [1],
        "1.2": [4, 5],
        "1.3": [1],
        "1.4": [1],
        "2": [2, 3],
        "3": [7],
        "4": [1],
        "5": [1],
    }

    expected_clustering = {
        "1.1": ["1.1"],  # Floors too far away
        "3": ["3"],  # Floors too far away
        "1.2": ["1.2", "2"],  # Some floors far away but one is close
        "1.3": ["1.3"],  # Different room count
        "4": ["4"],  # Different room count
        "1.4": ["1.4"],  # net area too different
        "5": ["5"],  # net area too different
    }
    new_clustering = cluster_checks_fixer(
        clustering=clustering,
        unit_vectors=unit_vectors,
        units_floor_numbers=units_floor_numbers,
    )
    assert not DeepDiff(new_clustering, expected_clustering, ignore_order=True)
