from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import requests
from marshmallow import ValidationError

from handlers.external_api_clients.layout_predictor_client import LayoutPredictorClient


class TestLayoutPredictorClient:
    @pytest.fixture
    def api_client(self):
        return LayoutPredictorClient()

    @pytest.fixture
    def jpeg_image_bytes(self, images_path: Path):
        with images_path.joinpath("floorplan_b.jpg").open("rb") as f:
            image_bytes = f.read()
        return image_bytes

    @pytest.fixture
    def mock_upload_url(self):
        return "https://www.mock-url.com"

    @pytest.mark.parametrize(
        "rois", [[[1, 1, 1, 1]], [[0, 0, 100, 100], [100, 100, 200, 200]], None]
    )
    @pytest.mark.parametrize("scale", [None, 0.5])
    def test_request_prediction_success(
        self, api_client, requests_mock, jpeg_image_bytes, mock_upload_url, scale, rois
    ):
        # Mock the requests
        requests_mock.get(
            f"{api_client.predict_service_url}/images/upload-url",
            json={"url": mock_upload_url, "image_name": "mock_image"},
        )
        requests_mock.put(mock_upload_url, status_code=200)
        requests_mock.post(
            f"{api_client.predict_service_url}/request-prediction/icons",
            json={"icon_task": {"id": "mock_task"}},
        )

        # Call the function
        response = api_client.request_prediction(
            image_bytes=jpeg_image_bytes,
            username="mock_username",
            pixels_per_meter=50.0,
            rois=rois,
        )

        # Assert the returned task ID
        assert response["icon_task"]["id"] == "mock_task"

        # Get request (get_upload_url)
        assert requests_mock.request_history[0].headers["username"] == "mock_username"
        parsed_params = parse_qs(urlparse(requests_mock.request_history[0].url).query)
        assert parsed_params["content_type"] == ["image/jpeg"]
        # Put request (upload_image)
        assert requests_mock.request_history[1].headers["Content-Type"] == "image/jpeg"
        assert (
            requests_mock.request_history[1].headers["x-goog-content-length-range"]
            == f"0,{LayoutPredictorClient.MAX_FILE_SIZE}"
        )
        assert requests_mock.request_history[1]._request.body == jpeg_image_bytes
        # Post request (request_prediction)
        parsed_params = parse_qs(urlparse(requests_mock.request_history[2].url).query)

        assert parsed_params["image_name"] == ["mock_image"]
        assert parsed_params["pixels_per_meter"] == ["50.0"]
        if rois:
            assert parsed_params["minx"] == [str(x[0]) for x in rois]
            assert parsed_params["miny"] == [str(x[1]) for x in rois]
            assert parsed_params["maxx"] == [str(x[2]) for x in rois]
            assert parsed_params["maxy"] == [str(x[3]) for x in rois]
        else:
            assert all(
                param not in parsed_params for param in ("minx", "miny", "maxx", "maxy")
            )

    def test_request_prediction_invalid_image_bytes(self, api_client):
        with pytest.raises(ValueError, match="Cannot determine image type"):
            api_client.request_prediction(b"invalid_image_bytes", "mock_username", 0.5)

    def test_request_prediction_missing_url_or_image_name(
        self, api_client, requests_mock, jpeg_image_bytes
    ):
        # Mock the GET request to return an empty JSON object
        requests_mock.get(
            f"{api_client.predict_service_url}/images/upload-url", json={}
        )

        with pytest.raises(ValidationError):
            api_client.request_prediction(jpeg_image_bytes, "mock_username", 1.0)

    def test_request_prediction_missing_task_id(
        self, api_client, requests_mock, mock_upload_url, jpeg_image_bytes
    ):
        # Mock requests
        requests_mock.get(
            f"{api_client.predict_service_url}/images/upload-url",
            json={"url": mock_upload_url, "image_name": "mock_image"},
        )
        requests_mock.put(mock_upload_url, status_code=200)

        # Mock the POST request to return an empty JSON object
        requests_mock.post(
            f"{api_client.predict_service_url}/request-prediction/icons", json={}
        )

        with pytest.raises(ValidationError):
            api_client.request_prediction(jpeg_image_bytes, "mock_username", 1.0)

    def test_request_prediction_get_failure(
        self, api_client, requests_mock, jpeg_image_bytes, mock_upload_url
    ):
        # Mock the requests
        requests_mock.get(
            f"{api_client.predict_service_url}/images/upload-url",
            status_code=500,
        )

        with pytest.raises(requests.exceptions.HTTPError):
            api_client.request_prediction(jpeg_image_bytes, "mock_username", 1.0)

    def test_request_prediction_put_failure(
        self, api_client, requests_mock, jpeg_image_bytes, mock_upload_url
    ):
        # Mock the requests
        requests_mock.get(
            f"{api_client.predict_service_url}/images/upload-url",
            json={"url": mock_upload_url, "image_name": "mock_image"},
        )
        requests_mock.put(mock_upload_url, status_code=500)

        with pytest.raises(requests.exceptions.HTTPError):
            api_client.request_prediction(jpeg_image_bytes, "mock_username", 1.0)

    def test_request_prediction_post_failure(
        self, api_client, requests_mock, jpeg_image_bytes, mock_upload_url
    ):
        # Mock the requests
        requests_mock.get(
            f"{api_client.predict_service_url}/images/upload-url",
            json={"url": mock_upload_url, "image_name": "mock_image"},
        )
        requests_mock.put(mock_upload_url, status_code=200)
        requests_mock.post(
            f"{api_client.predict_service_url}/request-prediction/icons",
            status_code=500,
        )

        with pytest.raises(requests.exceptions.HTTPError):
            api_client.request_prediction(jpeg_image_bytes, "mock_username", 1.0)

    @pytest.mark.parametrize("response_status_code", [200, 202])
    def test_get_prediction_by_task_id_success(
        self, api_client, requests_mock, response_status_code
    ):
        requests_mock.get(
            f"{api_client.predict_service_url}/retrieve-results/mock_task_id.json",
            json={"some": "stuff"},
            status_code=response_status_code,
        )
        response = api_client.get_prediction_by_task_id("mock_task_id")
        assert response.status_code == response_status_code
        assert response.json() == {"some": "stuff"}

    @pytest.mark.parametrize("response_status_code", [404, 424, 500])
    def test_get_prediction_by_task_id_failure(
        self, api_client, requests_mock, response_status_code
    ):
        requests_mock.get(
            f"{api_client.predict_service_url}/retrieve-results/mock_task_id.json",
            status_code=response_status_code,
        )

        response = api_client.get_prediction_by_task_id("mock_task_id")
        assert response.status_code == response_status_code
