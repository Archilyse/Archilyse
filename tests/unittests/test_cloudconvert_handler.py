from pathlib import Path
from zipfile import ZipFile

import pytest

from common_utils.constants import GOOGLE_CLOUD_BUCKET
from common_utils.exceptions import (
    CloudConvertConvertException,
    CloudConvertExportException,
    CloudConvertUploadException,
)
from handlers import CloudConvertHandler, GCloudStorageHandler


@pytest.mark.parametrize(
    "fail_upload, fail_convert, fail_export, expected_error",
    [
        (False, False, False, None),
        (False, False, True, CloudConvertExportException),
        (False, True, False, CloudConvertConvertException),
        (True, False, False, CloudConvertUploadException),
    ],
)
def test_dxf_to_dwg(
    mocker,
    fixtures_path,
    celery_eager,
    requests_mock,
    random_media_link,
    mocked_gcp_upload_bytes_to_bucket,
    monkeypatch,
    fail_upload,
    fail_convert,
    fail_export,
    expected_error,
):
    """Note: This test (beside the binary assertion in the end) also works w/o mocking by deactivating
    the request_mock autouse=True flag. The API KEY provided here is a sandbox-api key which
    only works for the fixture dxf when the requests are not mocked.
    """
    import urllib

    with ZipFile(
        fixtures_path.joinpath("dxf/AL_Sample building_1OG_DXF.dwg.zip")
    ) as zip_file:
        with zip_file.open("AL_Sample building_1OG_DXF.dwg", "r") as fh:
            expected_dwg_file_content = fh.read()

    # Cloud Convert Fake Workflow
    expected_convert_status = "finished" if not fail_convert else "failed"
    expected_export_status = "finished" if not fail_export else "failed"
    expected_upload_status_code = 201 if not fail_upload else 500

    request_mocks = [
        requests_mock.post(
            "https://api.sandbox.cloudconvert.com/v2/import/upload",
            text='{"id": "upload-id", "operation": "import/upload", "result": {"form": {"url": "https://upload.cloudconvert.com/some_upload_target"}}}',
        ),
        requests_mock.request(
            url="https://upload.cloudconvert.com/some_upload_target",
            status_code=expected_upload_status_code,
            method="POST",
        ),
        requests_mock.post(
            "https://api.sandbox.cloudconvert.com/v2/convert",
            text='{"id": "convert-id", "operation": "convert", "status": "processing"}',
        ),
        requests_mock.get(
            "https://api.sandbox.cloudconvert.com/v2/tasks/convert-id/wait",
            text=f'{{"id": "convert-id", "operation": "convert", "status": "{expected_convert_status}"}}',
        ),
        requests_mock.post(
            "https://api.sandbox.cloudconvert.com/v2/export/url",
            text='{"id": "export-id", "operation": "export/url", "status": "processing"}',
        ),
        requests_mock.get(
            "https://api.sandbox.cloudconvert.com/v2/tasks/export-id/wait",
            text=f'{{"id": "export-id", "operation": "export/url", "status": "{expected_export_status}", "result": {{"files": [{{"filename": "test.dwg", "url": "https://result-file.com/is/here"}}]}}}}',
        ),
    ]

    def _fake_download_file(url, filename):
        assert url == "https://result-file.com/is/here"
        with open(filename, "wb") as fh:
            fh.write(expected_dwg_file_content)

    monkeypatch.setattr(urllib.request, "urlretrieve", _fake_download_file)

    # Actual Test
    with ZipFile(
        fixtures_path.joinpath("dxf/AL_Sample building_1OG_DXF.dxf.zip")
    ) as zip_file:
        with zip_file.open("AL_Sample building_1OG_DXF.dxf", "r") as fh:
            gcp_download_mock = mocker.patch.object(
                GCloudStorageHandler,
                "download_bytes_from_media_link",
                return_value=fh.read(),
            )
    args = dict(
        source_bucket=GOOGLE_CLOUD_BUCKET,
        source_medialink=random_media_link,
        destination_bucket=GOOGLE_CLOUD_BUCKET,
        destination_folder=Path("dwg_folder/"),
        destination_filename="test.dwg",
        input_format="dxf",
        output_format="dwg",
    )
    if expected_error:
        with pytest.raises(expected_error):
            CloudConvertHandler().transform_gcloud_file(**args)
    else:
        CloudConvertHandler().transform_gcloud_file(**args)

        for mock in request_mocks:
            assert mock.call_count == 1

        gcp_download_mock.assert_called_once_with(
            bucket_name=GOOGLE_CLOUD_BUCKET, source_media_link=random_media_link
        )

        assert mocked_gcp_upload_bytes_to_bucket.call_count == 1
        assert (
            mocked_gcp_upload_bytes_to_bucket.call_args.kwargs["bucket_name"]
            == GOOGLE_CLOUD_BUCKET
        )
        assert mocked_gcp_upload_bytes_to_bucket.call_args.kwargs[
            "destination_folder"
        ] == Path("dwg_folder")
        assert (
            mocked_gcp_upload_bytes_to_bucket.call_args.kwargs["destination_file_name"]
            == "test.dwg"
        )

        assert (
            mocked_gcp_upload_bytes_to_bucket.call_args.kwargs["contents"]
            == expected_dwg_file_content
        )
