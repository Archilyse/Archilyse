from http import HTTPStatus

import msgpack
import pytest

from common_utils.constants import DMS_PERMISSION, SIMULATION_VERSION, USER_ROLE
from handlers import BuildingHandler
from handlers.db.dms_permission_handler import DmsPermissionDBHandler
from slam_api.apis.building import BuildingTrianglesView, building_app
from tests.constants import USERS
from tests.flask_utils import get_address_for
from tests.utils import login_with


@pytest.mark.parametrize(
    "user_role, permission",
    [
        (USER_ROLE.ARCHILYSE_ONE_ADMIN, None),
        (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
        (USER_ROLE.ADMIN, None),
    ],
)
def test_get_building_triangles_lightweight(
    first_pipeline_complete_db_models,
    client,
    login,
    recreate_test_gcp_client_bucket,
    user_role,
    permission,
):

    login = login_with(client, USERS[user_role.name])
    if permission:
        DmsPermissionDBHandler.add(
            site_id=first_pipeline_complete_db_models["site"]["id"],
            user_id=login["user"]["id"],
            rights=permission.name,
        )

    BuildingHandler(
        building_id=first_pipeline_complete_db_models["building"]["id"]
    ).generate_and_upload_triangles_to_gcs(SIMULATION_VERSION.PH_01_2021)
    response = client.get(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingTrianglesView,
            building_id=first_pipeline_complete_db_models["building"]["id"],
        )
    )
    assert response.status_code == HTTPStatus.OK, response.json
    meshes = msgpack.unpackb(response.data)

    expected_units = {
        unit["client_id"] for unit in first_pipeline_complete_db_models["units"]
    }
    current_units = {client_id for client_id, _ in meshes}
    assert current_units == expected_units

    expected_dimensions = {
        (216, 3, 3),
        (84, 3, 3),
        (566, 3, 3),
        (168, 3, 3),
    }

    assert len(meshes) == len(expected_dimensions)
