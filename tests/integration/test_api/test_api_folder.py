from http import HTTPStatus
from itertools import chain
from pathlib import Path

import pytest

from common_utils.constants import DMS_FOLDER_NAME, DMS_PERMISSION, USER_ROLE
from handlers.db import (
    ClientDBHandler,
    DmsPermissionDBHandler,
    FileDBHandler,
    FolderDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
)
from handlers.utils import get_client_bucket_name
from slam_api.apis.folder import (
    FolderFileView,
    FolderRestoreView,
    FolderSubfolderView,
    FolderTrashView,
    FolderTrashViewCollection,
    FolderView,
    FolderViewCollection,
    folder_app,
)
from tests.constants import USERS
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for
from tests.utils import login_with


class TestFolderViewCollection:
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
    def test_post_folder(
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

        folder_name = "MainFolder"
        labels = ["Le", "szek"]
        response = client.post(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderViewCollection,
            ),
            json={"name": folder_name, "labels": labels, **attached_entity},
        )

        assert response.status_code == expected_response
        if response.status_code == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to create this folder"
        elif response.status_code == HTTPStatus.CREATED:
            assert response.json["name"] == folder_name
            assert response.json["labels"] == labels
            assert response.json["client_id"] == client_db["id"]
            if entity_type == "building_id":
                for key, expected_entity in zip(
                    ("site_id", "building_id"),
                    (site_with_3_units["site"], site_with_3_units["building"]),
                ):
                    assert response.json[key] == expected_entity["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_subfolder(
        self, client, client_db, login, site, building, floor, unit, make_folder
    ):
        main_folder = make_folder(
            user_id=login["user"]["id"], floor_id=floor["id"], name="MainFolder"
        )

        response = client.post(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderViewCollection,
            ),
            json={"name": "Subfolder", "parent_folder_id": main_folder["id"]},
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json["name"] == "Subfolder"
        assert response.json["parent_folder_id"] == main_folder["id"]
        assert response.json["floor_id"] == floor["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_folder_no_labels(self, client, client_db, unit):
        response = client.post(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderViewCollection,
            ),
            json={"name": "MainFolder", "unit_id": unit["id"]},
        )
        assert response.status_code == HTTPStatus.CREATED
        assert response.json["labels"] is None

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_no_association_provided(self, client, login):
        response = client.post(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderViewCollection,
            ),
            json={"name": "MainFolder"},
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert response.json == "No parent entities provided"

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_post_access_forbidden(self, client, site, unit, client_db):
        other_client = ClientDBHandler.add(name="Other Client")
        SiteDBHandler.update(
            item_pks={"id": site["id"]}, new_values={"client_id": other_client["id"]}
        )
        response = client.post(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderViewCollection,
            ),
            json={"name": "MainFolder", "unit_id": unit["id"]},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json["msg"] == "Access to this resource is forbidden."

    @pytest.mark.parametrize(
        "association_key", ["unit_id", "floor_id", "building_id", "site_id"]
    )
    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_folder_by_association(
        self,
        client,
        client_db,
        site,
        building,
        floor,
        unit,
        login,
        make_folder,
        association_key,
    ):
        key_entity_mapping = {
            "unit_id": unit,
            "floor_id": floor,
            "building_id": building,
            "site_id": site,
        }

        # adding a folder to every entity from unit to site
        for key, entity in key_entity_mapping.items():
            make_folder(
                user_id=login["user"]["id"],
                client_id=client_db["id"],
                labels=["TEST", "IT"],
                **{key: entity["id"]},
            )

        # adding extra folder for current association
        make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            labels=["TEST", "IT"],
            **{association_key: key_entity_mapping[association_key]["id"]},
        )
        http_address = get_address_for(
            blueprint=folder_app,
            use_external_address=False,
            view_function=FolderViewCollection,
        )
        query_string = f"?{association_key}={key_entity_mapping[association_key]['id']}"
        response = client.get(http_address + query_string)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 2
        assert (
            response.json[0][association_key]
            == key_entity_mapping[association_key]["id"]
        )

    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_get_folder_dms_limited_attached_to_client(
        self,
        client,
        client_db,
        site,
        floor,
        login,
        make_folder,
    ):

        folder = make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            labels=["TEST", "IT"],
        )
        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )

        http_address = get_address_for(
            blueprint=folder_app,
            use_external_address=False,
            view_function=FolderViewCollection,
        )
        query_string = f"?client_id={client_db['id']}"
        response = client.get(http_address + query_string)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert response.json[0]["id"] == folder["id"]

    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_get_folder_dms_limited_attached_to_floor(
        self,
        client,
        client_db,
        site,
        floor,
        login,
        make_folder,
    ):

        folder = make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            labels=["TEST", "IT"],
            floor_id=floor["id"],
        )
        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )

        http_address = get_address_for(
            blueprint=folder_app,
            use_external_address=False,
            view_function=FolderViewCollection,
        )
        query_string = f"?floor_id={floor['id']}"
        response = client.get(http_address + query_string)
        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert response.json[0]["id"] == folder["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_not_showing_deleted_folders(
        self, client, client_db, floor, login, make_folder
    ):
        make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            floor_id=floor["id"],
            deleted=True,
        )
        http_address = get_address_for(
            blueprint=folder_app,
            use_external_address=False,
            view_function=FolderViewCollection,
        )
        query_string = f"?floor_id={floor['id']}"
        response = client.get(http_address + query_string)

        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 0

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_only_folders_not_subfolders(
        self, client, client_db, floor, unit, login, make_folder
    ):
        folder_directly_attached = make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            floor_id=floor["id"],
        )
        make_folder(
            user_id=login["user"]["id"],
            parent_folder_id=folder_directly_attached["id"],
        )
        http_address = get_address_for(
            blueprint=folder_app,
            use_external_address=False,
            view_function=FolderViewCollection,
        )
        query_string = f"?floor_id={floor['id']}"
        response = client.get(http_address + query_string)

        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert response.json[0]["id"] == folder_directly_attached["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_folder_by_name(
        self, client, client_db, floor, unit, login, make_folder
    ):
        make_folder(user_id=login["user"]["id"], floor_id=floor["id"], name="Trump")
        folder_to_find = make_folder(
            user_id=login["user"]["id"], floor_id=floor["id"], name="Biden"
        )

        http_address = get_address_for(
            blueprint=folder_app,
            use_external_address=False,
            view_function=FolderViewCollection,
        )
        query_string = f"?floor_id={floor['id']}&name={folder_to_find['name']}"
        response = client.get(http_address + query_string)

        assert response.status_code == HTTPStatus.OK
        assert len(response.json) == 1
        assert response.json[0]["id"] == folder_to_find["id"]


