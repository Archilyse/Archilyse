from collections import defaultdict
from dataclasses import asdict

from common_utils.constants import (
    COUNTRY_CODE,
    REGION,
    TASK_TYPE,
    UNIT_BASICS_DIMENSION,
    UNIT_USAGE,
)
from handlers import SlamSimulationHandler
from handlers.custom_valuator_pricing.cv_api import CustomValuatorApi
from handlers.custom_valuator_pricing.cv_api_model import (
    ValuationRequest,
    ValuationResponse,
)
from handlers.db import BuildingDBHandler, FloorDBHandler, SiteDBHandler, UnitDBHandler
from handlers.ph_vector.ph2022 import AreaVector
from handlers.utils import get_simulation_name


class CustomValuatorApiHandler:
    @staticmethod
    def _get_residential_units_info(site_id: int) -> list[dict]:
        return UnitDBHandler.find(
            site_id=site_id,
            unit_usage=UNIT_USAGE.RESIDENTIAL.name,
            output_columns=["id", "client_id", "floor_id"],
        )

    @classmethod
    def _get_building_info(cls, site_id: int, building_year: int) -> dict[str, dict]:
        site = SiteDBHandler.get_by(id=site_id, output_columns=["georef_region"])
        buildings = {
            building.pop("id"): {
                "country": COUNTRY_CODE[REGION[site["georef_region"]]],
                "city": building["city"],
                "post_code": building["zipcode"],
                "street": building["street"],
                "house_number": building["housenumber"],
                "building_year": building_year,
            }
            for building in BuildingDBHandler.find(
                site_id=site_id,
                output_columns=["id", "city", "zipcode", "street", "housenumber"],
            )
        }
        building_ids = {
            floor["id"]: floor["building_id"]
            for floor in FloorDBHandler.find_in(
                building_id=list(buildings.keys()), output_columns=["id", "building_id"]
            )
        }
        return {
            unit["client_id"]: buildings[building_ids[unit["floor_id"]]]
            for unit in cls._get_residential_units_info(site_id=site_id)
        }

    @staticmethod
    def _get_area_vectors(site_id: int) -> dict[str, list]:
        area_vector_by_apartment_id = defaultdict(list)
        for room in AreaVector(site_id=site_id).get_vector(
            representative_units_only=False
        ):
            room_dict = asdict(room)
            area_vector_by_apartment_id[room_dict.pop("apartment_id")].append(room_dict)
        return area_vector_by_apartment_id

    @classmethod
    def _get_net_areas(cls, site_id: int) -> dict[str, float]:
        basic_features = SlamSimulationHandler.get_latest_results(
            site_id=site_id, task_type=TASK_TYPE.BASIC_FEATURES, success_only=True
        )
        return {
            unit["client_id"]: basic_features[unit["id"]][0][
                get_simulation_name(dimension=UNIT_BASICS_DIMENSION.NET_AREA)
            ]
            for unit in cls._get_residential_units_info(site_id=site_id)
        }

    @staticmethod
    def _valuation_request(
        site_id: int,
        building_info: dict[str, dict],
        area_vectors: dict[str, list[dict]],
    ) -> ValuationRequest:
        return ValuationRequest(
            **{
                "project_id": site_id,
                "units": [
                    {
                        "unit_id": apartment_id,
                        "property_subcode": "apartment_normal",
                        "room_simulations": area_vectors[apartment_id],
                        **building_info,
                    }
                    for apartment_id, building_info in building_info.items()
                ],
            }
        )

    @staticmethod
    def _format_valuation_response(
        valuation_response: ValuationResponse, net_areas: dict[str, float]
    ) -> list[dict]:
        return [
            {
                "client_unit_id": client_unit_id,
                "ph_final_gross_rent_annual_m2": (
                    final_valuation / net_areas[client_unit_id]
                )
                * 12,
                "ph_final_gross_rent_adj_factor": adjustment_factor,
            }
            for client_unit_id, final_valuation, adjustment_factor in zip(
                valuation_response.unit_id,
                valuation_response.final_valuation,
                valuation_response.adjustment_factor,
            )
        ]

    @classmethod
    def get_valuation_results(cls, site_id: int, building_year: int) -> list[dict]:
        """
        Building year should come from site or building db model eventually
        """
        building_info = cls._get_building_info(
            site_id=site_id, building_year=building_year
        )
        area_vectors = cls._get_area_vectors(site_id=site_id)
        valuation_response = CustomValuatorApi.get_valuation(
            valuation_request=cls._valuation_request(
                site_id=site_id,
                building_info=building_info,
                area_vectors=area_vectors,
            )
        )
        return cls._format_valuation_response(
            valuation_response=valuation_response,
            net_areas=cls._get_net_areas(site_id=site_id),
        )
