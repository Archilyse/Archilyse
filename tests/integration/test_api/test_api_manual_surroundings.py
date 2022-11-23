from http import HTTPStatus

import pytest
from deepdiff import DeepDiff

from common_utils.constants import ADMIN_SIM_STATUS, ManualSurroundingTypes
from handlers.db import ManualSurroundingsDBHandler, SiteDBHandler
from slam_api.apis.manual_surroundings import (
    ManualSurroundingsView,
    manual_surroundings_app,
)
from tests.flask_utils import get_address_for


class TestManualSurroundingsView:
    def test_put(self, site, client, manually_created_surroundings):
        SiteDBHandler.update(
            item_pks={"id": site["id"]},
            new_values={
                "full_slam_results": ADMIN_SIM_STATUS.SUCCESS,
            },
        )
        url = get_address_for(
            blueprint=manual_surroundings_app,
            view_function=ManualSurroundingsView,
            site_id=site["id"],
        )
        response = client.put(url, json=manually_created_surroundings)
        assert response.status_code == HTTPStatus.CREATED, response.data

        actual_manual_surroundings = ManualSurroundingsDBHandler.get_by(
            site_id=site["id"]
        )
        assert response.json == actual_manual_surroundings

        expected_manual_surroundings = {
            "site_id": site["id"],
            "surroundings": manually_created_surroundings,
        }
        assert not DeepDiff(
            expected_manual_surroundings,
            actual_manual_surroundings,
            exclude_paths=["root['updated']", "root['created']"],
        )
        assert (
            SiteDBHandler.get_by(id=site["id"], output_columns=["full_slam_results"])[
                "full_slam_results"
            ]
            == ADMIN_SIM_STATUS.UNPROCESSED.name
        )

    def test_put_site_running(self, site, client, manually_created_surroundings):
        SiteDBHandler.update(
            item_pks={"id": site["id"]},
            new_values={
                "full_slam_results": ADMIN_SIM_STATUS.PROCESSING,
            },
        )
        url = get_address_for(
            blueprint=manual_surroundings_app,
            view_function=ManualSurroundingsView,
            site_id=site["id"],
        )
        response = client.put(url, json=manually_created_surroundings)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.get_json() == {
            "msg": "Can't make changes to the pipeline while simulation tasks are running."
        }

    @pytest.mark.parametrize(
        "feature_properties",
        [
            {
                "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
            },
            {
                "surrounding_type": ManualSurroundingTypes.BUILDINGS.name,
                "height": -10.0,
            },
            {
                "surrounding_type": "UNKNOWN_SURROUNDING_TYPE",
            },
        ],
    )
    def test_put_returns_422_on_invalid_feature_properties(
        self, site, feature_properties, manually_created_surroundings, client
    ):
        feature = manually_created_surroundings["features"][0]
        feature["properties"] = feature_properties

        url = get_address_for(
            blueprint=manual_surroundings_app,
            view_function=ManualSurroundingsView,
            site_id=site["id"],
        )
        response = client.put(url, json=manually_created_surroundings)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data

    def test_get(self, site, manually_created_surroundings, client):
        manual_surroundings = ManualSurroundingsDBHandler.add(
            site_id=site["id"], surroundings=manually_created_surroundings
        )
        response = client.get(
            get_address_for(
                blueprint=manual_surroundings_app,
                use_external_address=False,
                view_function=ManualSurroundingsView,
                site_id=site["id"],
            )
        )
        assert response.status_code == HTTPStatus.OK, response.data
        assert response.json == manual_surroundings
