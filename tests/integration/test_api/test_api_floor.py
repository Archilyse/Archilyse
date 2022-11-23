from collections import Counter
from http import HTTPStatus
from io import BytesIO

import pytest
from werkzeug.datastructures import FileStorage

from common_utils.constants import (
    DMS_PERMISSION,
    DXF_MIME_TYPE,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    USER_ROLE,
)
from common_utils.exceptions import DXFImportException
from handlers import GCloudStorageHandler, PlanHandler, PlanLayoutHandler
from handlers.db import (
    ClientDBHandler,
    DmsPermissionDBHandler,
    FloorDBHandler,
    UserDBHandler,
)
from handlers.utils import get_client_bucket_name
from slam_api.apis.floor import (
    FloorCollectionView,
    FloorView,
    floor_app,
    get_bytes_of_floor_deliverable,
)
from tests.constants import FLAKY_RERUNS, USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.integration.utils import response_message
from tests.utils import login_with


@pytest.mark.parametrize(
    "user_role", [USER_ROLE.TEAMMEMBER, USER_ROLE.ARCHILYSE_ONE_ADMIN]
)
def test_update_floor(client, floor, user_role):
    login_with(client, USERS[user_role.name])
    url = get_address_for(
        blueprint=floor_app,
        view_function=FloorView,
        floor_id=floor["id"],
        use_external_address=False,
    )
    request_body = {"floor_number": 42}
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.OK, response.data
    assert (
        FloorDBHandler.get_by(id=floor["id"])["floor_number"]
        == request_body["floor_number"]
    )


def login_external_customer(client):
    login = "test"
    pwd = "test"

    new_customer = ClientDBHandler.add(name="OtherCustomer")
    new_user = UserDBHandler.add(
        name=new_customer["name"],
        login=login,
        password=pwd,
        roles=[USER_ROLE.ARCHILYSE_ONE_ADMIN],
        client_id=new_customer["id"],
        email="test@test.com",
    )
    login_with(
        client=client,
        user=dict(
            name=new_user["name"],
            login=login,
            password=pwd,
            roles=new_user["roles"],
            client_id=new_customer["id"],
        ),
    )
    return new_user, new_customer


@pytest.mark.parametrize(
    "has_permission, expected_response_status",
    [(True, HTTPStatus.OK), (False, HTTPStatus.FORBIDDEN)],
)
@login_as([USER_ROLE.DMS_LIMITED.name])
def test_get_floors_dms_limited(
    client,
    client_db,
    site,
    building,
    floor,
    site_coordinates,
    login,
    make_sites,
    make_buildings,
    make_plans,
    make_floor,
    has_permission,
    expected_response_status,
):

    (other_site,) = make_sites(*(client_db,), group_id=login["group"]["id"])

    (other_building,) = make_buildings(*(other_site,))

    (other_plan,) = make_plans(*(other_building,))

    make_floor(building=other_building, plan=other_plan, floornumber=1)

    if has_permission:
        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.READ.name,
        )

    response = client.get(
        get_address_for(
            blueprint=floor_app,
            use_external_address=False,
            view_function=FloorCollectionView,
            building_id=building["id"],
        )
    )

    assert response.status_code == expected_response_status, response_message(
        response=response
    )

    if expected_response_status == HTTPStatus.OK:

        assert len(response.json) == 1
        assert {element["id"] for element in response.json} == {
            floor["id"],
        }
    elif expected_response_status == HTTPStatus.FORBIDDEN:
        assert response.json["msg"] == "User is not allowed to access this building"


