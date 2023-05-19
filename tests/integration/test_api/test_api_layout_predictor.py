from http import HTTPStatus

import pytest
from shapely.geometry import Polygon, box

from common_utils.constants import USER_ROLE
from common_utils.exceptions import DBNotFoundException
from handlers.db import PlanDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.external_api_clients.layout_predictor_client import LayoutPredictorClient
from slam_api.apis.layout_predictor.endpoints import (
    LayoutPredictorResultView,
    LayoutPredictorView,
    PredictorClientPlanDataExtractor,
    layout_predictor_app,
)
from tests.constants import USERS
from tests.flask_utils import get_address_for
from tests.utils import login_with


class TestLayoutPredictorView:
    @pytest.fixture
    def jpeg_image_bytes(self, images_path):
        with images_path.joinpath("floorplan_b.jpg").open("rb") as f:
            image_bytes = f.read()
        return image_bytes

    @pytest.fixture
    def mocked_gcp_download_file_as_bytes(self, mocker, jpeg_image_bytes):
        from handlers.gcloud_storage import GCloudStorageHandler

        return mocker.patch.object(
            GCloudStorageHandler,
            GCloudStorageHandler.download_file_as_bytes.__name__,
            return_value=jpeg_image_bytes,
        )

    @pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN])
    def test_get_success(
        self,
        plan_annotated,
        client,
        mocked_gcp_download_file_as_bytes,
        requests_mock,
        user_role,
    ):
        login_with(client, USERS[user_role.name])
        mock_upload_url = "https://mock-url.com"
        requests_mock.get(
            f"{LayoutPredictorClient().predict_service_url}/images/upload-url",
            json={"url": mock_upload_url, "image_name": "mock_image"},
        )
        requests_mock.put(mock_upload_url, status_code=200)
        requests_mock.post(
            f"{LayoutPredictorClient().predict_service_url}/request-prediction/icons",
            json={"icon_task": {"id": "some_task_id"}},
        )

        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorView,
            plan_id=plan_annotated["id"],
        )

        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.json == {"icon_task": {"id": "some_task_id"}}
        assert (
            requests_mock.request_history[0].headers["username"]
            == USERS[user_role.name]["login"]
        )

    @pytest.mark.parametrize("user_role", [USER_ROLE.DMS_LIMITED, USER_ROLE.TEAMMEMBER])
    def test_get_user_permission_denied(
        self, plan_annotated, client, requests_mock, user_role
    ):
        login_with(client, USERS[user_role.name])

        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorView,
            plan_id=plan_annotated["id"],
        )

        response = client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_get_plan_does_not_exists(self, client, requests_mock):
        login_with(client, USERS[USER_ROLE.ADMIN.name])

        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorView,
            plan_id=24,
        )

        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_get_external_api_down(
        self, plan_annotated, client, mocked_gcp_download_file_as_bytes, requests_mock
    ):
        login_with(client, USERS[USER_ROLE.ADMIN.name])
        requests_mock.get(
            f"{LayoutPredictorClient().predict_service_url}/images/upload-url",
            status_code=500,
        )

        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorView,
            plan_id=plan_annotated["id"],
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert response.text.startswith('"There is some issue with deep-learning api')


class TestLayoutPredictorResultView:
    @pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN])
    def test_get_success(self, client, requests_mock, user_role):
        login_with(client, USERS[user_role.name])
        requests_mock.get(
            f"{LayoutPredictorClient().predict_service_url}/retrieve-results/mock_task_id.json",
            json={"status": "success"},
        )
        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorResultView,
            task_id="mock_task_id",
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.OK
        assert response.json == {"status": "success"}

    @pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN])
    def test_get_result_not_ready(self, client, requests_mock, user_role):
        login_with(client, USERS[user_role.name])
        requests_mock.get(
            f"{LayoutPredictorClient().predict_service_url}/retrieve-results/mock_task_id.json",
            status_code=HTTPStatus.ACCEPTED,
            raw="",
        )
        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorResultView,
            task_id="mock_task_id",
        )

        response = client.get(url)
        assert response.status_code == HTTPStatus.ACCEPTED

    @pytest.mark.parametrize("user_role", [USER_ROLE.ADMIN])
    def test_get_server_error(self, client, requests_mock, user_role):
        login_with(client, USERS[user_role.name])
        requests_mock.get(
            f"{LayoutPredictorClient().predict_service_url}/retrieve-results/mock_task_id.json",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        )
        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorResultView,
            task_id="mock_task_id",
        )

        response = client.get(url)
        assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    @pytest.mark.parametrize("user_role", [USER_ROLE.DMS_LIMITED, USER_ROLE.TEAMMEMBER])
    def test_get_user_permission_denied(self, client, requests_mock, user_role):
        login_with(client, USERS[user_role.name])
        url = get_address_for(
            blueprint=layout_predictor_app,
            view_function=LayoutPredictorResultView,
            task_id="mock_task_id",
        )
        response = client.get(url)
        assert response.status_code == HTTPStatus.FORBIDDEN


