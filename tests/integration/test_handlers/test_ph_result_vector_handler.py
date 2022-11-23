import json

import pytest
from deepdiff import DeepDiff

from common_utils.constants import SIMULATION_VERSION
from handlers.ph_vector import PHResultVectorHandler


class TestPHResultVectorHandler:
    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_01_2021], indirect=True
    )
    def test_generate_area_vector_with_balcony(
        self,
        site_with_simulation_results,
        expected_room_vector_with_balcony,
        fixtures_path,
    ):
        ph_vector_handler = PHResultVectorHandler(
            site_id=site_with_simulation_results["id"]
        )
        result = ph_vector_handler._generate_area_vector(interior_only=False)
        assert not DeepDiff(
            expected_room_vector_with_balcony,
            result,
            ignore_order=True,
            ignore_nan_inequality=True,
            significant_digits=6,
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_01_2021], indirect=True
    )
    def test_generate_area_vector_no_balcony(
        self, site_with_simulation_results, expected_room_vector_no_balcony
    ):
        ph_vector_handler = PHResultVectorHandler(
            site_id=site_with_simulation_results["id"]
        )
        result = ph_vector_handler._generate_area_vector(interior_only=True)

        assert not DeepDiff(
            expected_room_vector_no_balcony,
            result,
            ignore_order=True,
            ignore_nan_inequality=True,
            significant_digits=6,
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_01_2021], indirect=True
    )
    def test_generate_apartment_vector_with_balcony(
        self, site_with_simulation_results, expected_apartment_vector_with_balcony
    ):
        ph_vector_handler = PHResultVectorHandler(
            site_id=site_with_simulation_results["id"]
        )
        result = ph_vector_handler.generate_apartment_vector(interior_only=False)

        assert not DeepDiff(
            expected_apartment_vector_with_balcony,
            result,
            ignore_nan_inequality=True,
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_01_2021], indirect=True
    )
    def test_generate_apartment_vector_no_balcony(
        self, site_with_simulation_results, expected_apartment_vector_no_balcony
    ):
        ph_vector_handler = PHResultVectorHandler(
            site_id=site_with_simulation_results["id"]
        )
        result = ph_vector_handler.generate_apartment_vector(interior_only=True)

        assert not DeepDiff(
            expected_apartment_vector_no_balcony,
            result,
            ignore_nan_inequality=True,
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_01_2021], indirect=True
    )
    def test_generate_vectors(
        self,
        site_with_simulation_results,
        expected_apartment_vector_with_balcony,
        expected_apartment_vector_no_balcony,
        expected_room_vector_with_balcony,
        expected_room_vector_no_balcony,
        expected_full_vector_with_balcony,
        expected_full_vector_no_balcony,
        fixtures_path,
        update_fixtures: bool = False,
    ):
        site = site_with_simulation_results

        ph_vector_handler = PHResultVectorHandler(site_id=site["id"])
        actual_vectors = ph_vector_handler.generate_vectors()
        if update_fixtures:
            for vector_name, vector in actual_vectors.items():
                with fixtures_path.joinpath(f"vectors/{vector_name.value}.json").open(
                    "w"
                ) as fh:
                    json.dump(vector, fh)

        for actual_vector, expected_vector in zip(
            actual_vectors.values(),
            (
                expected_apartment_vector_with_balcony,
                expected_apartment_vector_no_balcony,
                expected_room_vector_with_balcony,
                expected_room_vector_no_balcony,
                expected_full_vector_with_balcony,
                expected_full_vector_no_balcony,
            ),
        ):
            assert not DeepDiff(
                expected_vector,
                actual_vector,
                ignore_order=True,
                ignore_nan_inequality=True,
                significant_digits=5,
            )
