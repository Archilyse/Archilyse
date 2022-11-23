from pathlib import Path
from typing import Iterator

from common_utils.constants import (
    EU_NOISE_DIR,
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_EU_NOISE,
    NOISE_SOURCE_TYPE,
    NOISE_TIME_TYPE,
    REGION,
)
from handlers import GCloudStorageHandler
from surroundings.eu_noise.constants import DATASET_CONTENT_TYPE, DATASET_FILENAMES


def download_files_if_not_exists(
    region: REGION,
    content_type: DATASET_CONTENT_TYPE,
    noise_source_type: NOISE_SOURCE_TYPE,
    noise_time: NOISE_TIME_TYPE = None,
) -> Iterator[Path]:
    files = DATASET_FILENAMES[content_type][region][noise_source_type]
    if content_type == DATASET_CONTENT_TYPE.NOISE_LEVELS:
        files = files[noise_time]

    for filename in files:
        for shp_file_extension in ["dbf", "prj", "sbn", "sbx", "shp", "shx"]:
            local_file_name = EU_NOISE_DIR.joinpath(filename.format(shp_file_extension))
            remote_file_path = GOOGLE_CLOUD_EU_NOISE.joinpath(
                filename.format(shp_file_extension)
            )
            GCloudStorageHandler().download_file(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                remote_file_path=remote_file_path,
                local_file_name=local_file_name,
            )
        yield EU_NOISE_DIR.joinpath(filename.format("shp"))
