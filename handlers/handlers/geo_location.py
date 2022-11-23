import os
from dataclasses import dataclass
from distutils.util import strtobool

import requests
from geopy import Nominatim
from requests import RequestException
from tenacity import (
    retry,
    retry_if_exception_message,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from unidecode import unidecode

from common_utils.constants import REGION
from common_utils.exceptions import GoogleGeocodeAPIException, InvalidRegion
from common_utils.logger import logger

get_region_from_lat_lon_retry_config = dict(
    retry=(
        retry_if_exception_type(RequestException)
        | retry_if_exception_message("Non-successful status code 502")
        | retry_if_exception_message("Non-successful status code 504")
    ),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=3, max=20),
    reraise=True,
)


@dataclass
class LatLong:
    lat: float
    lon: float


class GeoLocator:

    nominatim = Nominatim(user_agent="Archilyse-app", timeout=10)
    nominatim_reverse_address = "https://nominatim.openstreetmap.org/reverse"
    google_geocode_address = "https://maps.googleapis.com/maps/api/geocode/json"

    @classmethod
    @retry(**get_region_from_lat_lon_retry_config)
    def get_region_from_lat_lon(cls, lat: float, lon: float):
        if strtobool(os.environ.get("TEST_ENVIRONMENT", "False")):
            return REGION.CH

        location = cls.nominatim.reverse([lat, lon])
        if not location:
            raise InvalidRegion(lat, lon)

        region_name = location.raw["address"]["country_code"].upper()

        if region_name in {"DE", "US"}:
            address = location.raw["address"]
            state = address["state"] if "state" in address else address.get("city")
            if not state:
                raise InvalidRegion(
                    x=lat,
                    y=lon,
                    msg="Could not determine the region for this location. Contact Support",
                )
            state_normalized = unidecode(state.replace("-", "_").upper())

            region_name = f"{region_name}_{state_normalized}"

        try:
            return REGION[region_name]
        except KeyError:
            raise InvalidRegion(lat, lon)

    @classmethod
    def get_lat_lon_from_address(cls, address: str) -> LatLong:
        if strtobool(os.environ.get("TEST_ENVIRONMENT", "False")):
            return LatLong(lat=47.4047366, lon=8.4864537)

        api_key = os.environ.get("GOOGLE_GEOCODE_API_KEY")
        if not api_key:
            raise GoogleGeocodeAPIException(
                "API key not provided to use Google Geocode API"
            )
        logger.debug(f"Requesting lat/lng lookup of address {address} to Google API")
        response = requests.get(
            f"{cls.google_geocode_address}?address={address}&key={api_key}"
        )
        if response.ok:
            if not response.json()["results"]:
                raise GoogleGeocodeAPIException(
                    f"Couldn't get a geocode for the address: {address}. Reason: {response.status_code}: {response.json()}"
                )
            result = response.json()["results"][0]["geometry"]["location"]
            return LatLong(lat=result["lat"], lon=result["lng"])
        else:
            raise GoogleGeocodeAPIException(
                f"Couldn't get a geocode for the address: {address}. Reason: {response.status_code}: {response.json()}"
            )
