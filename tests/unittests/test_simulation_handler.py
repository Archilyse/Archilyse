import gzip
from pathlib import Path
from unittest.mock import call

import msgpack
import pytest
from google.cloud.exceptions import NotFound

from common_utils.constants import GOOGLE_CLOUD_BUCKET


@pytest.mark.parametrize(
    "run_id,not_found",
    [("run_id", None), ("run_id", [NotFound("msg") for _ in range(4)])],
)
def test_delete_simulation_artifacts(run_id, not_found, mocked_gcp_delete):
    from handlers.quavis import QuavisGCPHandler

    mocked_gcp_delete.side_effect = not_found

    expected_calls = [
        call(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            source_folder=Path("quavis"),
            filename=Path(f"{run_id}-out.zip"),
        ),
        call(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            source_folder=Path("quavis"),
            filename=Path(f"{run_id}-in.zip"),
        ),
    ]
    if not_found:
        expected_calls.extend(
            [
                call(
                    bucket_name=GOOGLE_CLOUD_BUCKET,
                    source_folder=Path("quavis"),
                    filename=Path(f"{run_id}-out.json"),
                ),
                call(
                    bucket_name=GOOGLE_CLOUD_BUCKET,
                    source_folder=Path("quavis"),
                    filename=Path(f"{run_id}-in.json"),
                ),
            ]
        )
        # Switch order of arguments
        expected_calls[1:3] = expected_calls[1:3][::-1]

    QuavisGCPHandler.delete_simulation_artifacts(run_id=run_id)
    assert mocked_gcp_delete.mock_calls == expected_calls


def test_download_quavis_file_reads_msgpack(
    mocked_gcp_download_file_as_bytes,
):
    from handlers.quavis import QuavisGCPHandler

    orig_dict = {"salpica": 3.1416}
    mocked_gcp_download_file_as_bytes.return_value = gzip.compress(
        msgpack.dumps(orig_dict)
    )
    result = QuavisGCPHandler._download_quavis_file(Path("salpica.zip"))
    assert result == orig_dict


def test_download_quavis_file_calls_old_method_if_not_found(
    mocked_gcp_download_file_as_bytes,
):
    from handlers.quavis import QuavisGCPHandler

    mocked_gcp_download_file_as_bytes.side_effect = [NotFound("msg"), NotFound("msg")]
    expected_calls = [
        call(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            filename=Path("salpica.zip"),
        ),
        call(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            filename=Path("salpica.json"),
        ),
    ]
    with pytest.raises(NotFound):
        QuavisGCPHandler._download_quavis_file(Path("salpica.zip"))
        assert mocked_gcp_download_file_as_bytes.mock_calls == expected_calls
