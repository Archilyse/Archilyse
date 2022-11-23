import io
import mimetypes
from http import HTTPStatus
from pathlib import Path

import pytest

from common_utils.constants import DMS_FOLDER_NAME, DMS_PERMISSION, USER_ROLE
from handlers.db import DmsPermissionDBHandler, FileDBHandler, UnitAreaDBHandler
from handlers.utils import get_client_bucket_name
from slam_api.apis.file import (
    FileCommentView,
    FileTrashView,
    FileTrashViewCollection,
    FileView,
    FileViewCollection,
    FileViewDownload,
    file_app,
)
from slam_api.utils import Entities
from tests.constants import USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.utils import login_with

FILE_COLLECTION_URL = get_address_for(
    blueprint=file_app,
    use_external_address=False,
    view_function=FileViewCollection,
)


class TestFileViewCollection:
    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.CREATED),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "site_id", None, HTTPStatus.CREATED),
            (
                USER_ROLE.DMS_LIMITED,
                "building_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.CREATED,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "floor_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.CREATED,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.CREATED,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "area_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.CREATED,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.CREATED,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.FORBIDDEN,
            ),
        ],
    )
    def test_post_simple_file(
        self,
        client,
        client_db,
        site,
        mocked_gcp_upload_bytes_to_bucket,
        site_with_3_units,
        mocked_gcp_delete,
        user_role,
        entity_type,
        permission_type,
        expected_response,
    ):
        login = login_with(client, USERS[user_role.name])
        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site_with_3_units["site"]["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )

        entity_type_association = {
            "client_id": {"client_id": client_db["id"]},
            "building_id": {"building_id": site_with_3_units["building"]["id"]},
            "site_id": {"site_id": site_with_3_units["site"]["id"]},
            "plan_id": {"plan_id": site_with_3_units["plan"]["id"]},
            "floor_id": {"floor_id": site_with_3_units["floor"]["id"]},
            "unit_id": {"unit_id": site_with_3_units["units"][0]["id"]},
            "area_id": {
                "unit_id": site_with_3_units["units"][0]["id"],
                "area_id": list(
                    UnitAreaDBHandler.find_in(
                        unit_id=[site_with_3_units["units"][0]["id"]],
                        output_columns=["area_id"],
                    )
                )[0]["area_id"],
            },
        }

        attached_entity = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {
                "client_id": client_db["id"],
                **entity_type_association[entity_type],
            }
        )

        response = client.post(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileViewCollection,
            ),
            content_type="multipart/form-data",
            data={
                "file": (
                    io.BytesIO(b"abcdef"),
                    "AC20-FZK-Haus.ifc",
                    mimetypes.types_map[".ifc"],
                ),
                "name": "foo-bar",
                "labels": ["foo", "bar"],
                **attached_entity,
            },
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.CREATED:
            assert response.json["name"] == "foo-bar"
            assert response.json["checksum"] == "6AtQFwmJUPxYqtg8jBSXjg%3D%3D"
            assert response.json["labels"] == ["foo", "bar"]
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to create this file"

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_file_to_folder(
        self,
        client,
        client_db,
        login,
        mocked_gcp_upload_bytes_to_bucket,
        mocked_gcp_delete,
        make_folder,
    ):
        folder = make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            labels=["TEST", "IT"],
        )

        response = client.post(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileViewCollection,
            ),
            content_type="multipart/form-data",
            data={
                "file": (
                    io.BytesIO(b"abcdef"),
                    "AC20-FZK-Haus.ifc",
                    mimetypes.types_map[".ifc"],
                ),
                "name": "foo-bar",
                "folder_id": folder["id"],
            },
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json["folder_id"] == folder["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_wrong_mime(
        self, client, client_db, login, mocked_gcp_upload_bytes_to_bucket
    ):
        response = client.post(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileViewCollection,
            ),
            content_type="multipart/form-data",
            data={
                "file": (
                    io.BytesIO(b"abcdef"),
                    "AC20-FZK-Haus.ifc",
                    "application/ifc2",
                ),
                "name": "foo-bar",
                "client_id": client_db["id"],
            },
        )

        assert response.status_code == HTTPStatus.CREATED

    def test_post_unknown_client(
        self, client, client_db, login, fixtures_path, mocked_gcp_upload_bytes_to_bucket
    ):
        response = client.post(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileViewCollection,
            ),
            content_type="multipart/form-data",
            data={
                "file": (
                    io.BytesIO(b"abcdef"),
                    "AC20-FZK-Haus.ifc",
                    mimetypes.types_map[".ifc"],
                ),
                "name": "foo-bar",
                "client_id": -1,
            },
        )
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert (
            response.json["msg"]
            == "Entity not found! Could not find one item for table ClientDBModel"
        )

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_with_associations(
        self,
        client,
        client_db,
        unit,
        login,
        mocked_gcp_upload_bytes_to_bucket,
    ):

        response = client.post(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileViewCollection,
            ),
            content_type="multipart/form-data",
            data={
                "file": (
                    io.BytesIO(b"abcdef"),
                    "AC20-FZK-Haus.ifc",
                    mimetypes.types_map[".ifc"],
                ),
                "name": "foo-bar",
                "unit_id": unit["id"],
            },
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json["building_id"]
        assert response.json["client_id"]
        assert response.json["floor_id"]
        assert response.json["site_id"]
        assert response.json["unit_id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    @pytest.mark.parametrize(
        "user_role, permission",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, None),
            (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
            (USER_ROLE.ADMIN, None),
        ],
    )
    def test_get_files_by_name_and_entity(
        self,
        client,
        client_db,
        site,
        mocked_gcp_upload_bytes_to_bucket,
        unit,
        make_files,
        user_role,
        permission,
    ):
        login = login_with(client, USERS[user_role.name])
        if permission:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission.name,
            )

        make_files(user_id=login["user"]["id"], name="boss.ifc", unit_id=unit["id"])

        response = client.get(f"{FILE_COLLECTION_URL}?unit_id={unit['id']}")
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == 1

        response = client.get(
            f"{FILE_COLLECTION_URL}?name=foo-bar&unit_id={unit['id']}"
        )
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == 0

        response = client.get(
            f"{FILE_COLLECTION_URL}?name=boss.ifc&unit_id={unit['id']}"
        )
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == 1

        response = client.get(f"{FILE_COLLECTION_URL}?name=boss&unit_id={unit['id']}")
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == 1

        response = client.get(f"{FILE_COLLECTION_URL}?unit_id=100000")
        assert response.status_code == HTTPStatus.NOT_FOUND
        assert (
            response.json["msg"]
            == "Entity not found! Could not find one item for table UnitDBModel"
        )

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    @pytest.mark.parametrize(
        "user_role, permission",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, None),
            (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
            (USER_ROLE.ADMIN, None),
        ],
    )
    def test_get_files_no_other_documents(
        self,
        client,
        client_db,
        site,
        mocked_gcp_upload_bytes_to_bucket,
        make_files,
        user_role,
        permission,
        unit_areas_db,
        floor,
    ):
        from handlers import FileHandler

        login = login_with(client, USERS[user_role.name])
        if permission:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission.name,
            )

        make_files(
            user_id=login["user"]["id"],
            name="boss.ifc",
            unit_id=unit_areas_db[0]["unit_id"],
        )
        make_files(
            user_id=login["user"]["id"],
            name="area1.ifc",
            unit_id=unit_areas_db[0]["unit_id"],
            area_id=unit_areas_db[0]["area_id"],
        )
        make_files(
            user_id=login["user"]["id"],
            name="area2.ifc",
            unit_id=unit_areas_db[1]["unit_id"],
            area_id=unit_areas_db[1]["area_id"],
        )

        # Unit should only get its file
        response = client.get(
            f"{FILE_COLLECTION_URL}?unit_id={unit_areas_db[0]['unit_id']}"
        )
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == 1

        # Area should only get its file
        response = client.get(
            f"{FILE_COLLECTION_URL}?unit_id={unit_areas_db[0]['unit_id']}&area_id={unit_areas_db[0]['area_id']}"
        )
        assert response.status_code == HTTPStatus.OK, response.json
        assert len(response.json) == 1

        # If we return subdocuments of the unit, the area files should be included
        # NOTE: There is no API endpoint for this
        assert (
            len(
                list(
                    FileHandler.get(
                        client_id=client_db["id"],
                        unit_id=unit_areas_db[0]["unit_id"],
                        return_subdocuments=True,
                    )
                )
            )
            == 3
        )

    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_get_files_dms_limited_no_permission(
        self, client, client_db, site, building, login, make_files
    ):
        make_files(
            user_id=login["user"]["id"],
            building_id=building["id"],
            name="the_file",
            n=1,
        )
        response = client.get(
            f"{FILE_COLLECTION_URL}?name=the_file&building_id={building['id']}"
        )
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 0

    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_file_performance_lower_levels_not_returned(
        self, mocker, client, client_db, make_files, login, site, building
    ):
        find_spy = mocker.spy(FileDBHandler, "find")

        make_files(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            name="client_file_only",
            n=1,
        )
        make_files(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            site_id=site["id"],
            name="site_file_only",
            n=1,
        )
        make_files(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            site_id=site["id"],
            building_id=building["id"],
            name="building_file_only",
            n=1,
        )

        response = client.get(f"{FILE_COLLECTION_URL}?client_id={client_db['id']}")
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1

        # we also make sure the endpoint is not filtering in the view
        assert len(find_spy.spy_return) == 1
        assert find_spy.spy_return[0]["name"] == "client_file_only"


