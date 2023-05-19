import math
from http import HTTPStatus

from flask.views import MethodView
from flask_smorest import Blueprint
from requests import HTTPError
from shapely.geometry import polygon
from shapely.ops import unary_union

from common_utils.constants import USER_ROLE
from dufresne.polygon.utils import as_multipolygon
from handlers import PlanHandler, PlanLayoutHandler, ReactPlannerHandler
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.external_api_clients.layout_predictor_client import LayoutPredictorClient
from slam_api.utils import get_user_authorized, role_access_control

layout_predictor_app = Blueprint("layout_predictor", __name__)


@layout_predictor_app.route("/request-predictions/<int:plan_id>")
class LayoutPredictorView(MethodView):
    @layout_predictor_app.response(status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self, plan_id: int):
        """Get layout prediction for plan"""
        username = get_user_authorized()["login"]

        plan_data = PredictorClientPlanDataExtractor(plan_id=plan_id).get_plan_data()
        try:
            result = LayoutPredictorClient().request_prediction(
                username=username,
                image_bytes=plan_data["image_bytes"],
                pixels_per_meter=plan_data["pixels_per_meter"],
                rois=plan_data["rois"],
            )
        except HTTPError as e:
            return (
                f"There is some issue with deep-learning api {e}",
                HTTPStatus.NOT_FOUND,
            )

        return result


@layout_predictor_app.route("/retrieve-results/<string:task_id>")
class LayoutPredictorResultView(MethodView):
    @layout_predictor_app.response(status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self, task_id: str):
        """Get layout prediction for plan"""
        response = LayoutPredictorClient().get_prediction_by_task_id(task_id=task_id)
        return (
            response.json() if response.status_code == HTTPStatus.OK else "",
            response.status_code,
        )


class PredictorClientPlanDataExtractor:
    def __init__(self, plan_id: int):
        self.plan_id = plan_id
        self.plan_handler = PlanHandler(plan_id=plan_id)
        self.plan_layout_handler = PlanLayoutHandler(plan_id=plan_id)

    def get_plan_data(self) -> dict:
        plan_image = self.plan_handler.get_plan_image_as_bytes()
        pixels_per_meter = self._get_pixels_per_meter()
        rois = self._get_rois(self.plan_handler.plan_info)
        return {
            "image_bytes": plan_image,
            "pixels_per_meter": pixels_per_meter,
            "rois": rois,
        }

    def _get_pixels_per_meter(self) -> float:
        georef_scale = PlanDBHandler.get_by(id=self.plan_id)["georef_scale"]
        react_scale = ReactPlannerProjectsDBHandler.get_by(plan_id=self.plan_id)[
            "data"
        ]["scale"]
        return (1 / math.sqrt(georef_scale)) / react_scale

    def _get_rois(self, plan_info: dict) -> list[tuple[int, int, int, int]]:
        from brooks.types import SeparatorType

        max_x, max_y = plan_info["image_width"], plan_info["image_height"]
        separators_by_type: dict[
            SeparatorType, list[polygon]
        ] = ReactPlannerToBrooksMapper().get_original_separator_geometries(
            planner_elements=ReactPlannerHandler().get_data(plan_id=self.plan_id)
        )
        all_separators = [pol for pols in separators_by_type.values() for pol in pols]
        rois = []
        for pol in as_multipolygon(unary_union(all_separators)).geoms:
            bounds = pol.bounds

            # ensure that the bounds are within the image
            rois.append(
                (
                    max(round(bounds[0]), 0),
                    max(round(bounds[1]), 0),
                    min(round(bounds[2]), max_x),
                    min(round(bounds[3]), max_y),
                )
            )
        return rois
