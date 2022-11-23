from http import HTTPStatus
from typing import Dict

import requests
from shapely.geometry import Polygon
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from common_utils.exceptions import OverpassAPIException
from common_utils.logger import logger


class OverpassAPIHandler:

    _OVERPASS_API_BASE_URL = "https://overpass-api.de/api/interpreter?data="

    @classmethod
    def query_builder(cls, bounding_box: Polygon, way: str, relation: str):
        """Helper to build queries http://overpass-turbo.eu/"""
        xmin, ymin, xmax, ymax = bounding_box.bounds
        return (
            f"[out:json][timeout:30];("
            f"{way}({ymin},{xmin},{ymax},{xmax});"
            f"{relation}({ymin},{xmin},{ymax},{xmax});"
            f");"
            f"out;>;out qt;"
        )

    @classmethod
    def url_with_parameters(cls, bounding_box: Polygon, way: str, relation: str):
        """Helper to build queries http://overpass-turbo.eu/"""
        return (
            f"{cls._OVERPASS_API_BASE_URL}"
            f"{cls.query_builder(bounding_box=bounding_box, way=way, relation=relation)}"
        )

    @classmethod
    @retry(
        retry=retry_if_exception_type(ConnectionError),
        wait=wait_random_exponential(multiplier=10, max=60),
        stop=stop_after_attempt(5),
        reraise=True,
    )
    def get_entity_metadata(cls, url: str):
        """Bounding box is assumed to be already in lat lon coordinate system"""
        referer = "Archilyse Switzerland"
        response = requests.get(url, headers={"referer": referer})

        if response.status_code in {  # To be retried
            HTTPStatus.GATEWAY_TIMEOUT,
            HTTPStatus.TOO_MANY_REQUESTS,
        }:
            raise ConnectionError(
                response.status_code, response.text, {"headers": response.headers}
            )
        elif response.status_code == HTTPStatus.OK:
            return response.json()

        msg = (
            f"Could not get metadata from Overpass API, "
            f"service responded with status {response.status_code} {response.text} for url = {url}"
        )
        logger.warning(msg)
        raise OverpassAPIException(msg)

    @classmethod
    def building_full_url(cls, bounding_box: Polygon):
        return cls.url_with_parameters(
            bounding_box=bounding_box,
            way='way["building"]',
            relation='relation["building"]["type"="multipolygon"]',
        )

    @classmethod
    def get_building_metadata(cls, bounding_box: Polygon) -> Dict:
        url = cls.building_full_url(bounding_box=bounding_box)
        response = cls.get_entity_metadata(url=url)
        if not response["elements"]:
            raise OverpassAPIException(f"No buildings found with query {url}")
        return {b["id"]: b for b in response["elements"]}
