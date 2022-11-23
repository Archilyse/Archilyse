import urllib
from glob import glob
from pathlib import Path

from celery.states import SUCCESS

from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_SWISSTOPO,
    SWISSTOPO_BUILDING_FILES_PREFIX,
)
from handlers import SiteHandler
from handlers.db import SiteDBHandler
from handlers.gcloud_storage import GCloudStorageHandler
from tasks.surroundings_tasks import generate_geo_referencing_surroundings_for_site_task
from tests.celery_utils import (
    get_celery_metadata_from_flower_api,
    trigger_task_and_wait_for_backend,
)


def test_building_surrounding_task(
    site, fixtures_swisstopo_path, recreate_test_gcp_bucket
):
    """
    Given an existing Site in the DB
    And there is a test bucket in GCP with buildings surroundings for the previous site location
    When the task to generate the building surroundings is triggered
    Then the results are available in flower
    And the task has finished with a DB exception when reading the site info
    """

    site = SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={
            "lon": 7.743521927962778,
            "lat": 46.88832402553733,
        },
    )
    for file_name in glob(
        pathname=fixtures_swisstopo_path.joinpath(
            "buildings/SWISSBUILDINGS3D_2_0_CHLV95LN02_1188-11"
        ).as_posix()
        + "*"
    ):
        GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_folder=GOOGLE_CLOUD_SWISSTOPO.joinpath(
                SWISSTOPO_BUILDING_FILES_PREFIX
            ),
            local_file_path=Path(file_name),
        )
    task_id = trigger_task_and_wait_for_backend(
        generate_geo_referencing_surroundings_for_site_task, site_id=site["id"]
    )
    task_metadata = get_celery_metadata_from_flower_api(task_id=task_id)
    assert task_metadata["state"] == SUCCESS, task_metadata["exception"]

    new_site_info = SiteDBHandler.get_by(id=site["id"])
    created_file_name = Path(
        urllib.parse.unquote(new_site_info["gcs_buildings_link"])
    ).name
    lv95_location = SiteHandler.get_projected_location(site_id=site["id"])
    building_surroundings_file = SiteHandler.get_building_json_surroundings_path(
        lv95_location
    )
    assert created_file_name.startswith(building_surroundings_file.name)