class TestPredictorClientPlanDataExtractor:
    def test_get_plan_data(self, plan_annotated, mocked_gcp_download_file_as_bytes):
        # makes sure ids are different for plan and annotations
        PlanDBHandler.update(
            item_pks={"id": plan_annotated["id"]}, new_values={"id": 5}
        )
        extractor = PredictorClientPlanDataExtractor(plan_id=5)

        plan_data = extractor.get_plan_data()

        assert isinstance(plan_data["image_bytes"], bytes)
        assert pytest.approx(plan_data["pixels_per_meter"]) == 100.0035671
        assert plan_data["rois"] == [(621, 419, 1721, 1241)]

    def test_get_rois(self, plan_annotated):
        extractor = PredictorClientPlanDataExtractor(plan_annotated["id"])
        rois = extractor._get_rois(plan_annotated)

        assert all(
            roi_y <= plan_annotated["image_height"]
            for roi in rois
            for roi_y in (roi[1], roi[3])
        )
        assert all(
            roi_x <= plan_annotated["image_width"]
            for roi in rois
            for roi_x in (roi[0], roi[2])
        )

    def test_get_rois_bounds_too_big_should_be_clipped(self, plan_annotated, mocker):
        mocker.patch.object(
            ReactPlannerToBrooksMapper,
            ReactPlannerToBrooksMapper.get_original_separator_geometries.__name__,
            return_value={
                "something": [
                    Polygon(
                        [
                            (-1, -1),
                            (plan_annotated["image_width"] + 1, -1),
                            (
                                plan_annotated["image_width"] + 1,
                                plan_annotated["image_height"] + 1,
                            ),
                            (-1, plan_annotated["image_height"] + 1),
                        ]
                    )
                ]
            },
        )
        extractor = PredictorClientPlanDataExtractor(plan_annotated["id"])
        rois = extractor._get_rois(plan_annotated)

        assert all(
            roi_y <= plan_annotated["image_height"]
            for roi in rois
            for roi_y in (roi[1], roi[3])
        )
        assert all(
            roi_x <= plan_annotated["image_width"]
            for roi in rois
            for roi_x in (roi[0], roi[2])
        )

    def test_get_rois_several_rois(self, plan_annotated, mocker):
        mocker.patch.object(
            ReactPlannerToBrooksMapper,
            ReactPlannerToBrooksMapper.get_original_separator_geometries.__name__,
            return_value={
                "something": [
                    Polygon([(-1, -1), (10, 10), (10, 20), (-1, 20)]),
                    Polygon([(100, 100), (110, 110), (110, 120), (100, 120)]),
                ],
                "something2": [
                    Polygon([(1000, 1000), (1010, 1010), (1010, 1020), (1000, 1020)]),
                    box(
                        plan_annotated["image_width"] - 100,
                        plan_annotated["image_height"] - 100,
                        plan_annotated["image_width"] + 10,
                        plan_annotated["image_height"] + 10,
                    ),
                ],
            },
        )
        extractor = PredictorClientPlanDataExtractor(plan_annotated["id"])
        rois = extractor._get_rois(plan_annotated)

        assert len(rois) == 4
        assert all(
            roi_y <= plan_annotated["image_height"]
            for roi in rois
            for roi_y in (roi[1], roi[3])
        )
        assert all(
            roi_x <= plan_annotated["image_width"]
            for roi in rois
            for roi_x in (roi[0], roi[2])
        )

    def test_get_rois_no_annotations(self, plan):
        extractor = PredictorClientPlanDataExtractor(plan["id"])
        with pytest.raises(DBNotFoundException):
            extractor._get_rois(plan)
