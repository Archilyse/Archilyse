from dataclasses import asdict

import pytest

from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from handlers.custom_valuator_pricing.cv_api import CustomValuatorApi
from handlers.custom_valuator_pricing.cv_api_handler import CustomValuatorApiHandler
from handlers.custom_valuator_pricing.cv_api_model import (
    ValuationRequest,
    ValuationResponse,
)
from handlers.db import SlamSimulationDBHandler, UnitSimulationDBHandler
from handlers.ph_vector.ph2022 import AreaVector, AreaVectorSchema


class TestCustomValuatorApiHandler:
    @pytest.fixture
    def fake_api(self, mocker, unit):
        gross_monthly_apartment_rent = 2000
        adjustment_factor = 1.2
        return mocker.patch.object(
            CustomValuatorApi,
            "get_valuation",
            return_value=ValuationResponse(
                unit_id=[unit["client_id"]],
                avm_valuation=[gross_monthly_apartment_rent],
                final_valuation=[gross_monthly_apartment_rent * adjustment_factor],
                adjustment_factor=[adjustment_factor],
            ),
        )

    @pytest.fixture
    def fake_net_areas(self, site, unit):
        SlamSimulationDBHandler.add(
            run_id="fake run",
            site_id=site["id"],
            type=TASK_TYPE.BASIC_FEATURES.name,
            state=ADMIN_SIM_STATUS.SUCCESS.name,
        )
        UnitSimulationDBHandler.add(
            run_id="fake run",
            unit_id=unit["id"],
            results=[{"UnitBasics.net-area": 120.0}],
        )

    @pytest.fixture
    def fake_area_vector(self, mocker, unit):
        area_vector_data = {
            "apartment_id": unit["client_id"],
            "layout_compactness": 1.0,
            "layout_is_navigable": True,
            "layout_mean_walllengths": 1.0,
            "layout_area": 1.0,
            "layout_net_area": 1.0,
            "layout_room_count": 1.0,
            "layout_std_walllengths": 1.0,
            "layout_area_type": "BALCONY",
            "layout_number_of_doors": 1,
            "layout_number_of_windows": 4,
            "layout_has_sink": True,
            "layout_has_shower": True,
            "layout_has_bathtub": True,
            "layout_has_stairs": True,
            "layout_has_entrance_door": True,
            "layout_has_toilet": True,
            "layout_perimeter": 1.0,
            "layout_door_perimeter": 1.0,
            "layout_window_perimeter": 1.0,
            "layout_open_perimeter": 1.0,
            "layout_railing_perimeter": 1.0,
            "layout_connects_to_bathroom": True,
            "layout_connects_to_private_outdoor": True,
            "floor_number": 1,
            "floor_has_elevator": False,
            "layout_biggest_rectangle_length": 10.0,
            "layout_biggest_rectangle_width": 1.0,
        }
        return mocker.patch.object(
            AreaVector,
            "get_vector",
            return_value=[AreaVectorSchema(**area_vector_data)],
        )

    def test_get_custom_valuation_results(
        self, unit, fake_api, fake_net_areas, fake_area_vector
    ):
        assert CustomValuatorApiHandler.get_valuation_results(
            site_id=unit["site_id"], building_year=-9999
        ) == [
            {
                "client_unit_id": unit["client_id"],
                "ph_final_gross_rent_annual_m2": 240,
                "ph_final_gross_rent_adj_factor": 1.2,
            }
        ]

    def test_get_custom_valuation_results_calls_api(
        self, building, unit, fake_api, fake_net_areas, fake_area_vector
    ):
        site_id = 1
        building_year = 2022

        CustomValuatorApiHandler.get_valuation_results(
            site_id=site_id, building_year=building_year
        )

        (expected_room_simulation,) = fake_area_vector.return_value
        expected_room_simulation = asdict(expected_room_simulation)
        expected_room_simulation.pop("apartment_id")

        fake_api.assert_called_once_with(
            valuation_request=ValuationRequest(
                **{
                    "project_id": site_id,
                    "units": [
                        {
                            "unit_id": unit["client_id"],
                            "street": building["street"],
                            "house_number": building["housenumber"],
                            "city": building["city"],
                            "post_code": building["zipcode"],
                            "building_year": building_year,
                            "country": "CH",
                            "property_subcode": "apartment_normal",
                            "room_simulations": [expected_room_simulation],
                        }
                    ],
                }
            )
        )
