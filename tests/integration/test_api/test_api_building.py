from collections import Counter
from http import HTTPStatus

import msgpack
import pytest
from deepdiff import DeepDiff
from google.cloud import exceptions as gcloud_exceptions
from shapely import wkt
from shapely.geometry import Polygon

from common_utils.constants import DMS_PERMISSION, SIMULATION_VERSION, USER_ROLE
from handlers import BuildingHandler, GCloudStorageHandler
from handlers.db import DmsPermissionDBHandler, UnitAreaDBHandler, UnitDBHandler
from slam_api.apis.building import (
    BuildingCollectionView,
    BuildingTrianglesView,
    BuildingView,
    building_app,
)
from tests.constants import USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.integration.utils import response_message
from tests.utils import login_with


@pytest.fixture
def building_default_values(site):
    return {
        "site_id": site["id"],
        "housenumber": "3",
        "city": "3",
        "zipcode": "3",
        "street": "3",
    }


@pytest.mark.parametrize(
    "new_building_values",
    [{}, {"client_building_id": "1"}, {"client_building_id": ""}],
)
def test_post_building(new_building_values, building_default_values, client, login):
    building_data = building_default_values
    building_data.update(**new_building_values)

    post_response = client.post(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingCollectionView,
        ),
        json=building_data,
    )

    assert post_response.status_code == HTTPStatus.CREATED

    for k, v in building_data.items():
        assert k in post_response.json
        assert v == post_response.json[k]


@pytest.mark.parametrize(
    "unique_key",
    [("site_id", "client_building_id"), ("site_id", "street", "housenumber")],
)
def test_post_building_returns_400_in_case_of_unique_key_violation(
    unique_key, building_default_values, client, building, login
):
    building_data = building_default_values
    for field in unique_key:
        building_data[field] = building[field]

    post_response = client.post(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingCollectionView,
        ),
        json=building_data,
    )

    assert post_response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "psycopg2.errors.UniqueViolation" in post_response.json["msg"]


@pytest.mark.parametrize(
    "new_building_values",
    [
        {"client_building_id": "-777"},
        {"client_building_id": ""},
        {"housenumber": "-777"},
    ],
)
@pytest.mark.parametrize(
    "user_role", [USER_ROLE.TEAMMEMBER, USER_ROLE.ARCHILYSE_ONE_ADMIN]
)
def test_put_building(new_building_values, client, building, user_role):
    login_with(client, USERS[user_role.name])
    post_response = client.put(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingView,
            building_id=building["id"],
        ),
        json=new_building_values,
    )

    assert post_response.status_code == HTTPStatus.OK

    new_building = post_response.json
    expected_results = {
        **building,
        **new_building_values,
        "updated": new_building["updated"],
    }

    assert new_building == expected_results


@pytest.mark.parametrize(
    "unique_key",
    [("site_id", "client_building_id"), ("site_id", "street", "housenumber")],
)
def test_put_building_returns_400_in_case_of_unique_key_violation(
    unique_key, client, building, other_clients_building, login
):
    building_data = {}
    for field in unique_key:
        building_data[field] = building[field]

    post_response = client.put(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingView,
            building_id=other_clients_building["id"],
        ),
        json=building_data,
    )

    assert post_response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "psycopg2.errors.UniqueViolation" in post_response.get_json()["msg"]


@pytest.mark.parametrize(
    "has_permission, expected_response_status",
    [(True, HTTPStatus.OK), (False, HTTPStatus.FORBIDDEN)],
)
@login_as([USER_ROLE.DMS_LIMITED.name])
def test_get_buildings_dms_limited(
    client,
    client_db,
    site,
    site_coordinates,
    login,
    make_sites,
    make_buildings,
    has_permission,
    expected_response_status,
):
    from handlers.db import ClientDBHandler

    other_client = ClientDBHandler.add(name="OtherClient")
    site_other_client, other_site = make_sites(
        *(other_client, client_db), group_id=login["group"]["id"]
    )

    building1, building2, building_3, building_other_client = make_buildings(
        *(site, site, other_site, site_other_client)
    )
    if has_permission:
        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.READ.name,
        )

    response = client.get(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingCollectionView,
            site_id=site["id"],
        )
    )

    assert response.status_code == expected_response_status, response_message(
        response=response
    )

    if expected_response_status == HTTPStatus.OK:
        assert len(response.json) == 2
        assert {element["id"] for element in response.json} == {
            building1["id"],
            building2["id"],
        }
    elif expected_response_status == HTTPStatus.FORBIDDEN:
        assert response.json["msg"] == "User is not allowed to access this site"


