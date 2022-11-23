import pytest

from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE, REGION
from surroundings.eu_noise.constants import DATASET_CONTENT_TYPE


@pytest.mark.parametrize(
    "content_type, region, noise_source_type, noise_time, expected_file_count, expected_file_ending",
    [
        (
            DATASET_CONTENT_TYPE.NOISE_LEVELS,
            REGION.DE_HAMBURG,
            NOISE_SOURCE_TYPE.TRAIN,
            NOISE_TIME_TYPE.DAY,
            3,
            "Aggrail_Lden",
        ),
        (
            DATASET_CONTENT_TYPE.NOISE_LEVELS,
            REGION.DE_HAMBURG,
            NOISE_SOURCE_TYPE.TRAFFIC,
            NOISE_TIME_TYPE.NIGHT,
            2,
            "Aggroad_Lnight",
        ),
        (
            DATASET_CONTENT_TYPE.SOURCE_GEOMETRIES,
            REGION.DE_HAMBURG,
            NOISE_SOURCE_TYPE.TRAIN,
            None,
            3,
            "Mrail_Source",
        ),
        (
            DATASET_CONTENT_TYPE.SOURCE_GEOMETRIES,
            REGION.DE_HAMBURG,
            NOISE_SOURCE_TYPE.TRAFFIC,
            None,
            2,
            "Mroad_Source",
        ),
    ],
)
def test_download_files_if_not_exists(
    mocker,
    content_type,
    region,
    noise_source_type,
    noise_time,
    expected_file_count,
    expected_file_ending,
):
    from handlers import GCloudStorageHandler
    from surroundings.eu_noise.utils import download_files_if_not_exists

    mocked_download = mocker.patch.object(
        GCloudStorageHandler, GCloudStorageHandler.download_file.__name__
    )

    filenames = list(
        download_files_if_not_exists(
            noise_source_type=noise_source_type,
            noise_time=noise_time,
            content_type=content_type,
            region=region,
        )
    )

    assert len(filenames) == expected_file_count
    assert mocked_download.call_count == expected_file_count * 6
    assert all(f.name.endswith(f"{expected_file_ending}.shp") for f in filenames)
