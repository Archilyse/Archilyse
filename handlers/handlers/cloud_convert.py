from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

import cloudconvert

from common_utils.exceptions import (
    CloudConvertConvertException,
    CloudConvertException,
    CloudConvertExportException,
    CloudConvertUploadException,
)
from handlers.constants import CLOUD_CONVERT_API_KEY, CLOUD_CONVERT_IS_SANDBOX
from handlers.gcloud_storage import GCloudStorageHandler


class CloudConvertHandler:
    @staticmethod
    def cloudconvert_initialized():
        cloudconvert.configure(
            api_key=CLOUD_CONVERT_API_KEY, sandbox=CLOUD_CONVERT_IS_SANDBOX
        )

    def __init__(self):
        self.upload_task_id: Optional[str] = None
        self.convert_task_id: Optional[str] = None

    # --------- Convenience Methods --------- #

    def transform(
        self,
        source_file_path: Path,
        destination_file_path: Path,
        input_format: str,
        output_format: str,
        **kwargs,
    ):
        self.cloudconvert_initialized()
        self.import_from_file(source_file_path=source_file_path)
        self.convert(input_format=input_format, output_format=output_format, **kwargs)
        self.export_to_file(destination_file_path=destination_file_path)

    def transform_bytes(
        self, source_content: bytes, input_format: str, output_format: str, **kwargs
    ) -> bytes:
        with NamedTemporaryFile("wb", suffix=f".{input_format}") as source_temp_file:
            source_temp_file.write(source_content)

            with NamedTemporaryFile() as output_temp_file:
                self.transform(
                    source_file_path=Path(source_temp_file.name),
                    destination_file_path=Path(output_temp_file.name),
                    input_format=input_format,
                    output_format=output_format,
                    **kwargs,
                )

                output_temp_file.seek(0)
                return output_temp_file.read()

    def transform_gcloud_file(
        self,
        source_bucket: str,
        source_medialink: str,
        destination_bucket: str,
        destination_folder: Path,
        destination_filename: str,
        input_format: str,
        output_format: str,
        **kwargs,
    ) -> bytes:
        output_data = self.transform_bytes(
            source_content=GCloudStorageHandler().download_bytes_from_media_link(
                bucket_name=source_bucket, source_media_link=source_medialink
            ),
            input_format=input_format,
            output_format=output_format,
            **kwargs,
        )

        GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=destination_bucket,
            destination_folder=destination_folder,
            destination_file_name=destination_filename,
            contents=output_data,
        )

        return output_data

    # --------- File Import --------- #

    def import_from_file(self, source_file_path: Path):
        upload_task = cloudconvert.Task.create(operation="import/upload")
        if "message" in upload_task and upload_task["message"] == "Unauthenticated.":
            raise CloudConvertException(
                "Authentication not established: Are you maybe using the wrong api key and / or the sandbox?"
            )

        if cloudconvert.Task.upload(
            file_name=source_file_path.as_posix(), task=upload_task
        ):
            self.upload_task_id = upload_task["id"]
        else:
            raise CloudConvertUploadException(
                f"CloudConvert upload failed for {source_file_path}"
            )

    # --------- File Conversion --------- #

    def convert(self, input_format: str, output_format: str, **kwargs):
        convert_task = cloudconvert.Task.create(
            operation="convert",
            payload={
                "input": self.upload_task_id,
                "input_format": input_format,
                "output_format": output_format,
                **kwargs,
            },
        )

        convert_task = cloudconvert.Task.wait(id=convert_task["id"])
        if convert_task["status"] == "failed":
            raise CloudConvertConvertException(
                f"Failed to convert {input_format} to {output_format}"
            )
        self.convert_task_id = convert_task["id"]

        return convert_task

    # --------- File Export --------- #

    def export_to_file(self, destination_file_path: Path):
        export_task = cloudconvert.Task.create(
            operation="export/url",
            payload={
                "input": self.convert_task_id,
            },
        )

        result = cloudconvert.Task.wait(id=export_task["id"])
        if result["status"] == "failed":
            raise CloudConvertExportException("Could not export from CloudConvert")

        result_file = result["result"]["files"][0]
        if cloudconvert.download(
            filename=destination_file_path.as_posix(), url=result_file["url"]
        ):
            return

        raise CloudConvertExportException(
            f"CloudConvert download failed to download {result_file['url']}"
        )