class TestFolderView:
    @pytest.mark.parametrize(
        "user_role,entity_type,permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "unit_id", None, HTTPStatus.OK),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.WRITE,
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
                DMS_PERMISSION.WRITE,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                DMS_PERMISSION.READ,
                HTTPStatus.OK,
            ),
        ],
    )
    def test_get_folder_dms_limited(
        self,
        client,
        client_db,
        site,
        unit,
        make_folder,
        user_role,
        permission_type,
        entity_type,
        expected_response,
    ):
        login = login_with(client, USERS[user_role.name])

        associations = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: unit["id"]}
        )
        folder = make_folder(user_id=login["user"]["id"], **associations)
        if permission_type:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=permission_type.name,
            )
        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert response.json["id"] == folder["id"]
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to access this folder"

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_folder_access_forbidden(self, client, client_db, login, make_folder):
        other_client = ClientDBHandler.add(name="OtherClient")
        folder = make_folder(user_id=login["user"]["id"], client_id=other_client["id"])
        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json["msg"] == "Access to this resource is forbidden."

    @pytest.mark.parametrize(
        "user_role,entity_type,permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (
                USER_ROLE.DMS_LIMITED,
                "client_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.FORBIDDEN,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "building_id",
                DMS_PERMISSION.WRITE,
                HTTPStatus.OK,
            ),
            (
                USER_ROLE.DMS_LIMITED,
                "building_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
        ],
    )
    def test_update_folder(
        self,
        client,
        client_db,
        site,
        building,
        make_folder,
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
        associations = (
            {entity_type: client_db["id"]}
            if entity_type == "client_id"
            else {entity_type: building["id"]}
        )
        folder = make_folder(
            user_id=login["user"]["id"], labels=["TEST", "IT"], **associations
        )

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"name": "NEWNAME", "labels": ["NEW_LABELS"]},
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert response.json["name"] == "NEWNAME"
            assert response.json["labels"] == ["NEW_LABELS"]

        if expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this folder"

    @pytest.mark.parametrize(
        "userrole",
        [USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED],
    )
    def test_move_folder_from_site_to_another(
        self, client, client_db, userrole, site, make_folder, make_sites
    ):
        login = login_with(client, USERS[userrole.name])
        folder = make_folder(user_id=login["user"]["id"], site_id=site["id"])
        other_site = make_sites(*(client_db,))[0]
        if userrole is USER_ROLE.DMS_LIMITED:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=DMS_PERMISSION.WRITE.name,
            )
            DmsPermissionDBHandler.add(
                site_id=other_site["id"],
                user_id=login["user"]["id"],
                rights=DMS_PERMISSION.WRITE.name,
            )

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"site_id": other_site["id"]},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json["site_id"] == other_site["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_folder_unit_to_site(
        self, client, client_db, site, unit, login, make_folder, make_files
    ):
        folder = make_folder(
            user_id=login["user"]["id"], unit_id=unit["id"], name="mainfolder"
        )
        subfolder = make_folder(
            user_id=login["user"]["id"], parent_folder_id=folder["id"], name="subfolder"
        )
        file_in_folder = make_files(
            user_id=login["user"]["id"], folder_id=folder["id"], name="file_a"
        )[0]
        file_in_subfolder = make_files(
            user_id=login["user"]["id"], folder_id=subfolder["id"], name="file_b"
        )[0]

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"site_id": site["id"]},
        )
        assert response.status_code == HTTPStatus.OK
        for document in chain(FileDBHandler.find(), FolderDBHandler.find()):
            assert document["client_id"] == client_db["id"]
            assert document["site_id"] == site["id"]
            assert document["building_id"] is None
            assert document["floor_id"] is None
            assert document["unit_id"] is None

        assert FolderDBHandler.get_by(id=subfolder["id"])["name"] == subfolder["name"]
        assert (
            FileDBHandler.get_by(id=file_in_folder["id"])["name"]
            == file_in_folder["name"]
        )
        assert (
            FileDBHandler.get_by(id=file_in_subfolder["id"])["name"]
            == file_in_subfolder["name"]
        )

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_folder_site_to_floor(
        self, client, client_db, site, building, floor, login, make_folder, make_files
    ):
        folder = make_folder(
            user_id=login["user"]["id"], site_id=site["id"], name="mainfolder"
        )
        subfolder = make_folder(
            user_id=login["user"]["id"], parent_folder_id=folder["id"], name="subfolder"
        )
        file_in_folder = make_files(
            user_id=login["user"]["id"], folder_id=folder["id"], name="file_a"
        )[0]
        file_in_subfolder = make_files(
            user_id=login["user"]["id"], folder_id=subfolder["id"], name="file_b"
        )[0]

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"floor_id": floor["id"]},
        )
        assert response.status_code == HTTPStatus.OK
        for document in chain(FileDBHandler.find(), FolderDBHandler.find()):
            assert document["client_id"] == client_db["id"]
            assert document["site_id"] == site["id"]
            assert document["building_id"] == building["id"]
            assert document["floor_id"] == floor["id"]
            assert document["unit_id"] is None

        assert FolderDBHandler.get_by(id=subfolder["id"])["name"] == subfolder["name"]
        assert (
            FileDBHandler.get_by(id=file_in_folder["id"])["name"]
            == file_in_folder["name"]
        )
        assert (
            FileDBHandler.get_by(id=file_in_subfolder["id"])["name"]
            == file_in_subfolder["name"]
        )

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_folder_into_folder(
        self, client, client_db, site, building, floor, login, make_folder, make_files
    ):
        folder = make_folder(user_id=login["user"]["id"], site_id=site["id"])

        folder_to_move_into = make_folder(
            user_id=login["user"]["id"], building_id=building["id"]
        )

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"parent_folder_id": folder_to_move_into["id"]},
        )

        assert response.status_code == HTTPStatus.OK
        folder_db = FolderDBHandler.get_by(id=folder["id"])
        assert folder_db["parent_folder_id"] == folder_to_move_into["id"]
        assert folder_db["building_id"] == building["id"]

    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_move_folder_from_folder(
        self, client, client_db, site, building, floor, login, make_folder, make_files
    ):

        parent_folder = make_folder(
            user_id=login["user"]["id"], building_id=building["id"]
        )
        folder = make_folder(
            user_id=login["user"]["id"], parent_folder_id=parent_folder["id"]
        )

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"site_id": site["id"]},
        )

        assert response.status_code == HTTPStatus.OK
        folder_db = FolderDBHandler.get_by(id=folder["id"])
        assert folder_db["parent_folder_id"] is None
        assert folder_db["building_id"] is None
        assert folder_db["site_id"] == site["id"]

    @pytest.mark.parametrize(
        "userrole",
        [USER_ROLE.ADMIN, USER_ROLE.ARCHILYSE_ONE_ADMIN, USER_ROLE.DMS_LIMITED],
    )
    def test_move_folder_to_other_client_not_allowed(
        self,
        client,
        client_db,
        site,
        floor,
        userrole,
        make_sites,
        make_folder,
        make_files,
    ):
        login = login_with(client, USERS[userrole.name])

        folder = make_folder(user_id=login["user"]["id"], floor_id=floor["id"])

        if userrole is USER_ROLE.DMS_LIMITED:
            DmsPermissionDBHandler.add(
                site_id=site["id"],
                user_id=login["user"]["id"],
                rights=DMS_PERMISSION.WRITE.name,
            )

        other_client = ClientDBHandler.add(name="OtherClient")
        other_site = make_sites(*(other_client,))[0]

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"site_id": other_site["id"]},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert (
            response.json["msg"] == "Its not allowed to move a folder to another client"
        )

    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_move_folder_missing_permissions(
        self, client, client_db, site, login, make_sites, make_folder
    ):

        folder = make_folder(user_id=login["user"]["id"], site_id=site["id"])

        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.WRITE.name,
        )

        other_site = make_sites(*(client_db,))[0]

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
            json={"site_id": other_site["id"]},
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert response.json["msg"] == "User is not allowed to move folder here"

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
    def test_delete_folder(
        self,
        client,
        client_db,
        site,
        make_folder,
        mocked_gcp_delete,
        make_files,
        user_role,
        permission_type,
        expected_response,
        entity_type,
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

        folder = make_folder(
            user_id=login["user"]["id"],
            **attached_entity,
        )

        subfolder = make_folder(
            user_id=login["user"]["id"], parent_folder_id=folder["id"]
        )
        files = make_files(user_id=login["user"]["id"], folder_id=folder["id"], n=3)

        files.extend(
            make_files(user_id=login["user"]["id"], folder_id=subfolder["id"], n=2)
        )

        response = client.delete(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderView,
                folder_id=folder["id"],
            ),
        )
        assert response.status_code == expected_response
        if expected_response == HTTPStatus.NO_CONTENT:
            assert {
                (
                    call_args[1]["bucket_name"],
                    call_args[1]["source_folder"],
                    call_args[1]["filename"],
                )
                for call_args in mocked_gcp_delete.call_args_list
            } == {
                (
                    get_client_bucket_name(client_id=client_db["id"]),
                    Path(DMS_FOLDER_NAME),
                    Path(file["checksum"]),
                )
                for file in files
            }

            assert len(FolderDBHandler.find()) == 0
            assert len(FileDBHandler.find()) == 0

        elif HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this folder"