class TestDownloadFloorFiles:
    @staticmethod
    def test_missing_arguments(client, floor, login):
        response = client.get(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=get_bytes_of_floor_deliverable,
                floor_id=floor["id"],
            )
        )
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert response.json["errors"] == {
            "querystring": {
                "file_format": ["Missing data for required field."],
                "language": ["Missing data for required field."],
            }
        }

    @staticmethod
    def test_download_successful(
        client, floor, login, mocked_gcp_download_file_as_bytes, client_db
    ):
        new_link = "fake link"
        FloorDBHandler.update(
            item_pks={"id": floor["id"]},
            new_values={"gcs_en_floorplan_link": new_link},
        )
        response = client.get(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=get_bytes_of_floor_deliverable,
                floor_id=floor["id"],
                file_format=SUPPORTED_OUTPUT_FILES.PNG.name,
                language=SUPPORTED_LANGUAGES.EN.name,
            )
        )
        assert response.status_code == HTTPStatus.OK
        assert SUPPORTED_OUTPUT_FILES.PNG.name.lower() in response.mimetype
        assert (
            response.headers[0][1]
            == 'attachment; filename="Big-ass portfolio_building_1_floor_1_EN.png"'
        )
        # Check filename
        mocked_gcp_download_file_as_bytes.assert_called_with(
            bucket_name=get_client_bucket_name(client_id=client_db["id"]),
            source_file_name=GCloudStorageHandler._convert_media_link_to_file_in_gcp(
                new_link
            ),
        )

    @staticmethod
    def test_download_missing_link(mock_gcp_client, client, floor, login):
        response = client.get(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=get_bytes_of_floor_deliverable,
                floor_id=floor["id"],
                file_format=SUPPORTED_OUTPUT_FILES.PNG.name,
                language=SUPPORTED_LANGUAGES.EN.name,
            )
        )
        assert response.status_code == HTTPStatus.NOT_FOUND

    @staticmethod
    def test_post_floor(mocker, client, building, plan):
        mocker.patch.object(PlanHandler, "add", return_value=plan)
        floor_number = 3

        response = client.post(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=FloorCollectionView,
            ),
            content_type="multipart/form-data",
            data={
                "floorplan": FileStorage(
                    stream=BytesIO(b"something"),
                    filename="floorplan.jpg",
                    content_type="image/jpeg",
                ),
                "floor_lower_range": floor_number,
                "building_id": plan["building_id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json == [
            {
                "building_id": building["id"],
                "floor_number": floor_number,
                "plan_id": plan["id"],
            }
        ]

    @staticmethod
    def test_post_floor_with_dxf_file_returns_feedback_error(mocker, client, building):
        mocker.patch.object(
            PlanHandler,
            "load_dxf",
            side_effect=DXFImportException("Error creating the DXF file"),
        )
        response = client.post(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=FloorCollectionView,
            ),
            content_type="multipart/form-data",
            data={
                "floorplan": FileStorage(
                    stream=BytesIO(b"something"),
                    filename="floorplan.dxf",
                    content_type=DXF_MIME_TYPE,
                ),
                "floor_lower_range": 3,
                "building_id": building["id"],
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert "Error creating the DXF file" in response.json["msg"]

    @staticmethod
    def test_post_identical_floorplan_does_not_delete_existing_floors(
        mocker, client, building, plan, make_floor
    ):
        for i in (8, 9, 10):
            make_floor(building=building, plan=plan, floornumber=i)

        mocker.patch.object(
            PlanHandler, "get_existing_identical_plan", return_value=plan
        )
        response = client.post(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=FloorCollectionView,
                site_id=plan["site_id"],
            ),
            content_type="multipart/form-data",
            data={
                "floorplan": FileStorage(
                    stream=BytesIO(b"something"),
                    filename="floorplan.jpg",
                    content_type="image/jpeg",
                ),
                "floor_lower_range": 0,
                "floor_upper_range": 2,
                "building_id": plan["building_id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert {floor["floor_number"] for floor in response.json} == {0, 1, 2, 8, 9, 10}

    def test_return_error_message_if_floor_number_already_exists(
        self, mocker, client, building, plan, floor
    ):
        mocker.patch.object(PlanHandler, "add", return_value={"id": 999})
        response = client.post(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=FloorCollectionView,
                site_id=plan["site_id"],
            ),
            content_type="multipart/form-data",
            data={
                "floorplan": FileStorage(
                    stream=BytesIO(b"something"),
                    filename="floorplan.jpg",
                    content_type="image/jpeg",
                ),
                "floor_lower_range": 0,
                "floor_upper_range": 2,
                "building_id": plan["building_id"],
            },
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert (
            response.json["msg"]
            == "Some of the floor numbers requested to be created {0, 1, 2} already exist for the building"
        )

    @staticmethod
    @pytest.mark.flaky(reruns=FLAKY_RERUNS)
    def test_post_compliant_dxf(
        mocker,
        client,
        building,
        dxf_sample_compliant,
        mocked_gcp_upload_bytes_to_bucket,
    ):
        response = client.post(
            get_address_for(
                blueprint=floor_app,
                use_external_address=False,
                view_function=FloorCollectionView,
            ),
            content_type="multipart/form-data",
            data={
                "floorplan": FileStorage(
                    stream=BytesIO(dxf_sample_compliant),
                    filename="floorplan.dxf",
                    content_type=DXF_MIME_TYPE,
                ),
                "floor_lower_range": 3,
                "building_id": building["id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        plan_id = response.json[0]["plan_id"]

        layout = PlanLayoutHandler(plan_id=plan_id).get_layout(
            scaled=True, validate=True, classified=True
        )
        assert Counter([error.violation_type.name for error in layout.errors]) == {
            "DOOR_NOT_CONNECTING_AREAS": 9,
            "FEATURE_NOT_ASSIGNED": 3,
        }
