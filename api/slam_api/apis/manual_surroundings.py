from http import HTTPStatus
from typing import Dict

from flask.views import MethodView
from flask_smorest import Blueprint

from common_utils.constants import USER_ROLE
from handlers.db import ManualSurroundingsDBHandler
from handlers.db.manual_surroundings_handler import GeoJsonFeatureCollectionSchema
from slam_api.utils import ensure_site_consistency, role_access_control

manual_surroundings_app = Blueprint("manual_surroundings", __name__)


@manual_surroundings_app.route("/<int:site_id>")
class ManualSurroundingsView(MethodView):
    @role_access_control(roles={USER_ROLE.ADMIN})
    @ensure_site_consistency()
    @manual_surroundings_app.arguments(
        GeoJsonFeatureCollectionSchema, location="json", as_kwargs=False
    )
    @manual_surroundings_app.response(status_code=HTTPStatus.CREATED)
    def put(self, manual_surroundings: Dict, site_id: int) -> Dict:
        return ManualSurroundingsDBHandler.upsert(
            site_id=site_id, new_values={"surroundings": manual_surroundings}
        )

    @role_access_control(roles={USER_ROLE.ADMIN})
    @manual_surroundings_app.response(status_code=HTTPStatus.OK)
    def get(self, site_id: int) -> Dict:
        return ManualSurroundingsDBHandler.get_by(site_id=site_id)