class TestFileView:
    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_file_building_to_site(
        self, client, client_db, site, building, login, make_files
    ):
        file = make_files(
            user_id=login["user"]["id"],
            building_id=building["id"],
            name="the_file",
            n=1,
        )[0]
        response = client.put(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=file["id"],
            ),
            json={"site_id": site["id"]},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json["client_id"] == client_db["id"]
        assert response.json["site_id"] == site["id"]
        assert response.json["building_id"] is None
        assert response.json["floor_id"] is None
        assert response.json["unit_id"] is None

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_file_site_to_floor(
        self, client, client_db, site, building, floor, login, make_files
    ):
        file = make_files(
            user_id=login["user"]["id"],
            building_id=site["id"],
            name="the_file",
            n=1,
        )[0]
        response = client.put(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=file["id"],
            ),
            json={"floor_id": floor["id"]},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json["client_id"] == client_db["id"]
        assert response.json["site_id"] == site["id"]
        assert response.json["building_id"] == building["id"]
        assert response.json["floor_id"] == floor["id"]
        assert response.json["unit_id"] is None

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_file_into_folder(
        self, client, client_db, site, building, unit, login, make_files, make_folder
    ):
        file = make_files(user_id=login["user"]["id"], building_id=building["id"])[0]
        folder = make_folder(user_id=login["user"]["id"], unit_id=unit["id"])
        response = client.put(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=file["id"],
            ),
            json={"folder_id": folder["id"]},
        )
        assert response.status_code == HTTPStatus.OK
        for key in Entities.keys:
            assert response.json[key] == folder[key]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_file_from_folder(
        self, client, client_db, site, unit, login, make_files, make_folder
    ):
        """
        Given a folder at unit level
        And a file inside that folder
        When we move the file into the site level
        Then the file is not associated with the folder anymore
        And the file is associated only with the site and the client
        """
        folder = make_folder(user_id=login["user"]["id"], unit_id=unit["id"])
        file = make_files(user_id=login["user"]["id"], folder_id=folder["id"])[0]

        response = client.put(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=file["id"],
            ),
            json={"site_id": site["id"]},
        )
        assert response.status_code == HTTPStatus.OK
        assert response.json["client_id"] == client_db["id"]
        assert response.json["site_id"] == site["id"]
        assert response.json["folder_id"] is None
        assert all(
            [
                response.json[element_key] is None
                for element_key in Entities.keys
                if element_key not in ("client_id", "site_id")
            ]
        )

    @pytest.mark.parametrize(
        "user_role, permission, expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, None, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, None, HTTPStatus.FORBIDDEN),
        ],
    )
    def test_move_file_from_site_to_another(
        self,
        client,
        client_db,
        site,
        make_files,
        make_sites,
        user_role,
        permission,
        expected_response,
    ):
        login = login_with(client, USERS[user_role.name])

        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )

        (other_site,) = make_sites(*(client_db,))
        if permission:
            DmsPermissionDBHandler.add(
                site_id=other_site["id"],
                user_id=login["user"]["id"],
                rights=permission.name,
            )

        file = make_files(user_id=login["user"]["id"], site_id=site["id"])[0]

        response = client.put(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=file["id"],
            ),
            json={"site_id": other_site["id"]},
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert response.json["site_id"] == other_site["id"]
        else:
            assert response.json["msg"] == "User is not allowed to move file here"

    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "site_id", None, HTTPStatus.OK),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.FORBIDDEN,
            ),
        ],
    )
    def test_put_labels_file(
        self,
        client,
        client_db,
        site,
        user_role,
        entity_type,
        permission_type,
        expected_response,
        make_files,
    ):
        login = login_with(client, USERS[user_role.name])

        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )

        attached_entity = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: site["id"]}
        )

        files = make_files(
            user_id=login["user"]["id"], name="boss-ifc", **attached_entity
        )

        response = client.put(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=files[0]["id"],
            ),
            json={"labels": ["far", "boo"]},
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert response.json["labels"] == ["far", "boo"]
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this file"

    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "site_id", None, HTTPStatus.OK),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.READ,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                None,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.READ,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                None,
                HTTPStatus.OK,
            ),
        ],
    )
    def test_get_file(
        self,
        client,
        client_db,
        site,
        user_role,
        entity_type,
        permission_type,
        expected_response,
        make_files,
    ):
        login = login_with(client, USERS[user_role.name])

        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )

        attached_entity = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: site["id"]}
        )

        files = make_files(
            user_id=login["user"]["id"], name="boss-ifc", **attached_entity
        )

        response = client.get(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=files[0]["id"],
            ),
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert response.json["id"] == files[0]["id"]
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to access this file"

    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.NO_CONTENT),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "site_id", None, HTTPStatus.NO_CONTENT),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "site_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.NO_CONTENT,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                None,
                HTTPStatus.FORBIDDEN,
            ),
        ],
    )
    def test_delete_file(
        self,
        client,
        client_db,
        mocked_gcp_delete,
        site,
        user_role,
        entity_type,
        permission_type,
        expected_response,
        make_files,
    ):
        login = login_with(client, USERS[user_role.name])

        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )

        attached_entity = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: site["id"]}
        )

        files = make_files(
            user_id=login["user"]["id"], name="boss-ifc", **attached_entity
        )

        response = client.delete(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileView,
                file_id=files[0]["id"],
            ),
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.NO_CONTENT:
            assert [
                (
                    call_args[1]["bucket_name"],
                    call_args[1]["source_folder"],
                    call_args[1]["filename"],
                )
                for call_args in mocked_gcp_delete.call_args_list
            ] == [
                (
                    get_client_bucket_name(client_id=client_db["id"]),
                    Path(DMS_FOLDER_NAME),
                    Path(file["checksum"]),
                )
                for file in files
            ]

            assert len(FileDBHandler.find()) == 0

        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this file"


