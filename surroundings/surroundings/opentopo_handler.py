import os
from http import HTTPStatus

import requests
from requests import RequestException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from common_utils.exceptions import OpenTopoException
from common_utils.logger import logger


class OpenTopoHandler:
    base_url = "https://portal.opentopography.org/API/"
    demtype = "SRTMGL1"
    tile_margin = 0.0001
    api_key = os.environ["OPEN_TOPO_API_KEY"]

    @classmethod
    def _get_globaldem_url(
        cls,
        bb_min_north: float,
        bb_max_north: float,
        bb_min_east: float,
        bb_max_east: float,
    ) -> str:
        globaldem = (
            f"globaldem?demtype={cls.demtype}"
            f"&south={bb_min_north}&north={bb_max_north}&west={bb_min_east}&east={bb_max_east}"
            f"&outputFormat=GTiff&API_Key={cls.api_key}"
        )
        return cls.base_url + globaldem

    @classmethod
    @retry(
        retry=retry_if_exception_type(RequestException),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=3, max=20),
        reraise=True,
    )
    def get_srtm_tile(cls, bb_min_north: int, bb_min_east: int):
        logger.info(f"Getting tile {bb_min_north},{bb_min_east} from OpenTopo")
        response = requests.get(
            cls._get_globaldem_url(
                bb_min_north=bb_min_north - cls.tile_margin,
                bb_max_north=bb_min_north + 1 + cls.tile_margin,
                bb_min_east=bb_min_east - cls.tile_margin,
                bb_max_east=bb_min_east + 1 + cls.tile_margin,
            )
        )
        if response.status_code == HTTPStatus.OK:
            return response.content
        else:
            raise OpenTopoException(
                f"OpenTopo failed to retrieve tile {bb_min_north}-{bb_min_east}. "
                f"HTTP code {response.status_code}; Message {response.content}"
            )
