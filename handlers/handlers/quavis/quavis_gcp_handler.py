import gzip
import json
from pathlib import Path

import msgpack
from google.cloud.exceptions import NotFound
from msgpack import ExtraData

from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_QUAVIS,
    QUAVIS_INPUT_FILENAME_TEMPLATE,
    QUAVIS_OUTPUT_FILENAME_TEMPLATE,
)
from common_utils.logger import logger
from handlers.gcloud_storage import GCloudStorageHandler


class QuavisGCPHandler:
    @classmethod
    def upload_quavis_input(cls, run_id: str | int, quavis_input: dict):
        logger.info(f"Uploading quavis input for run_id={run_id}")
        quavis_input_path = QUAVIS_INPUT_FILENAME_TEMPLATE.format(run_id=run_id)
        cls._upload_quavis_file(filename=quavis_input_path, data=quavis_input)

    @classmethod
    def get_quavis_input(cls, run_id: str | int) -> dict:
        quavis_input_path = GOOGLE_CLOUD_QUAVIS.joinpath(
            QUAVIS_INPUT_FILENAME_TEMPLATE.format(run_id=run_id)
        )
        return cls._download_quavis_file(filename=quavis_input_path)

    @classmethod
    def upload_quavis_output(cls, run_id: str | int, quavis_output: dict):
        logger.info(f"Uploading quavis output for run_id={run_id}")
        quavis_output_path = QUAVIS_OUTPUT_FILENAME_TEMPLATE.format(run_id=run_id)
        cls._upload_quavis_file(filename=quavis_output_path, data=quavis_output)

    @classmethod
    def get_quavis_output(cls, run_id: str | int) -> dict:
        quavis_output_path = GOOGLE_CLOUD_QUAVIS.joinpath(
            QUAVIS_OUTPUT_FILENAME_TEMPLATE.format(run_id=run_id)
        )
        return cls._download_quavis_file(filename=quavis_output_path)

    @classmethod
    def delete_simulation_artifacts(cls, run_id: str | int):
        logger.debug(f"Deleting quavis input/output from GCS for run_id={run_id}")
        quavis_output_path = Path(QUAVIS_OUTPUT_FILENAME_TEMPLATE.format(run_id=run_id))
        quavis_input_path = Path(QUAVIS_INPUT_FILENAME_TEMPLATE.format(run_id=run_id))
        for filename in [quavis_output_path, quavis_input_path]:
            try:
                cls._delete_quavis_file(filename=filename)
            except NotFound:
                try:
                    # Old uncompressed json format
                    filename = filename.with_suffix(".json")
                    cls._delete_quavis_file(filename=filename)
                except NotFound:
                    logger.error(
                        f"Could not delete file {filename} from bucket {GOOGLE_CLOUD_QUAVIS} because it was not found."
                    )

    @classmethod
    def _upload_quavis_file(cls, filename: str, data: dict):
        GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_folder=GOOGLE_CLOUD_QUAVIS,
            destination_file_name=filename,
            contents=gzip.compress(msgpack.dumps(data)),
        )

    @classmethod
    def _download_quavis_file(cls, filename: Path) -> dict:
        try:
            quavis_file_string = GCloudStorageHandler().download_file_as_bytes(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                source_file_name=filename,
            )
            data_uncompressed = gzip.decompress(quavis_file_string)
            try:
                # To be removed when all the simulations are using the new format
                return msgpack.loads(data_uncompressed)
            except ExtraData:
                return json.loads(data_uncompressed)
        except NotFound:
            return cls._download_old_format(filename=filename)

    @staticmethod
    def _download_old_format(filename: Path) -> dict:
        """Old uncompressed json format"""
        # To be removed when all the simulations are using the new format
        filename = filename.with_suffix(".json")
        quavis_input_string = GCloudStorageHandler().download_file_as_bytes(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            source_file_name=filename,
        )
        return json.loads(quavis_input_string)

    @staticmethod
    def _delete_quavis_file(filename):
        GCloudStorageHandler().delete_resource(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            source_folder=GOOGLE_CLOUD_QUAVIS,
            filename=filename,
        )
        logger.debug(
            f"Successfully deleted {GOOGLE_CLOUD_QUAVIS.joinpath(filename)} from {GOOGLE_CLOUD_BUCKET}."
        )