class TestFolderFileView:
    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_files_of_deleted_folder(
        self, client, client_db, login, make_folder, make_files
    ):
        folder = make_folder(user_id=login["user"]["id"], client_id=client_db["id"])

        files = make_files(user_id=login["user"]["id"], folder_id=folder["id"], n=3)

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderTrashView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == HTTPStatus.OK
        assert response.json["deleted"] is True

        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderFileView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == HTTPStatus.OK
        assert {file["id"] for file in response.json} == {file["id"] for file in files}

    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "site_id", None, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", DMS_PERMISSION.READ, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "site_id", DMS_PERMISSION.READ, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "site_id", DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "site_id", None, HTTPStatus.FORBIDDEN),
        ],
    )
    def test_get_files_in_folder(
        self,
        client,
        client_db,
        site,
        make_folder,
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
            else {entity_type: site["id"]}
        )

        folder = make_folder(user_id=login["user"]["id"], **attached_entity)

        file, *_ = make_files(user_id=login["user"]["id"], folder_id=folder["id"])
        make_files(
            user_id=login["user"]["id"],
            folder_id=folder["id"],
            deleted=True,
        )

        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderFileView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert {file["id"] for file in response.json} == {file["id"]}
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to access this folder"


class TestFolderSubfolderView:
    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "unit_id", None, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", DMS_PERMISSION.READ, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "unit_id", DMS_PERMISSION.READ, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "unit_id", DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "unit_id", None, HTTPStatus.FORBIDDEN),
        ],
    )
    def test_get_subfolders(
        self,
        client,
        client_db,
        site,
        unit,
        make_folder,
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
        main_folder = make_folder(user_id=login["user"]["id"], **attached_entity)
        subfolder1, subfolder2 = (
            make_folder(
                user_id=login["user"]["id"],
                parent_folder_id=main_folder["id"],
                **attached_entity,
            ),
            make_folder(
                user_id=login["user"]["id"],
                parent_folder_id=main_folder["id"],
                **attached_entity,
            ),
        )

        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderSubfolderView,
                folder_id=main_folder["id"],
            ),
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert len(response.json) == 2
            assert {folder["id"] for folder in response.json} == {
                subfolder1["id"],
                subfolder2["id"],
            }
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to access this folder"


