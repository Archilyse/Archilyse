from http import HTTPStatus

import pytest

from common_utils.constants import ADMIN_SIM_STATUS
from handlers.db import SiteDBHandler
from slam_api.apis.building import BuildingCollectionView, BuildingView, building_app
from slam_api.apis.floor import FloorView, floor_app
from slam_api.utils import ensure_site_consistency
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.integration.utils import assert_site_consistency


@login_as(["TEAMMEMBER"])
def test_post_building_performs_site_consistency(
    client, site_delivered_simulated, login
):
    url = get_address_for(
        blueprint=building_app,
        view_function=BuildingCollectionView,
        use_external_address=False,
    )
    request_body = {
        "site_id": site_delivered_simulated["id"],
        "housenumber": "3",
        "city": "3",
        "zipcode": "3",
        "street": "3",
    }
    response = client.post(url, json=request_body)
    assert response.status_code == HTTPStatus.CREATED, response.data

    assert_site_consistency(
        site_id=site_delivered_simulated["id"], consistency_altered=True
    )


@login_as(["TEAMMEMBER"])
def test_put_building_performs_site_consistency(
    client, site_delivered_simulated, login, building
):
    url = get_address_for(
        blueprint=building_app,
        view_function=BuildingView,
        use_external_address=False,
        building_id=building["id"],
    )
    request_body = {
        "housenumber": "3",
        "city": "3",
        "zipcode": "3",
        "street": "3",
    }
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.OK, response.data

    assert_site_consistency(
        site_id=site_delivered_simulated["id"], consistency_altered=True
    )


@login_as(["TEAMMEMBER"])
def test_put_floor_performs_site_consistency(
    client, site_delivered_simulated, floor, login
):
    url = get_address_for(
        blueprint=floor_app,
        view_function=FloorView,
        floor_id=floor["id"],
        use_external_address=False,
    )
    request_body = {"floor_number": 2}
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.OK, response.data

    assert_site_consistency(
        site_id=site_delivered_simulated["id"], consistency_altered=True
    )


@login_as(["TEAMMEMBER"])
def test_put_floor_do_not_perform_site_consistency_if_error(
    client, site_delivered_simulated, floor, login
):
    url = get_address_for(
        blueprint=floor_app,
        view_function=FloorView,
        floor_id=floor["id"],
        use_external_address=False,
    )
    request_body = {"non_existing_field": 2}
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data

    assert_site_consistency(
        site_id=site_delivered_simulated["id"], consistency_altered=False
    )


@pytest.mark.parametrize("status_field", ("full_slam_results", "basic_features_status"))
def test_ensure_site_consistency_not_allowed_states(status_field, site):
    @ensure_site_consistency()
    def dummy_method(**kwargs):
        pass

    for state in (ADMIN_SIM_STATUS.PROCESSING, ADMIN_SIM_STATUS.PENDING):
        # given
        SiteDBHandler.update(
            item_pks=dict(id=site["id"]), new_values={status_field: state}
        )

        # when
        response, status_code = dummy_method(site_id=site["id"])

        # then
        assert response.get_json() == {
            "msg": "Can't make changes to the pipeline while simulation tasks are running."
        }
        assert status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.parametrize("status_field", ("full_slam_results", "basic_features_status"))
def test_ensure_site_consistency_allowed_states(status_field, site):
    @ensure_site_consistency()
    def dummy_method(**kwargs):
        return True

    for state in (
        ADMIN_SIM_STATUS.UNPROCESSED,
        ADMIN_SIM_STATUS.SUCCESS,
        ADMIN_SIM_STATUS.FAILURE,
    ):
        SiteDBHandler.update(
            item_pks=dict(id=site["id"]), new_values={status_field: state}
        )
        assert dummy_method(site_id=site["id"]) is True
