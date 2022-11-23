from deepdiff import DeepDiff

from common_utils.constants import SIMULATION_VERSION
from handlers.db import ClusteringSubsamplingDBHandler, SiteDBHandler, UnitDBHandler
from handlers.ph_vector import PHResultVectorHandler
from tasks.clustering_units_tasks import clustering_units_task


def test_clustering_units_task(
    mocker,
    celery_eager,
    units_vector_fixture_for_clustering,
    expected_unit_clusters,
    site,
    plan,
    floor,
):
    # Ensure we use the right PHResultVectorHandler
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"simulation_version": SIMULATION_VERSION.PH_01_2021.value},
    )
    mocker.patch.object(
        PHResultVectorHandler,
        PHResultVectorHandler.generate_apartment_vector.__name__,
        return_value=units_vector_fixture_for_clustering,
    )
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"sub_sampling_number_of_clusters": 6}
    )
    # prepare one unit per client_id
    for i, client_id in enumerate(units_vector_fixture_for_clustering.keys()):
        UnitDBHandler.add(
            site_id=site["id"],
            plan_id=plan["id"],
            floor_id=floor["id"],
            apartment_no=i,
            client_id=client_id,
        )

    # add janitor, commercial and placeholder units which should be excluded
    UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=len(units_vector_fixture_for_clustering),
        client_id="janitor_unit",
    )
    UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=len(units_vector_fixture_for_clustering) + 1,
        client_id="gewerbe_unit",
    )
    UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=len(units_vector_fixture_for_clustering) + 2,
        client_id="placeholder",
    )

    # clustering
    clustering_units_task.delay(site_id=site["id"])

    unit_data = UnitDBHandler.find(
        site_id=site["id"],
        output_columns=["client_id", "representative_unit_client_id"],
    )

    # make it a dict by representative_unit_client_id
    expected_unit_clusters = {c[1]: c[0] for c in expected_unit_clusters}
    # Due to the post checks
    expected_unit_clusters["00.L"] = ["00.L"]
    expected_unit_clusters["00.R"] = ["00.R"]

    for unit in unit_data:
        if unit["client_id"] in {"janitor_unit", "gewerbe_unit", "placeholder"}:
            assert not unit["representative_unit_client_id"]
        else:
            cluster = expected_unit_clusters[unit["representative_unit_client_id"]]
            assert unit["client_id"] in cluster

    # Check Cluster Subsampling data is saved
    cluster_subsamplings = ClusteringSubsamplingDBHandler.find()
    assert len(cluster_subsamplings) == 1
    assert not DeepDiff(
        cluster_subsamplings[0]["results"], expected_unit_clusters, ignore_order=True
    )


def test_clustering_units_task_1_unit(
    mocker,
    celery_eager,
    units_vector_fixture_for_clustering,
    expected_unit_clusters,
    site,
    plan,
    floor,
):
    # Ensure we use the right PHResultVectorHandler
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"simulation_version": SIMULATION_VERSION.PH_01_2021.value},
    )
    random_unit_client_id = list(units_vector_fixture_for_clustering.keys())[0]
    mocker.patch.object(
        PHResultVectorHandler,
        PHResultVectorHandler.generate_apartment_vector.__name__,
        return_value={
            random_unit_client_id: units_vector_fixture_for_clustering[
                random_unit_client_id
            ]
        },
    )
    # prepare ONLY one unit
    UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=0,
        client_id=random_unit_client_id,
    )

    clustering_units_task.delay(site_id=site["id"])
    unit = UnitDBHandler.get_by(
        client_id=random_unit_client_id,
        output_columns=["client_id", "representative_unit_client_id"],
    )

    # make it a dict by representative_unit_client_id
    expected_unit_clusters = {c[1]: c[0] for c in expected_unit_clusters}

    cluster = expected_unit_clusters[unit["representative_unit_client_id"]]
    assert unit["client_id"] in cluster