class TestFolderTrashView:
    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "unit_id", None, HTTPStatus.OK),
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
            (
                USER_ROLE.DMS_LIMITED,
                "unit_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (USER_ROLE.DMS_LIMITED, "unit_id", DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", None, HTTPStatus.FORBIDDEN),
            (USER_ROLE.DMS_LIMITED, "unit_id", None, HTTPStatus.FORBIDDEN),
        ],
    )
    def test_move_folder_to_trash(
        self,
        client,
        client_db,
        site,
        unit,
        make_folder,
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
        folder = make_folder(user_id=login["user"]["id"], **attached_entity)
        subfolder = make_folder(
            user_id=login["user"]["id"],
            name="Subfolder",
            parent_folder_id=folder["id"],
            **attached_entity,
        )
        make_files(
            user_id=login["user"]["id"],
            folder_id=subfolder["id"],
            n=3,
            **attached_entity,
        )
        make_files(
            user_id=login["user"]["id"], folder_id=folder["id"], n=1, **attached_entity
        )

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderTrashView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert response.json["id"] == folder["id"]
            assert all(
                [file["deleted"] for file in FileDBHandler.find(folder_id=folder["id"])]
            )
            assert FolderDBHandler.get_by(id=folder["id"])["deleted"]
            assert FolderDBHandler.get_by(id=subfolder["id"])["deleted"]
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this folder"


class TestFolderRestoreView:
    @pytest.mark.parametrize(
        "user_role,entity_type, permission_type,expected_response",
        [
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "client_id", None, HTTPStatus.OK),
            (USER_ROLE.ARCHILYSE_ONE_ADMIN, "floor_id", None, HTTPStatus.OK),
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
            (
                USER_ROLE.DMS_LIMITED,
                "floor_id",
                DMS_PERMISSION.READ,
                HTTPStatus.FORBIDDEN,
            ),
            (USER_ROLE.DMS_LIMITED, "floor_id", DMS_PERMISSION.WRITE, HTTPStatus.OK),
            (USER_ROLE.DMS_LIMITED, "client_id", None, HTTPStatus.FORBIDDEN),
            (USER_ROLE.DMS_LIMITED, "floor_id", None, HTTPStatus.FORBIDDEN),
        ],
    )
    def test_restore_trashed_folder(
        self,
        client,
        client_db,
        site,
        floor,
        login,
        make_folder,
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
            else {entity_type: floor["id"]}
        )
        folder = make_folder(
            user_id=login["user"]["id"], **attached_entity, deleted=True
        )
        make_files(
            user_id=login["user"]["id"],
            folder_id=folder["id"],
            n=3,
            deleted=True,
            **attached_entity,
        )

        response = client.put(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderRestoreView,
                folder_id=folder["id"],
            ),
        )

        assert response.status_code == expected_response
        if expected_response == HTTPStatus.OK:
            assert all(
                [
                    not file["deleted"]
                    for file in FileDBHandler.find(folder_id=folder["id"])
                ]
            )
            assert not FolderDBHandler.get_by(id=folder["id"])["deleted"]
        elif expected_response == HTTPStatus.FORBIDDEN:
            assert response.json["msg"] == "User is not allowed to edit this folder"


