import imghdr
import os

import requests
from flask import Response
from marshmallow import Schema, fields


class LayoutPredictorClient:
    MAX_FILE_SIZE = int(os.getenv("LAYOUT_PREDICT_MAX_FILE_SIZE", 9048576))

    def __init__(self):
        self.predict_service_url = f'{os.getenv("LAYOUT_PREDICT_SERVICE_URL")}/api'
        self.upload_url_schema = UploadUrlSchema()
        self.icon_task_response_schema = IconTaskResponseSchema()

    def request_prediction(
        self,
        image_bytes: bytes,
        username: str,
        pixels_per_meter: float,
        rois: list = None,
    ) -> dict:
        image_type = imghdr.what(None, image_bytes)
        if image_type is None:
            raise ValueError("Cannot determine image type")
        image_type = f"image/{image_type}"

        response = requests.get(
            f"{self.predict_service_url}/images/upload-url?content_type={image_type}",
            headers={"username": username},
        )
        response.raise_for_status()

        image_data = self.upload_url_schema.load(
            response.json()
        )  # raises ValidationError

        response = requests.put(
            image_data["url"],
            data=image_bytes,
            headers={
                "x-goog-content-length-range": f"0,{self.MAX_FILE_SIZE}",
                "Content-Type": image_type,
            },
        )
        response.raise_for_status()

        params = (
            f"image_name={image_data['image_name']}&pixels_per_meter={pixels_per_meter}"
        )
        for roi in rois or []:
            params += f"&minx={roi[0]}&miny={roi[1]}&maxx={roi[2]}&maxy={roi[3]}"

        response = requests.post(
            f"{self.predict_service_url}/request-prediction/icons?{params}",
        )
        response.raise_for_status()
        sim_task_data = self.icon_task_response_schema.load(
            response.json()
        )  # raises ValidationError
        return sim_task_data

    def get_prediction_by_task_id(self, task_id: str) -> Response:
        response = requests.get(
            f"{self.predict_service_url}/retrieve-results/{task_id}.json"
        )
        return response


class UploadUrlSchema(Schema):
    url = fields.Url(
        required=True, error_messages={"required": "Failed to retrieve the upload URL"}
    )
    image_name = fields.Str(
        required=True, error_messages={"required": "Failed to retrieve the image name"}
    )


class IconTaskSchema(Schema):
    id = fields.Str(
        required=True, error_messages={"required": "Failed to retrieve the task ID"}
    )


class IconTaskResponseSchema(Schema):
    icon_task = fields.Nested(IconTaskSchema(), required=True)
