import os
from collections import defaultdict
from typing import DefaultDict

import requests

from common_utils.chunker import chunker
from common_utils.exceptions import CustomValuatorApiException
from handlers.custom_valuator_pricing.cv_api_model import (
    ValuationRequest,
    ValuationResponse,
)


class CustomValuatorApi:
    BATCH_SIZE = 50

    @staticmethod
    def _validate_response(request: dict, response: requests.Response):
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise CustomValuatorApiException(response.text) from e

        delivered_unit_ids = set(response.json()["unit_id"])
        expected_unit_ids = set(u["unit_id"] for u in request["units"])
        if missing_ids := expected_unit_ids - delivered_unit_ids:
            raise CustomValuatorApiException(
                f"For the following ids no valuation was returned: {missing_ids}"
            )
        if unknown_ids := delivered_unit_ids - expected_unit_ids:
            raise CustomValuatorApiException(
                f"For the following ids are unknown: {unknown_ids}"
            )

    @classmethod
    def get_valuation(cls, valuation_request: ValuationRequest) -> ValuationResponse:
        valuation_request = valuation_request.dict()
        response_aggregated: DefaultDict[str, list] = defaultdict(list)

        for batch in chunker(valuation_request["units"], cls.BATCH_SIZE):
            request_json = {**valuation_request, "units": batch}
            response = requests.post(
                os.environ["CUSTOM_VALUATOR_API_URL"],
                params={"api-key": os.environ["CUSTOM_VALUATOR_API_KEY"]},
                json=request_json,
            )
            cls._validate_response(request=request_json, response=response)
            for k, v in response.json().items():
                response_aggregated[k] += v

        return ValuationResponse(**response_aggregated)
