import pytest
from geopy.exc import GeocoderServiceError
from requests import RequestException
from tenacity import retry

from common_utils.constants import REGION
from common_utils.exceptions import InvalidRegion
from handlers.geo_location import GeoLocator, LatLong


@pytest.mark.parametrize(
    "exception, expected_retries",
    [
        (GeocoderServiceError("Non-successful status code 502"), 2),
        (GeocoderServiceError("Non-successful status code 504"), 2),
        (GeocoderServiceError("Some random BS"), 0),
        (RequestException(), 2),
        (Exception(), 0),
    ],
)
def test_get_region_from_lat_lon_retry_config(exception, expected_retries, mocker):
    import handlers.geo_location

    mocked_wait = mocker.patch.object(
        handlers.geo_location.wait_exponential, "__call__", return_value=0.0
    )

    @retry(**handlers.geo_location.get_region_from_lat_lon_retry_config)
    def failed_request():
        raise exception

    with pytest.raises(type(exception)):
        failed_request()

    assert mocked_wait.call_count == expected_retries


@pytest.mark.parametrize(
    "country_code, state, expected_region",
    [
        ("ch", "not relevant", REGION.CH),
        ("dk", "not relevant", REGION.DK),
        ("de", "BREMEN", REGION.DE_BREMEN),
        ("de", "Baden-Württemberg", REGION.DE_BADEN_WURTTEMBERG),
        ("de", "Thüringen", REGION.DE_THURINGEN),
        ("us", "Georgia", REGION.US_GEORGIA),
    ],
)
def test_get_region_from_lat_lon(
    monkeypatch, requests_mock, country_code, state, expected_region
):
    monkeypatch.setenv("TEST_ENVIRONMENT", "False")
    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 293958087,
            "display_name": "Alter Zürichweg, Gut Sonnenberg, Schlieren, Bezirk Dietikon, Zürich, 8952, Switzerland",
            "address": {"state": state, "country_code": country_code},
        },
    )
    region = GeoLocator().get_region_from_lat_lon(lat=40.0, lon=30.0)
    assert region == expected_region


def test_get_region_from_lat_lon_invalid_region(monkeypatch, requests_mock):
    monkeypatch.setenv("TEST_ENVIRONMENT", "False")
    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 293958087,
            "display_name": "Alter Zürichweg, Gut Sonnenberg, Schlieren, Bezirk Dietikon, Zürich, 8952, Switzerland",
            "address": {"state": "Shithole", "country_code": "SHIT"},
        },
    )
    with pytest.raises(InvalidRegion):
        GeoLocator().get_region_from_lat_lon(lat=40.0, lon=30.0)


def test_geolocator_no_state_but_city(monkeypatch, requests_mock):
    monkeypatch.setenv("TEST_ENVIRONMENT", "False")
    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 4815162342,
            "display_name": "Salpica",
            "address": {"city": "Hamburg", "country_code": "DE"},
        },
    )

    region = GeoLocator().get_region_from_lat_lon(lat=40.0, lon=30.0)
    assert region == REGION.DE_HAMBURG


def test_geolocator_no_state_no_city(monkeypatch, requests_mock):
    monkeypatch.setenv("TEST_ENVIRONMENT", "False")
    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={
            "place_id": 4815162342,
            "display_name": "Salpica",
            "address": {"no_city": "Hamburg", "country_code": "DE"},
        },
    )

    with pytest.raises(InvalidRegion):
        GeoLocator().get_region_from_lat_lon(lat=40.0, lon=30.0)


def test_get_region_from_lat_lon_no_region(monkeypatch, requests_mock):
    monkeypatch.setenv("TEST_ENVIRONMENT", "False")
    requests_mock.get(
        GeoLocator.nominatim_reverse_address,
        json={},
    )
    with pytest.raises(InvalidRegion):
        GeoLocator().get_region_from_lat_lon(lat=40.0, lon=30.0)


def test_geo_locator_test_env(monkeypatch):
    monkeypatch.setenv("TEST_ENVIRONMENT", "True")
    assert GeoLocator().get_region_from_lat_lon(lat=20000, lon=2000) == REGION.CH


def test_google_geocoder(monkeypatch, requests_mock):
    fake_key = "1234"
    monkeypatch.setenv("GOOGLE_GEOCODE_API_KEY", fake_key)
    monkeypatch.setenv("TEST_ENVIRONMENT", "False")
    test_address = "test_address"

    requests_mock.get(
        f"https://maps.googleapis.com/maps/api/geocode/json?address={test_address}&key={fake_key}",
        json={"results": [{"geometry": {"location": {"lat": 1, "lng": 20}}}]},
    )
    assert GeoLocator.get_lat_lon_from_address(address=test_address) == LatLong(
        lat=1, lon=20
    )