class TestFolderTrashViewCollection:
    @login_as([USER_ROLE.ARCHILYSE_ONE_ADMIN.name])
    def test_get_deleted_folders(self, client, client_db, building, login, make_folder):
        make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            building_id=building["id"],
        )
        deleted_folder = make_folder(
            user_id=login["user"]["id"],
            client_id=client_db["id"],
            building_id=building["id"],
            deleted=True,
        )

        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderTrashViewCollection,
                client_id=client_db["id"],
            ),
        )

        assert response.status_code == HTTPStatus.OK
        assert {folder["id"] for folder in response.json} == {deleted_folder["id"]}

    @login_as([USER_ROLE.DMS_LIMITED.name])
    def test_get_deleted_folders_dms_limited(
        self, client, client_db, site, building, login, make_sites, make_folder
    ):
        def create_folders_to_display():
            deleted_folder = make_folder(
                user_id=login["user"]["id"],
                client_id=client_db["id"],
                building_id=building["id"],
                deleted=True,
            )
            deleted_folder2 = make_folder(
                user_id=login["user"]["id"],
                client_id=client_db["id"],
                deleted=True,
            )
            return deleted_folder, deleted_folder2

        def create_folders_not_to_display():
            (another_site,) = make_sites(*(client_db,))
            make_folder(
                user_id=login["user"]["id"],
                site_id=another_site["id"],
                deleted=True,
            )
            make_folder(
                user_id=login["user"]["id"],
                client_id=client_db["id"],
                building_id=building["id"],
            )

        folder1, folder2 = create_folders_to_display()
        create_folders_not_to_display()
        DmsPermissionDBHandler.add(
            site_id=site["id"],
            user_id=login["user"]["id"],
            rights=DMS_PERMISSION.READ.name,
        )

        response = client.get(
            get_address_for(
                blueprint=folder_app,
                use_external_address=False,
                view_function=FolderTrashViewCollection,
                client_id=client_db["id"],
            ),
        )
        assert len(FolderDBHandler.find()) == 4
        assert response.status_code == HTTPStatus.OK
        assert {folder["id"] for folder in response.json} == {
            folder1["id"],
            folder2["id"],
        }
