import io
import os

import pytest
from werkzeug.datastructures import FileStorage

from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES
from handlers import FileHandler, FloorHandler, UnitHandler
from handlers.db import FolderDBHandler, UnitDBHandler
from tests.e2e_utils import SlamUIClient

from .constants import USERS
from .utils import create_user_context


@pytest.fixture
def georeference_url_default_plan(plan):
    return SlamUIClient._georeference_url_plan(plan_id=plan["id"])


@pytest.fixture
def classification_url_default_plan(plan):
    return SlamUIClient._classification_url_plan(plan_id=plan["id"])


@pytest.fixture
def linking_url_default_plan(first_pipeline_complete_db_models, plan):
    return SlamUIClient._linking_url_plan(plan_id=plan["id"])


@pytest.fixture
def splitting_url_default_plan(plan_box_pipelined, plan):
    return SlamUIClient._splitting_url_plan(plan_id=plan["id"])


@pytest.fixture
def scaling_url_default_plan(plan_box_pipelined, plan):
    return SlamUIClient._scaling_url_plan(plan_id=plan["id"])


@pytest.fixture
def quality_url():
    def _quality_url(site_id):
        return SlamUIClient.quality_url(site_id=site_id)

    return _quality_url


@pytest.fixture
def heatmaps_url(login, site):
    return SlamUIClient.heatmaps_url(site_id=site["id"])


@pytest.fixture
def dms_file(
    client_db,
    site_with_full_slam_results_success,
    building,
    valid_image,
    recreate_test_gcp_client_bucket,
):

    context = create_user_context(USERS["ADMIN"])
    file_name = os.path.basename(valid_image)
    with valid_image.open("rb") as f:
        file = FileStorage(
            stream=io.BytesIO(f.read()),
            filename=file_name,
            content_type="image/jpeg",
        )

    return FileHandler.create(
        user_id=context["user"]["id"],
        file_obj=file,
        filename=file_name,
        labels=[],
        client_id=client_db["id"],
        site_id=site_with_full_slam_results_success["id"],
    )


@pytest.fixture
def dms_folder(client_db, site, valid_image, recreate_test_gcp_client_bucket):
    context = create_user_context(USERS["ARCHILYSE_ONE_ADMIN"])

    return FolderDBHandler.add(
        creator_id=context["user"]["id"],
        client_id=context["user"]["client_id"],
        name="test-parent-folder",
        site_id=site["id"],
    )


@pytest.fixture
def dms_subfolder(client_db, dms_folder, valid_image, recreate_test_gcp_client_bucket):
    context = create_user_context(USERS["ARCHILYSE_ONE_ADMIN"])

    subfolder = FolderDBHandler.add(
        creator_id=context["user"]["id"],
        client_id=context["user"]["client_id"],
        name="test-subfolder",
        parent_folder_id=dms_folder["id"],
    )

    file_name = os.path.basename(valid_image)
    with valid_image.open("rb") as f:
        file = FileStorage(
            stream=io.BytesIO(f.read()),
            filename=file_name,
            content_type="image/jpeg",
        )

        FileHandler.create(
            user_id=context["user"]["id"],
            file_obj=file,
            client_id=context["user"]["client_id"],
            filename=file_name,
            labels=[],
            folder_id=subfolder["id"],
        )
    return subfolder


@pytest.fixture
def dms_limited_user():
    create_user_context(USERS["DMS_LIMITED"])["user"]
    create_user_context(USERS["DMS_LIMITED_2"])["user"]


@pytest.fixture
def add_site_1439_floorplan_to_floor(fixtures_path, site_1439_simulated):
    def _add_site_1439_floorplan_to_floor(
        floor_id,
    ):
        file_name_languages = [
            ("images/floor_pngs/5797-full_floorplan_EN.png", SUPPORTED_LANGUAGES.EN),
            ("images/floor_pngs/5797-full_floorplan_DE.png", SUPPORTED_LANGUAGES.DE),
        ]
        f_number_by_id = {
            f["id"]: f["floor_number"] for f in site_1439_simulated["floors"]
        }
        for file_name, language in file_name_languages:
            with fixtures_path.joinpath(file_name).open("rb") as f:
                FloorHandler.old_upload_content_to_gcs(
                    site_id=site_1439_simulated["site"]["id"],
                    building_id=site_1439_simulated["building"][0]["id"],
                    floor_id=floor_id,
                    floor_number=f_number_by_id[floor_id],
                    file_format=SUPPORTED_OUTPUT_FILES.PNG,
                    language=language,
                    contents=f.read(),
                )

    return _add_site_1439_floorplan_to_floor


@pytest.fixture
def add_site_1439_floorplan_to_unit(fixtures_path, site_1439_simulated):
    def _add_site_1439_floorplan_to_unit(client_id):
        file_name_languages = [
            ("images/GS20-00-01-floorplan.png", SUPPORTED_LANGUAGES.EN),
            ("images/floor_pngs/3489-floor-axis-DE.png", SUPPORTED_LANGUAGES.DE),
        ]
        for file_name, language in file_name_languages:
            with fixtures_path.joinpath(file_name).open("rb") as f:
                UnitHandler().old_upload_content_to_gcs(
                    unit_id=UnitDBHandler.get_by(client_id=client_id)["id"],
                    file_format=SUPPORTED_OUTPUT_FILES.PNG,
                    language=language,
                    content=f.read(),
                )

    return _add_site_1439_floorplan_to_unit
