from http import HTTPStatus
from math import isclose

from flask import jsonify
from flask.views import MethodView
from flask_smorest import Blueprint

from common_utils.competition_constants import DEFAULT_WEIGHTS
from common_utils.constants import USER_ROLE
from common_utils.exceptions import (
    CompetitionConfigurationMissingError,
    UserAuthorizationException,
)
from db_models.db_entities import CompetitionDBModel
from handlers.competition import CompetitionHandler
from handlers.competition.utils import CompetitionCategoryTreeGenerator
from handlers.db import CompetitionDBHandler, CompetitionManualInputDBHandler
from slam_api.apis.competition.schemas import (
    AdminCompetitionPostArgs,
    AdminCompetitionQueryArgs,
    CompetitionParameters,
    CompetitorsPutArgs,
    WeightsPutArgs,
)
from slam_api.apis.competition.utils import format_percents
from slam_api.entity_ownership_validation import validate_entity_ownership
from slam_api.utils import get_user_authorized, role_access_control

competition_app = Blueprint("competition", __name__)


@competition_app.errorhandler(CompetitionConfigurationMissingError)
def control_competition_not_configured(e):
    return (
        jsonify(msg="The competition is not completely configured!"),
        HTTPStatus.BAD_REQUEST,
    )


@competition_app.route("/competitions", methods=["GET"])
@competition_app.response(status_code=HTTPStatus.OK)
@role_access_control(roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER})
def get_competitions():
    user = get_user_authorized()
    if client_id := user["client_id"]:
        return jsonify(CompetitionDBHandler.find(client_id=client_id))
    elif USER_ROLE.ADMIN in user["roles"]:
        return jsonify(CompetitionDBHandler.find())
    else:
        raise UserAuthorizationException(
            "The current user is not associated with any client. "
            "Please login with an appropriate user."
        )


@competition_app.route("/<int:competition_id>/categories", methods=["GET"])
@competition_app.response(status_code=HTTPStatus.OK)
@role_access_control(roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER})
def get_competition_categories(competition_id: int):
    return jsonify(CompetitionHandler(competition_id=competition_id).category_tree)


@competition_app.route("/categories", methods=["GET"])
@competition_app.response(status_code=HTTPStatus.OK)
@role_access_control(roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER})
def get_categories():
    cat_tree = CompetitionCategoryTreeGenerator(
        red_flags_enabled=True, features_selected=None
    ).get_category_tree()
    return jsonify(cat_tree)


@competition_app.route("/<int:competition_id>/competitors", methods=["GET"])
@competition_app.response(status_code=HTTPStatus.OK)
@role_access_control(roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER})
@validate_entity_ownership(
    CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
)
def get_competitors_features(competition_id: int):
    return jsonify(
        CompetitionHandler(
            competition_id=competition_id
        ).get_competitors_features_values()
    )


@competition_app.route("/<int:competition_id>/competitors/units", methods=["GET"])
@competition_app.response(status_code=HTTPStatus.OK)
@role_access_control(roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER})
@validate_entity_ownership(
    CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
)
def get_competitors_units(competition_id: int):
    return jsonify(
        CompetitionHandler(competition_id=competition_id).get_competitors_units()
    )


@competition_app.route("/<int:competition_id>/scores", methods=["GET"])
@competition_app.response(status_code=HTTPStatus.OK)
@role_access_control(roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER})
@validate_entity_ownership(
    CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
)
def get_competitors_scores(competition_id: int):
    sorted_competitors = sorted(
        CompetitionHandler(competition_id=competition_id).compute_competitors_scores(),
        key=lambda k: k["total"],
        reverse=True,
    )
    return jsonify(sorted_competitors)


@competition_app.route("/<int:competition_id>/info")
class CompetitionInfo(MethodView):
    @competition_app.response(status_code=HTTPStatus.OK)
    @role_access_control(
        roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER}
    )
    @validate_entity_ownership(
        CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
    )
    def get(self, competition_id: int):
        info = CompetitionDBHandler.get_by(
            id=competition_id,
            output_columns=["weights", "name", "currency", "prices_are_rent"],
        )
        return jsonify(info)


@competition_app.route("/<int:competition_id>/weights")
class CompetitionWeightsView(MethodView):
    @competition_app.arguments(WeightsPutArgs, location="json", as_kwargs=True)
    @competition_app.response(status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.COMPETITION_ADMIN})
    def put(self, competition_id: int, **kwargs):
        weights_sum = sum(kwargs.values())
        if not isclose(weights_sum, 1.0):
            formatted_percents = format_percents(weights_sum * 100)
            return (
                jsonify(
                    {
                        "msg": f"The sum of weights should be 100% but got {formatted_percents}%"
                    }
                ),
                HTTPStatus.BAD_REQUEST,
            )

        updated = CompetitionDBHandler.update(
            item_pks={"id": competition_id}, new_values={"weights": kwargs}
        )

        return jsonify(updated["weights"])


