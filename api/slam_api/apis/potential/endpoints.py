from http import HTTPStatus
from typing import Tuple

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint

from common_utils.constants import SIMULATION_TYPE, USER_ROLE
from common_utils.exceptions import MissingTargetPotentialException
from handlers.db import PotentialSimulationDBHandler
from slam_api.apis.potential.openapi.documentation import (
    bearer_security_scheme,
    potential_simulation_request_args,
    simulation_response,
)
from slam_api.utils import role_access_control

potential_api = Blueprint("potential_api", __name__)


@potential_api.errorhandler(MissingTargetPotentialException)
def control_missing_building(e):
    return (
        jsonify(msg="There are no buildings near the given location"),
        HTTPStatus.BAD_REQUEST,
    )


@potential_api.route("/", methods=["GET"])
class GetPotentialSimulation(MethodView):
    @role_access_control(roles={USER_ROLE.POTENTIAL_API})
    @potential_api.arguments(**potential_simulation_request_args)
    @potential_api.response(status_code=HTTPStatus.OK, **simulation_response)
    @potential_api.doc(**bearer_security_scheme)
    def get(
        self, lat: float, lon: float, floor_number: int, sim_type: str
    ) -> Tuple[dict, int]:
        """Get the potential simulation results"""
        simulation = PotentialSimulationDBHandler.get_by_location(
            lat=lat,
            lon=lon,
            floor_number=floor_number,
            sim_type=SIMULATION_TYPE(sim_type),
        )
        simulation["sim_type"] = simulation["type"]
        simulation["lat"] = lat
        simulation["lon"] = lon

        return simulation, HTTPStatus.OK
