import os

from flask_smorest import Api
from marshmallow import fields

from handlers.db.base_handler import Float, Int, Str
from slam_api.apis.annotation_react_planner import annotations_v2_app
from slam_api.apis.apartment import apartments_app
from slam_api.apis.areas import areas_app
from slam_api.apis.building import building_app
from slam_api.apis.client import client_app
from slam_api.apis.competition.endpoints import competition_app
from slam_api.apis.constants import constants_app
from slam_api.apis.features import features_app
from slam_api.apis.file import file_app
from slam_api.apis.floor import floor_app
from slam_api.apis.folder import folder_app
from slam_api.apis.group import group_app
from slam_api.apis.login import login_app
from slam_api.apis.manual_surroundings import manual_surroundings_app
from slam_api.apis.plan import plan_app
from slam_api.apis.potential.endpoints import potential_api
from slam_api.apis.potential.private_endpoints import potential_private_api
from slam_api.apis.qa import qa_app
from slam_api.apis.site import site_app
from slam_api.apis.unit import unit_app
from slam_api.apis.user import user_app

from .flask_app import reFlask as Flask

PUBLIC_BLUEPRINTS = ((potential_api, "/potential"), (login_app, "/auth"))

PRIVATE_BLUEPRINTS = (
    (annotations_v2_app, "/annotation/v2"),
    (client_app, "/client"),
    (group_app, "/group"),
    (building_app, "/building"),
    (floor_app, "/floor"),
    (plan_app, "/plan"),
    (areas_app, ""),
    (apartments_app, ""),
    (site_app, "/site"),
    (unit_app, "/unit"),
    (qa_app, "/qa"),
    (features_app, "/features"),
    (constants_app, "/constants"),
    (user_app, "/user"),
    (file_app, "/file"),
    (folder_app, "/folder"),
    (competition_app, "/competition"),
    (potential_private_api, "/potential"),
    (manual_surroundings_app, "/manualsurroundings"),
)


def setup_apis(application: Flask):
    """Register APIs"""
    api = Api(
        application,
        spec_kwargs={
            "servers": [
                {
                    "url": os.environ.get("SLAM_API_URL", "https://api.archilyse.com"),
                    "description": "API Server",
                },
            ],
            "title": "slam API",
            "version": 1.0,
        },
    )

    api.register_field(Float, fields.Float)
    api.register_field(Str, fields.Str)
    api.register_field(Int, fields.Int)

    # TODO: not needed, we are using cookies
    api.spec.components.security_scheme(
        "bearer", dict(type="http", scheme="bearer", bearerFormat="JWT")
    )

    for blp, url_prefix in PUBLIC_BLUEPRINTS:
        api.register_blueprint(blp, url_prefix=f"/api{url_prefix}")
        api.register_blueprint(blp, url_prefix=url_prefix, name=f"no_api_{blp.name}")

    api_app = api if os.environ.get("TEST_ENVIRONMENT") else application
    for blp, url_prefix in PRIVATE_BLUEPRINTS:
        api_app.register_blueprint(
            blp, url_prefix=url_prefix, name=f"no_api_{blp.name}"
        )
        api_app.register_blueprint(blp, url_prefix=f"/api{url_prefix}")
