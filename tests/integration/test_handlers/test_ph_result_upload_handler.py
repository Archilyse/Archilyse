from typing import Dict, List

import pytest
from deepdiff import DeepDiff

from common_utils.exceptions import DBException
from handlers.db import SiteDBHandler, UnitDBHandler
from handlers.ph_results_upload_handler import CVResultUploadHandler
from tests.constants import CLIENT_ID_1, CLIENT_ID_2


class TestCVResultUploadHandler:
    @pytest.fixture
    def expected_units_info_non_residential(self, non_residential_units):
        return [
            {"client_id": unit["client_id"], "ph_final_gross_rent_annual_m2": None}
            for unit in non_residential_units
        ]

    @pytest.fixture
    def site_clustering(self, site):
        def _internal(enable_clustering: bool):
            n_clusters = None
            if enable_clustering:
                n_clusters = 999
            SiteDBHandler.update(
                item_pks={"id": site["id"]},
                new_values={"sub_sampling_number_of_clusters": n_clusters},
            )

        return _internal

    @pytest.fixture
    def residential_units(self, site, floor, floor2, make_units):
        units = make_units(floor, floor2)
        UnitDBHandler.bulk_update(
            client_id={
                units[0]["id"]: CLIENT_ID_1,
                units[1]["id"]: CLIENT_ID_2,
            },
            representative_unit_client_id={
                units[0]["id"]: CLIENT_ID_1,
                units[1]["id"]: CLIENT_ID_1,
            },
        )
        return [UnitDBHandler.get_by(id=unit["id"]) for unit in units]

    def test_get_expected_client_ids_with_clustering(
        self, site, site_clustering, residential_units, non_residential_units
    ):
        site_clustering(enable_clustering=True)
        client_ids = CVResultUploadHandler._get_expected_client_ids(site_id=site["id"])
        assert not DeepDiff(
            {CLIENT_ID_1: [unit["id"] for unit in residential_units]},
            dict(client_ids),
            ignore_order=True,
        )

    def test_get_expected_client_ids_no_clustering(
        self, site, site_clustering, residential_units, non_residential_units
    ):
        site_clustering(enable_clustering=False)
        client_ids = CVResultUploadHandler._get_expected_client_ids(site_id=site["id"])
        assert client_ids == {
            CLIENT_ID_1: [residential_units[0]["id"]],
            CLIENT_ID_2: [residential_units[1]["id"]],
        }

    ph_results_clustered = [
        {"client_unit_id": CLIENT_ID_1, "ph_final_gross_rent_annual_m2": 100}
    ]
    ph_results_not_clustered = [
        *ph_results_clustered,
        {"client_unit_id": CLIENT_ID_2, "ph_final_gross_rent_annual_m2": 200},
    ]
    expected_units_info_residential_clustered = [
        {"client_id": CLIENT_ID_1, "ph_final_gross_rent_annual_m2": 100},
        {"client_id": CLIENT_ID_2, "ph_final_gross_rent_annual_m2": 100},
    ]
    expected_units_info_residential_not_clustered = [
        {"client_id": CLIENT_ID_1, "ph_final_gross_rent_annual_m2": 100},
        {"client_id": CLIENT_ID_2, "ph_final_gross_rent_annual_m2": 200},
    ]

    @pytest.mark.parametrize(
        "clustering_enabled, ph_results, expected_units_info_residential",
        [
            (True, ph_results_clustered, expected_units_info_residential_clustered),
            (
                False,
                ph_results_not_clustered,
                expected_units_info_residential_not_clustered,
            ),
        ],
    )
    def test_update_custom_valuator_results_clustering(
        self,
        site,
        site_clustering,
        residential_units,
        non_residential_units,
        expected_units_info_non_residential,
        expected_units_info_residential,
        clustering_enabled,
        ph_results: List[Dict],
    ):
        # Given
        site_clustering(enable_clustering=clustering_enabled)

        # When
        CVResultUploadHandler.update_custom_valuator_results(
            site_id=site["id"], custom_valuator_results=ph_results
        )

        # Then
        units_info = UnitDBHandler.find(
            site_id=site["id"],
            output_columns=["client_id", "ph_final_gross_rent_annual_m2"],
        )
        expected_units_info = [
            *expected_units_info_residential,
            *expected_units_info_non_residential,
        ]
        assert not DeepDiff(expected_units_info, units_info, ignore_order=True)

    ph_results = [
        {"client_unit_id": CLIENT_ID_1, "ph_final_sale_price_m2": 200.0},
        {"client_unit_id": CLIENT_ID_2, "ph_final_sale_price_m2": 200.0},
    ]
    ph_results_duplicated_client_id = ph_results + [ph_results[-1]]
    ph_results_with_unknown_client_id = ph_results + [
        {"client_unit_id": "UNKNOWN", "ph_final_sale_price_m2": 200.0}
    ]
    ph_results_with_missing_client_id = ph_results[:-1]

    @pytest.mark.parametrize(
        "ph_results, expected_error_message",
        [
            (
                ph_results_duplicated_client_id,
                "custom_valuator_results contains 1 more elements than expected. Does the file contain duplicates?",
            ),
            (
                ph_results_with_unknown_client_id,
                "custom_valuator_results contains unknown client unit ids.",
            ),
            (
                ph_results_with_missing_client_id,
                "custom_valuator_results does not contain all expected client unit ids.",
            ),
            ([], "custom_valuator_results must not be empty."),
        ],
    )
    def test_update_custom_valuator_results_validates_ph_results(
        self, site, residential_units, ph_results, expected_error_message
    ):
        with pytest.raises(DBException) as e:
            CVResultUploadHandler.update_custom_valuator_results(
                site_id=site["id"], custom_valuator_results=ph_results
            )
        assert expected_error_message in str(e.value)

    def test_update_custom_valuator_results_does_not_modify_non_existing_values(
        self, site, residential_units
    ):
        # Given
        UnitDBHandler.bulk_update(
            **{
                field: {unit["id"]: 100.0 for unit in residential_units[:2]}
                for field in [
                    "ph_final_gross_rent_annual_m2",
                    "ph_final_gross_rent_adj_factor",
                    "ph_final_sale_price_m2",
                    "ph_final_sale_price_adj_factor",
                ]
            }
        )
        ph_results = [
            {"client_unit_id": CLIENT_ID_1, "ph_final_gross_rent_annual_m2": 200.0},
            {"client_unit_id": CLIENT_ID_2, "ph_final_gross_rent_annual_m2": 400.0},
        ]

        CVResultUploadHandler.update_custom_valuator_results(
            site_id=site["id"], custom_valuator_results=ph_results
        )
        units_info = UnitDBHandler.find(
            site_id=site["id"],
            output_columns=[
                "client_id",
                "ph_final_gross_rent_annual_m2",
                "ph_final_gross_rent_adj_factor",
                "ph_final_sale_price_m2",
                "ph_final_sale_price_adj_factor",
            ],
        )

        assert not DeepDiff(
            units_info,
            [
                {
                    "client_id": CLIENT_ID_1,
                    "ph_final_sale_price_m2": 100,
                    "ph_final_gross_rent_annual_m2": 200.0,
                    "ph_final_gross_rent_adj_factor": 100,
                    "ph_final_sale_price_adj_factor": 100,
                },
                {
                    "client_id": CLIENT_ID_2,
                    "ph_final_sale_price_m2": 100.0,
                    "ph_final_gross_rent_annual_m2": 400,
                    "ph_final_gross_rent_adj_factor": 100,
                    "ph_final_sale_price_adj_factor": 100,
                },
            ],
            ignore_order=True,
        )