def test_get_building_triangles(
    mocker,
    site,
    building,
    plan,
    client,
    login,
    make_classified_split_plans,
    mocked_gcp_upload_bytes_to_bucket,
    visualize=False,
):
    areas = make_classified_split_plans(
        plan, annotations_plan_id=6380, building=building
    )
    units = UnitDBHandler.find()
    # to generate consistent results, we assign the client id to each unit based on the
    # total area sizes
    area_size_by_id = {
        area["id"]: wkt.loads(area["scaled_polygon"]).area for area in areas
    }
    unit_areas = UnitAreaDBHandler.find()
    area_size_by_unit_id = Counter()
    for unit_area in unit_areas:
        area_size_by_unit_id[unit_area["unit_id"]] += area_size_by_id[
            unit_area["area_id"]
        ]
    UnitDBHandler.bulk_update(
        client_id={
            unit["id"]: f"{i}"
            for i, unit in enumerate(
                sorted(units, key=lambda x: area_size_by_unit_id[x["id"]])
            )
        }
    )

    BuildingHandler(building_id=building["id"]).generate_and_upload_triangles_to_gcs(
        simulation_version=SIMULATION_VERSION.PH_01_2021
    )
    mocker.patch.object(
        BuildingHandler,
        "_get_triangles_from_gcs",
        return_value=mocked_gcp_upload_bytes_to_bucket.call_args_list[0].kwargs[
            "contents"
        ],
    )

    response = client.get(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingTrianglesView,
            building_id=building["id"],
        )
    )
    meshes = msgpack.unpackb(response.data)
    expected_units = {unit["client_id"] for unit in UnitDBHandler.find()}
    current_units = {client_id for client_id, _ in meshes}
    assert current_units == expected_units

    if visualize:
        from surroundings.visualization.sourroundings_3d_figure import (
            create_3d_surroundings_from_triangles_per_type,
        )

        create_3d_surroundings_from_triangles_per_type(
            filename="salpica",
            triangles_per_layout=meshes,
            triangles_per_surroundings_type=[],
        )
    # Although the shapes of the triangles can change for each generation, the number of triangles should remain similar
    # if the number of polygons generated is the same.
    num_triangles_generated_by_client = {
        client_id: len(triangles) for client_id, triangles in meshes
    }
    area_triangles_generated_by_client = {
        client_id: sum(Polygon(t).area for t in triangles)
        for client_id, triangles in meshes
    }
    expected_triangles_num_triangles_by_client = {
        "0": 1406,
        "1": 1572,
        "2": 1586,
        "3": 1820,
        "4": 2196,
    }

    expected_area_by_client = {
        "1": 6.227485344193616e-08,
        "4": 9.202622873156764e-08,
        "2": 6.260870900818532e-08,
        "3": 6.912508508699821e-08,
        "0": 5.6443427809896076e-08,
    }

    assert not DeepDiff(
        expected_triangles_num_triangles_by_client, num_triangles_generated_by_client
    )
    assert not DeepDiff(
        expected_area_by_client,
        area_triangles_generated_by_client,
        significant_digits=7,
        number_format_notation="e",
    )


def test_get_building_triangles_not_ready(mocker, building, client, login):
    mocker.patch.object(
        GCloudStorageHandler, "download_file", side_effect=gcloud_exceptions.NotFound
    )
    response = client.get(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingTrianglesView,
            building_id=building["id"],
        )
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_get_building_triangles_not_existing(client, login):
    response = client.get(
        get_address_for(
            blueprint=building_app,
            use_external_address=False,
            view_function=BuildingTrianglesView,
            building_id=31416,
        )
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
