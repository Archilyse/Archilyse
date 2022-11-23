from http import HTTPStatus

import pytest

from common_utils.constants import DMS_PERMISSION, USER_ROLE
from slam_api.apis.building import BuildingView, building_app
from slam_api.apis.floor import FloorView, floor_app
from slam_api.apis.site import SiteView, site_app
from slam_api.apis.unit import UnitView, unit_app
from tests.constants import USERS
from tests.flask_utils import get_address_for
from tests.integration.utils import (
    add_site_permissions,
    assert_site_consistency,
    change_site_ownership,
)
from tests.utils import login_with


@pytest.fixture
def entity_labels():
    return ["testing", "a", "label"]


@pytest.fixture
def id_by_entity_name(site, building, floor, unit, areas_db):
    return {
        "site": site["id"],
        "building": building["id"],
        "floor": floor["id"],
        "unit": unit["id"],
        "area": areas_db[0]["id"],
    }


@pytest.mark.parametrize(
    "view_app,view_function",
    [
        (site_app, SiteView),
        (building_app, BuildingView),
        (floor_app, FloorView),
        (unit_app, UnitView),
    ],
)
@pytest.mark.parametrize(
    "user_role",
    [USER_ROLE.ADMIN, USER_ROLE.DMS_LIMITED],
)
def test_add_label_to_entities_admin(
    client,
    view_app,
    view_function,
    entity_labels,
    id_by_entity_name,
    user_role,
    site_delivered_simulated,
):
    user = login_with(client, USERS[user_role.name])["user"]
    change_site_ownership(site_delivered_simulated["id"], user["client_id"])
    add_site_permissions(
        site_delivered_simulated["id"], user["id"], DMS_PERMISSION.READ.name
    )
    entity_id = {
        view_app.name.lower() + "_id": id_by_entity_name[view_app.name.lower()]
    }
    response = client.put(
        get_address_for(
            blueprint=view_app,
            use_external_address=False,
            view_function=view_function,
            **entity_id,
        ),
        json={"labels": entity_labels},
    )
    assert response.status_code == HTTPStatus.OK, response.json
    assert response.json["labels"] == entity_labels

    assert_site_consistency(
        site_id=site_delivered_simulated["id"], consistency_altered=False
    )


@pytest.mark.parametrize(
    "view_app,view_function,attribute_name",
    [
        (site_app, SiteView, "name"),
        (building_app, BuildingView, "zipcode"),
        (floor_app, FloorView, "gcs_en_floorplan_link"),
        (unit_app, UnitView, "unit_type"),
    ],
)
@pytest.mark.parametrize(
    "user_role,expected_http",
    [(USER_ROLE.ADMIN, HTTPStatus.OK), (USER_ROLE.DMS_LIMITED, HTTPStatus.FORBIDDEN)],
)
def test_put_entity_by_role(
    client,
    site_delivered_simulated,
    view_app,
    view_function,
    attribute_name,
    user_role,
    expected_http,
    id_by_entity_name,
):
    user = login_with(client, USERS[user_role.name])["user"]
    change_site_ownership(site_delivered_simulated["id"], user["client_id"])
    add_site_permissions(
        site_delivered_simulated["id"], user["id"], DMS_PERMISSION.READ.name
    )
    entity_id = {
        view_app.name.lower() + "_id": id_by_entity_name[view_app.name.lower()]
    }
    response = client.put(
        get_address_for(
            blueprint=view_app,
            use_external_address=False,
            view_function=view_function,
            **entity_id,
        ),
        json={attribute_name: "I like writing tests"},
    )
    assert response.status_code == expected_http, response.json

    assert_site_consistency(
        site_id=site_delivered_simulated["id"],
        consistency_altered=expected_http == HTTPStatus.OK,
    )
