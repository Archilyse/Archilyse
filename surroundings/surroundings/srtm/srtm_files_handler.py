from enum import Enum
from math import floor
from pathlib import Path
from typing import Iterator, Tuple

from shapely.geometry import box

from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_SRTM,
    SRTM_DIR,
    SRTM_FILENAME_PATTERN,
)
from common_utils.exceptions import GCSLinkEmptyException
from handlers import GCloudStorageHandler
from surroundings.opentopo_handler import OpenTopoHandler


class Direction(Enum):
    EAST = "e"
    WEST = "w"
    NORTH = "n"
    SOUTH = "s"


class SrtmFilesHandler:
    @staticmethod
    def _get_direction_prefix(coord: float, direction: Direction) -> str:
        if coord < 0:
            # Invert directions
            return (
                Direction.WEST.value
                if direction == Direction.EAST
                else Direction.SOUTH.value
            )

        return direction.value

    @classmethod
    def _get_direction_range_padded(
        cls, min_coord: float, max_coord: float, direction: Direction
    ) -> str:
        pad_length = 3 if direction == Direction.EAST else 2

        for coord in range(floor(min_coord), floor(max_coord) + 1):
            yield f"{cls._get_direction_prefix(coord, direction)}{str(abs(coord)).zfill(pad_length)}", coord

    @classmethod
    def get_srtm_filenames(
        cls, bounding_box: box
    ) -> Iterator[Tuple[Path, Path, Tuple[int, int]]]:
        minx, miny, maxx, maxy = bounding_box.bounds
        for north, raw_n in cls._get_direction_range_padded(
            miny, maxy, Direction.NORTH
        ):
            for east, raw_e in cls._get_direction_range_padded(
                minx, maxx, Direction.EAST
            ):
                filename = SRTM_FILENAME_PATTERN.format(north, east)
                yield SRTM_DIR.joinpath(filename), GOOGLE_CLOUD_SRTM.joinpath(
                    filename
                ), (raw_n, raw_e)

    @classmethod
    def get_srtm_files(cls, bounding_box: box) -> list[Path]:
        local_filenames = []
        for local_filename, remote_filename, coords in cls.get_srtm_filenames(
            bounding_box=bounding_box
        ):
            if not local_filename.parent.exists():
                local_filename.parent.mkdir(parents=True, exist_ok=True)

            cls.download_upload_srtm_tile(
                *coords, local_filename=local_filename, remote_filename=remote_filename
            )
            local_filenames.append(local_filename)
        return local_filenames

    @classmethod
    def download_upload_srtm_tile(
        cls, north: int, east: int, local_filename: Path, remote_filename: Path
    ):
        gcloud = GCloudStorageHandler()
        try:
            gcloud.download_file(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                remote_file_path=remote_filename,
                local_file_name=local_filename,
            )
        except GCSLinkEmptyException:
            data = OpenTopoHandler.get_srtm_tile(bb_min_north=north, bb_min_east=east)

            with local_filename.open("wb") as f:
                f.write(data)

            gcloud.upload_file_to_bucket(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                destination_folder=GOOGLE_CLOUD_SRTM,
                destination_file_name=remote_filename.name,
                local_file_path=local_filename,
                delete_local_after_upload=False,
            )
