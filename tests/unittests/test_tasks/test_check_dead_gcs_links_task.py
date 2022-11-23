from common_utils.exceptions import GCSLinkEmptyException
from handlers import GCloudStorageHandler
from tasks.check_gcs_links_task import (
    check_dead_gcs_links_task,
    get_gcs_columns_from_handler,
)


def test_check_dead_gcs_links_task(mocker):
    from handlers.db import (
        BuildingDBHandler,
        ClientDBHandler,
        FloorDBHandler,
        PlanDBHandler,
        SiteDBHandler,
        UnitDBHandler,
    )

    def mocked_get_by(id, output_columns):
        return {
            column: id if column == "id" else f"{column}_link"
            for column in output_columns
        }

    mocker.patch.object(ClientDBHandler, "find", return_value=[{"id": 1}])
    mocker.patch.object(SiteDBHandler, "find", return_value=[{"id": 2}])
    mocker.patch.object(BuildingDBHandler, "find", return_value=[{"id": 3}])
    mocker.patch.object(PlanDBHandler, "find", return_value=[{"id": 4}])
    mocker.patch.object(FloorDBHandler, "find", return_value=[{"id": 5}])
    mocker.patch.object(UnitDBHandler, "find", return_value=[{"id": 6}])

    mocker.patch.object(SiteDBHandler, "get_by", mocked_get_by)
    mocker.patch.object(BuildingDBHandler, "get_by", mocked_get_by)
    mocker.patch.object(PlanDBHandler, "get_by", mocked_get_by)
    mocker.patch.object(FloorDBHandler, "get_by", mocked_get_by)
    mocker.patch.object(UnitDBHandler, "get_by", mocked_get_by)

    num_gcs_columns = sum(
        len(get_gcs_columns_from_handler(handler=handler))
        for handler in (
            SiteDBHandler,
            BuildingDBHandler,
            PlanDBHandler,
            FloorDBHandler,
            UnitDBHandler,
        )
    )
    assert num_gcs_columns >= 25

    def mocked_get_blob_check_exists(self, bucket_name, file_path):
        if "pdf" in file_path:
            raise GCSLinkEmptyException()

    mocker.patch.object(
        GCloudStorageHandler, "get_blob_check_exists", mocked_get_blob_check_exists
    )

    def mocked__convert_media_link_to_file_in_gcp(self, media_link: str):
        return media_link

    mocker.patch.object(
        GCloudStorageHandler,
        "_convert_media_link_to_file_in_gcp",
        mocked__convert_media_link_to_file_in_gcp,
    )

    summary = check_dead_gcs_links_task()
    # All the last calls to the gcloud handler are exceptions, which correspond to Floor and Units calls
    assert summary == {
        "FloorDBHandler": {
            "gcs_de_pdf_link": [5],
            "gcs_en_pdf_link": [5],
            "gcs_fr_pdf_link": [5],
            "gcs_it_pdf_link": [5],
        },
        "UnitDBHandler": {
            "gcs_de_pdf_link": [6],
            "gcs_en_pdf_link": [6],
            "gcs_it_pdf_link": [6],
            "gcs_fr_pdf_link": [6],
        },
    }
