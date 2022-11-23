import json
import os
import shutil
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from deepdiff import DeepDiff

from bin.datastory.bulk_export_vectors import VectorGenerator
from common_utils.constants import ADMIN_SIM_STATUS, SIMULATION_VERSION, UNIT_USAGE
from handlers.db import SiteDBHandler, UnitDBHandler
from handlers.ph_vector.ph2022 import AreaVector
from tests.utils import load_csv_as_dict


class TestAreaVector:
    def test_get_units_info_returns_residential_units_only(self, site, floor):
        UnitDBHandler.bulk_insert(
            items=[
                {
                    "site_id": site["id"],
                    "floor_id": floor["id"],
                    "plan_id": floor["plan_id"],
                    "unit_usage": usage_type.name,
                    "apartment_no": i,
                }
                for i, usage_type in enumerate(UNIT_USAGE)
            ]
        )
        residential_units = list(
            AreaVector(site_id=site["id"])._get_units_info(
                representative_units_only=False
            )
        )
        assert len(residential_units) == 1
        assert UnitDBHandler.exists(
            id=residential_units[0]["id"], unit_usage=UNIT_USAGE.RESIDENTIAL.name
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_2022_H1], indirect=True
    )
    def test_get_vector(
        self,
        site_with_simulation_results,
        expected_room_vector_with_balcony_ph2022,
        fixtures_path,
        update_fixture: bool = False,
    ):
        site_id = site_with_simulation_results["id"]
        vector_as_dicts = list(
            map(
                asdict,
                AreaVector(site_id=site_id).get_vector(representative_units_only=False),
            )
        )
        if update_fixture:
            with open(
                fixtures_path.joinpath("vectors/room_vector_with_balcony_ph2022.json"),
                mode="w",
            ) as f:
                json.dump(vector_as_dicts, f)
        assert not DeepDiff(
            expected_room_vector_with_balcony_ph2022,
            vector_as_dicts,
            ignore_order=True,
            significant_digits=6,
        )

    @pytest.mark.parametrize(
        "site_with_simulation_results", [SIMULATION_VERSION.PH_2022_H1], indirect=True
    )
    def test_dataset_vector_export(
        self,
        site_with_simulation_results,
        expected_room_vector_with_balcony_ph2022,
        neufert_expected_room_vector_with_balcony,
        neufert_expected_vector_unit_geometry,
        fixtures_path,
        update_fixtures: bool = False,
    ):
        site_id = site_with_simulation_results["id"]
        client_id = site_with_simulation_results["client_id"]
        SiteDBHandler.update(
            item_pks={"id": site_id},
            new_values={"full_slam_results": ADMIN_SIM_STATUS.SUCCESS.name},
        )

        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)

            generator = VectorGenerator(
                client_ids={client_id}, vector_dir=temp_dir_path
            )
            generator.generate_vectors()
            generator.generate_geometries()

            room_vector_path = temp_dir_path.joinpath("simulations.csv")
            geometry_vector_path = temp_dir_path.joinpath("geometries.csv")
            if update_fixtures:
                room_vector_fixture_path = fixtures_path.joinpath(
                    "vectors/neufert_expected_room_vector_with_balcony.csv"
                )
                os.remove(room_vector_fixture_path)
                shutil.copy(room_vector_path, room_vector_fixture_path)

                geometry_vector_fixture_path = fixtures_path.joinpath(
                    "vectors/neufert_expected_vector_unit_geometry.csv"
                )
                os.remove(geometry_vector_fixture_path)
                shutil.copy(geometry_vector_path, geometry_vector_fixture_path)

            else:
                assert not DeepDiff(
                    load_csv_as_dict(filepath=room_vector_path),
                    neufert_expected_room_vector_with_balcony,
                    ignore_order=True,
                )
                assert not DeepDiff(
                    load_csv_as_dict(filepath=geometry_vector_path),
                    neufert_expected_vector_unit_geometry,
                    ignore_order=True,
                )
