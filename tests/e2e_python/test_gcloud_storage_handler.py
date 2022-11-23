from pathlib import Path

from google.cloud.storage import blob

from common_utils.constants import GOOGLE_CLOUD_BUCKET
from handlers.gcloud_storage import GCloudStorageHandler, get_md5_hash_from_path


def test_download_creates_folder_if_not_existing(
    mocker, recreate_test_gcp_bucket, tmp_path, annotations_path: Path
):
    sample_file = "background_image_full_plan.json"
    destination_bucket_folder = Path("salpica")
    initial_md5_hash = get_md5_hash_from_path(
        file_path=annotations_path.joinpath(sample_file)
    )

    gclient = GCloudStorageHandler()

    gclient.upload_file_to_bucket(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        destination_folder=destination_bucket_folder,
        local_file_path=annotations_path.joinpath(sample_file),
    )

    destination_file = tmp_path.joinpath("salpica/carota/dumy_file")
    gclient.download_file(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        remote_file_path=destination_bucket_folder.joinpath(sample_file),
        local_file_name=destination_file,
    )
    assert destination_file.exists()
    with open(f"{destination_file.as_posix()}.checksum", "r") as f:
        assert f.read() == initial_md5_hash

    mocked_blob = mocker.patch.object(blob.Blob, "download_to_filename")

    gclient.download_file(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        remote_file_path=destination_bucket_folder.joinpath(sample_file),
        local_file_name=destination_file,
    )
    assert destination_file.exists()
    mocked_blob.assert_not_called()
