import pytest
import requests

from common_utils.exceptions import CustomValuatorApiException
from handlers.custom_valuator_pricing.cv_api import CustomValuatorApi
from handlers.custom_valuator_pricing.cv_api_model import (
    ValuationRequest,
    ValuationResponse,
)


class TestCustomValuatorApi:
    @pytest.fixture
    def fake_api(self, mocker):
        def fake_post(*args, json, **kwargs):
            fake_http_response = mocker.MagicMock(spec=requests.Response, autospec=True)
            fake_http_response.json.return_value = dict(
                unit_id=[unit["unit_id"] for unit in json["units"]],
                adjustment_factor=[1.0] * len(json["units"]),
                avm_valuation=[1.0] * len(json["units"]),
                final_valuation=[1.0] * len(json["units"]),
            )
            return fake_http_response

        return mocker.patch.object(requests, "post", side_effect=fake_post)

    @pytest.fixture
    def fake_request(self, mocker):
        def _internal(number_of_units=1):
            fake_request = mocker.MagicMock(spec=ValuationRequest, autospec=True)
            fake_request.dict.return_value = dict(
                project_id="fake",
                units=[{"unit_id": str(unit_id)} for unit_id in range(number_of_units)],
            )
            return fake_request

        return _internal

    @pytest.mark.parametrize("number_of_units", [1, 3, 58])
    def test_get_valuation(self, fake_api, fake_request, number_of_units):
        valuation_request = fake_request(number_of_units=number_of_units)
        valuation_response = CustomValuatorApi.get_valuation(
            valuation_request=valuation_request
        )
        assert valuation_response == ValuationResponse(
            unit_id=list(map(str, range(number_of_units))),
            adjustment_factor=[1.0] * number_of_units,
            avm_valuation=[1.0] * number_of_units,
            final_valuation=[1.0] * number_of_units,
        )

    def test_get_valuation_batches_api_calls(self, fake_api, fake_request, mocker):
        CustomValuatorApi.get_valuation(
            valuation_request=fake_request(number_of_units=58)
        )
        fake_api.assert_has_calls(
            [
                mocker.call(
                    "https://api.fake.com/api/valuation",
                    params={"api-key": "fakekey"},
                    json=dict(
                        project_id="fake",
                        units=[
                            {"unit_id": str(unit_id)} for unit_id in range(start, stop)
                        ],
                    ),
                )
                for start, stop in [(0, 50), (50, 58)]
            ]
        )
        assert fake_api.call_count == 2

    @pytest.mark.parametrize("status_code", [400, 500])
    def test_get_valuation_on_error_status_codes(
        self, fake_request, requests_mock, status_code
    ):
        requests_mock.post(
            "https://api.fake.com/api/valuation?api-key=fakekey",
            status_code=status_code,
            json=dict(message="you win!"),
        )
        with pytest.raises(CustomValuatorApiException):
            CustomValuatorApi.get_valuation(valuation_request=fake_request())

    def test_get_valuation_missing_valuations(self, fake_request, requests_mock):
        valuation_request = fake_request(number_of_units=2)
        requests_mock.post(
            "https://api.fake.com/api/valuation?api-key=fakekey",
            json=dict(
                unit_id=["1"],
                adjustment_factor=[1.0],
                avm_valuation=[1.0],
                final_valuation=[1.0],
            ),
        )
        with pytest.raises(CustomValuatorApiException):
            CustomValuatorApi.get_valuation(valuation_request=valuation_request)
