from http import HTTPStatus

import pytest
import requests_mock
from shapely.geometry import box
from tenacity import wait_random_exponential

import surroundings.osm.overpass_api_handler as handler_module
from common_utils.exceptions import OverpassAPIException


def test_get_building_metadata(mocker):
    bounding_box = box(
        2680944.250255447,
        1248422.7511582754,
        2681944.250255447,
        1249422.7511582754,
    )
    with requests_mock.Mocker() as m:
        m.get(
            f"{handler_module.OverpassAPIHandler.building_full_url(bounding_box=bounding_box)}",
            json={"elements": [{"id": 1, "height": 10}]},
            status_code=HTTPStatus.OK,
        )

        building_metadata = handler_module.OverpassAPIHandler.get_building_metadata(
            bounding_box=bounding_box
        )
        assert building_metadata == {1: {"id": 1, "height": 10}}


def test_get_building_metadata_incorrect_response(mocker):
    bounding_box = box(
        2680944.250255447,
        1248422.7511582754,
        2681944.250255447,
        1249422.7511582754,
    )
    with requests_mock.Mocker() as m:
        m.get(
            f"{handler_module.OverpassAPIHandler.building_full_url(bounding_box=bounding_box)}",
            status_code=400,
        )

        with pytest.raises(OverpassAPIException):
            handler_module.OverpassAPIHandler.get_building_metadata(
                bounding_box=bounding_box
            )


def test_get_building_metadata_retry_on_connection_error(mocker):
    requests_mocked = mocker.patch("surroundings.osm.overpass_api_handler.requests")
    requests_mocked.get.side_effect = [
        ConnectionError,
    ] * 5
    bounding_box = box(
        2680944.250255447, 1248422.7511582754, 2681944.250255447, 1249422.7511582754
    )
    with pytest.raises(ConnectionError):
        handler_module.OverpassAPIHandler.get_building_metadata(
            bounding_box=bounding_box
        )
    assert requests_mocked.get.call_count == 5


@pytest.mark.parametrize(
    "code", [HTTPStatus.GATEWAY_TIMEOUT, HTTPStatus.TOO_MANY_REQUESTS]
)
def test_get_building_metadata_retry_on_bad_code(mocker, code):
    bounding_box = box(
        2680944.250255447,
        1248422.7511582754,
        2681944.250255447,
        1249422.7511582754,
    )
    mocker.patch.object(
        handler_module.OverpassAPIHandler.get_entity_metadata.retry,
        "wait",
        wait_random_exponential(multiplier=0, max=0.1),
    )
    with requests_mock.Mocker() as m:
        m.get(
            f"{handler_module.OverpassAPIHandler.building_full_url(bounding_box=bounding_box)}",
            status_code=code,
        )

        with pytest.raises(ConnectionError):
            handler_module.OverpassAPIHandler.get_building_metadata(
                bounding_box=bounding_box
            )
