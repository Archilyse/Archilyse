import pytest

from simulations.clustering_units import cluster_units


@pytest.fixture
def ph_data(fixtures_path):
    import csv

    # used for checking clusters actually makes sense
    with fixtures_path.joinpath(
        "clustering_units/ph_data_for_site_2657.csv"
    ).open() as f:
        return {x["Unit Identifier"]: x for x in csv.DictReader(f)}


def test_cluster_units(units_vector_fixture_for_clustering, expected_unit_clusters):
    clusters = cluster_units(
        unit_vectors=units_vector_fixture_for_clustering,
        n_clusters=round(len(units_vector_fixture_for_clustering) * 0.5),
    )
    assert list(clusters) == expected_unit_clusters


def test_cluster_units_100_percent(units_vector_fixture_for_clustering):
    # if number of clusters is too high, each cluster have one element
    clusters = list(
        cluster_units(
            unit_vectors=units_vector_fixture_for_clustering,
            n_clusters=len(units_vector_fixture_for_clustering),
        )
    )

    assert all([len(x[0]) == 1 for x in clusters])


def test_cluster_units_ph_pricing(units_vector_fixture_for_clustering, ph_data):
    def get_gross_rent(client_id):
        return float(ph_data[client_id]["Final Predicted Gross Rent (CHF monthly)"])

    clusters = cluster_units(
        unit_vectors=units_vector_fixture_for_clustering,
        n_clusters=round(len(units_vector_fixture_for_clustering) * 0.5),
    )
    approximate_site_gross_rent = sum(
        [
            get_gross_rent(center_unit_client_id) * len(cluster_client_ids)
            for cluster_client_ids, center_unit_client_id in clusters
        ]
    )
    actual_site_gross_rent = sum(
        [
            get_gross_rent(client_id)
            for client_id in units_vector_fixture_for_clustering.keys()
        ]
    )

    #  we know that the clustering have been validated to yield
    #  very similar pricing results clustering to half the units compared to the full site
    assert approximate_site_gross_rent == pytest.approx(
        actual_site_gross_rent, rel=0.05
    )