class TestFileCommentView:
    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.CREATED),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "unit_id", None, HTTPStatus.CREATED),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.CREATED,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                None,
                HTTPStatus.FORBIDDEN,
            ),
        ],
    )
    def test_add_comments(
        self,
        client,
        client_db,
        site,
        unit,
        make_files,
        user_role,
        entity_type,
        permission_type,
        expected_response,
    ):
        login = login_with(client, USERS[user_role.name])

        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )

        attached_entity = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: unit["id"]}
        )

        files = make_files(
            user_id=login["user"]["id"], name="boss-ifc", **attached_entity
        )

        file_id = files[0]["id"]

        response = client.post(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileCommentView,
                file_id=file_id,
            ),
            json={"comment": "bar and foo"},
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.CREATED:
            assert response.json["comments"][0]["comment"] == "bar and foo"
            assert (
                response.json["comments"][0]["creator"]["name"] == login["user"]["name"]
            )
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this file"


class TestFileTrashViewCollection:
    @pytest.mark.parametrize(
        "user_role, permission",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, None),
            (USER_ROLE.DMS_LIMITED, DMS_PERMISSION.READ),
        ],
    )
    def test_get_trash_collection(
        self,
        client,
        client_db,
        site,
        make_sites,
        make_files,
        user_role,
        permission,
    ):
        login = login_with(client, USERS[user_role.name])

        if permission:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission.name,
            )
        (other_site,) = make_sites(*(client_db,))
        files = make_files(
            user_id=login["user"]["id"],
            name="boss-ifc",
            site_id=site["id"],
            deleted=True,
        )
        files_other_site = make_files(
            user_id=login["user"]["id"],
            name="boss-ifc",
            site_id=other_site["id"],
            deleted=True,
        )
        make_files(user_id=login["user"]["id"], name="not_deleted", site_id=site["id"])

        response = client.get(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileTrashViewCollection,
            ),
        )
        assert response.status_code == HTTPStatus.OK
        if user_role is USER_ROLE.ARCHILYSE_ONE_ADMIN:
            assert {file["id"] for file in files} | {
                file["id"] for file in files_other_site
            } == {file["id"] for file in response.json}

        else:
            assert {file["id"] for file in files} == {
                file["id"] for file in response.json
            }

    class TestFileTrashView:
        @pytest.mark.parametrize("is_deleted", [False, True])
        @pytest.mark.parametrize(
            "user_role,entity_type, permission_type,expected_response",
            [
                (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
                (USER_ROLE.ARCHILYSE_ONE_ADMIN, "unit_id", None, HTTPStatus.OK),
                (
                    USER_ROLE.DMS_LIMITED,
                    "unit_id",
                    DMS_PERMISSION.READ,
                    HTTPStatus.FORBIDDEN,
                ),
                (
                    USER_ROLE.DMS_LIMITED,
                    "unit_id",
                    DMS_PERMISSION.WRITE,
                    HTTPStatus.OK,
                ),
                (
                    USER_ROLE.DMS_LIMITED,
                    "client_id",
                    DMS_PERMISSION.WRITE,
                    HTTPStatus.FORBIDDEN,
                ),
                (
                    USER_ROLE.DMS_LIMITED,
                    "unit_id",
                    None,
                    HTTPStatus.FORBIDDEN,
                ),
            ],
        )
        def test_put_file_to_trash_or_restore(
            self,
            client,
            client_db,
            site,
            unit,
            make_sites,
            make_files,
            user_role,
            entity_type,
            permission_type,
            expected_response,
            is_deleted,
        ):
            login = login_with(client, USERS[user_role.name])

            if permission_type:
                DmsPermissionDBHandler.add(
                    site_id=site["id"],
                    user_id=login["user"]["id"],
                    rights=permission_type.name,
                )

            attached_entity = (
                {entity_type: client_db["id"]}
                if entity_type == "client_id"
                else {entity_type: unit["id"]}
            )

            files = make_files(
                user_id=login["user"]["id"],
                name="some",
                **attached_entity,
                deleted=is_deleted,
            )

            response = client.put(
                get_address_for(
                    blueprint=file_app,
                    use_external_address=False,
                    view_function=FileTrashView,
                    file_id=files[0]["id"],
                ),
                json={"deleted": not is_deleted},
            )

            assert response.status_code == expected_response
            if expected_response == HTTPStatus.OK:
                assert FileDBHandler.get_by(id=files[0]["id"])["deleted"] == (
                    not is_deleted
                )

            elif expected_response == HTTPStatus.FORBIDDEN:
                assert response.json["msg"] == "User is not allowed to edit this file"


class TestFileViewDownload:
    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "unit_id", None, HTTPStatus.OK),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                DMS_PERMISSION.READ,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.READ,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                None,
                HTTPStatus.FORBIDDEN,
            ),
        ],
    )
    def test_download_file(
        self,
        client,
        client_db,
        site,
        unit,
        make_files,
        user_role,
        entity_type,
        permission_type,
        expected_response,
        mocker,
    ):
        from handlers import FileHandler

        mocked_file = bytes("placeholder", "utf-8")
        mocked_file_download = mocker.patch.object(
            FileHandler, "download", return_value=mocked_file
        )
        login = login_with(client, USERS[user_role.name])

        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )

        attached_entity = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: unit["id"]}
        )

        files = make_files(
            user_id=login["user"]["id"],
            name="some",
            **attached_entity,
        )

        response = client.get(
            get_address_for(
                blueprint=file_app,
                use_external_address=False,
                view_function=FileViewDownload,
                file_id=files[0]["id"],
            ),
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert (
                mocked_file_download.call_args_list[0].kwargs["checksum"]
                == files[0]["checksum"]
            )
            assert response.data == mocked_file

        else:
            assert response.json["msg"] == "User is not allowed to access this file"
