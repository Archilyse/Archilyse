from http import HTTPStatus
from typing import Dict, List, Tuple

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint

from common_utils.constants import USER_ROLE
from handlers.db import PotentialSimulationDBHandler
from slam_api.utils import role_access_control

from .schemas import BoundingBoxSchema

# Valid client facing exceptions
CLIENT_VALID_EXCEPTIONS = {"InvalidRegion"}


potential_private_api = Blueprint("potential_private_api", __name__)


@potential_private_api.route("/simulations", methods=["GET"])
class GetSimulations(MethodView):
    @potential_private_api.arguments(BoundingBoxSchema, location="querystring")
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self, bounding_box: Dict[str, float]) -> Tuple[List[dict], HTTPStatus]:
        """
        Returns the list of the 100 most recently requested simulations by the user, optionally filtered by bounding box
        """
        simulations = PotentialSimulationDBHandler.get_simulations_list(
            bounding_box=bounding_box
        )

        return jsonify(simulations), HTTPStatus.OK


@potential_private_api.route("/simulations/<int:simulation_id>/result", methods=["GET"])
class GetSimulationResultsById(MethodView):
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self, simulation_id: int) -> Tuple[dict, int]:
        """Returns the result of requested simulation"""
        simulation = PotentialSimulationDBHandler.get_by(
            id=simulation_id, output_columns=["id", "result"]
        )

        processed_observation_points = [
            [point["lat"], point["lon"], point["height"]]
            for point in simulation["result"]["observation_points"]
        ]
        simulation["result"]["observation_points"] = processed_observation_points

        return jsonify(simulation["result"]), HTTPStatus.OK


@potential_private_api.route("/simulations/<int:simulation_id>", methods=["GET"])
class GetSimulationById(MethodView):
    @role_access_control(roles={USER_ROLE.ADMIN})
    def get(self, simulation_id: int) -> Tuple[dict, int]:
        """Returns the requested simulation by id"""
        simulation = PotentialSimulationDBHandler.get_by(
            id=simulation_id,
            output_columns=[
                "id",
                "created",
                "floor_number",
                "type",
                "result",
                "status",
                "source_surr",
            ],
        )
        processed_observation_points = [
            [point["lat"], point["lon"], point["height"]]
            for point in simulation["result"]["observation_points"]
        ]
        simulation["result"]["observation_points"] = processed_observation_points

        return simulation, HTTPStatus.OK