@competition_app.route("/<int:competition_id>/configuration_parameters")
class CompetitionParametersView(MethodView):
    @competition_app.response(schema=CompetitionParameters, status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.COMPETITION_ADMIN})
    @validate_entity_ownership(
        CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
    )
    def get(self, competition_id: int):
        competition = CompetitionDBHandler.get_by(
            id=competition_id, output_columns=["configuration_parameters"]
        )
        return jsonify(competition["configuration_parameters"] or {})

    @competition_app.arguments(
        CompetitionParameters(partial=True), location="json", as_kwargs=True
    )
    @competition_app.response(schema=CompetitionParameters, status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.COMPETITION_ADMIN})
    @validate_entity_ownership(
        CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
    )
    def put(self, competition_id: int, **kwargs):
        competition = CompetitionDBHandler.get_by(
            id=competition_id, output_columns=["configuration_parameters"]
        )

        updated = CompetitionDBHandler.update(
            item_pks={"id": competition_id},
            new_values={
                "configuration_parameters": {
                    **(competition["configuration_parameters"] or {}),
                    **kwargs,
                }
            },
        )

        return jsonify(updated["configuration_parameters"])


@competition_app.route(
    "/<int:competition_id>/competitors/<int:competitor_id>/manual_input"
)
class CompetitionClientInputView(MethodView):
    @competition_app.response(status_code=HTTPStatus.OK)
    @role_access_control(
        roles={USER_ROLE.COMPETITION_ADMIN, USER_ROLE.COMPETITION_VIEWER}
    )
    @validate_entity_ownership(
        CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
    )
    def get(self, competition_id: int, competitor_id: int):
        return CompetitionManualInputDBHandler.get_by(
            competition_id=competition_id, competitor_id=competitor_id
        )

    @competition_app.arguments(CompetitorsPutArgs, location="json", as_kwargs=True)
    @competition_app.response(status_code=HTTPStatus.OK)
    @role_access_control(roles={USER_ROLE.COMPETITION_ADMIN})
    @validate_entity_ownership(
        CompetitionDBModel, lambda kwargs: {"id": kwargs["competition_id"]}
    )
    def put(self, competition_id: int, competitor_id: int, **kwargs):
        return CompetitionManualInputDBHandler.upsert(
            competition_id=competition_id,
            competitor_id=competitor_id,
            new_values={"features": kwargs},
        )


@competition_app.route("/")
class AdminCompetitionViewCollection(MethodView):
    @role_access_control(roles={USER_ROLE.ADMIN})
    @competition_app.arguments(
        AdminCompetitionQueryArgs, required=True, location="query", as_kwargs=True
    )
    @competition_app.response(status_code=HTTPStatus.OK)
    def get(self, client_id: int):
        return jsonify(CompetitionDBHandler.find(client_id=client_id))

    @role_access_control(roles={USER_ROLE.ADMIN})
    @competition_app.arguments(AdminCompetitionPostArgs, as_kwargs=True)
    @competition_app.response(status_code=HTTPStatus.CREATED)
    def post(self, **kwargs):
        return (
            jsonify(
                CompetitionDBHandler.add(
                    **kwargs,
                    weights=DEFAULT_WEIGHTS,
                )
            ),
            HTTPStatus.CREATED,
        )


@competition_app.route("/<int:competition_id>")
class AdminCompetitionView(MethodView):
    @role_access_control(roles={USER_ROLE.ADMIN})
    @competition_app.response(status_code=HTTPStatus.OK)
    def get(self, competition_id: int):
        return jsonify(CompetitionDBHandler.get_by(id=competition_id))

    @role_access_control(roles={USER_ROLE.ADMIN})
    @competition_app.arguments(AdminCompetitionPostArgs(partial=True), as_kwargs=True)
    @competition_app.response(status_code=HTTPStatus.OK)
    def put(self, competition_id: int, **new_values):
        return jsonify(
            CompetitionDBHandler.update(
                item_pks=dict(id=competition_id), new_values=new_values
            )
        )

    @role_access_control(roles={USER_ROLE.ADMIN})
    @competition_app.response(status_code=HTTPStatus.NO_CONTENT)
    def delete(self, competition_id: int):
        CompetitionDBHandler.delete(item_pk=dict(id=competition_id))
