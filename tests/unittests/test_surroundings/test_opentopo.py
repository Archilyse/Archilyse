import pytest

from common_utils.exceptions import OpenTopoException
from surroundings.opentopo_handler import OpenTopoHandler


def test_open_topo_get_tile(mocker, requests_mock):
    mocked_method = mocker.patch.object(
        OpenTopoHandler,
        OpenTopoHandler._get_globaldem_url.__name__,
        return_value="http://fake.com",
    )
    requests_mock.get("http://fake.com", content=b"data")

    OpenTopoHandler.get_srtm_tile(bb_min_north=10, bb_min_east=10)
    mocked_method.assert_called_once_with(
        bb_min_north=10 - 0.0001,
        bb_max_north=10 + 1 + 0.0001,
        bb_min_east=10 - 0.0001,
        bb_max_east=10 + 1 + 0.0001,
    )


def test_open_topo_get_tile_raises(mocker, requests_mock):
    mocker.patch.object(
        OpenTopoHandler,
        OpenTopoHandler._get_globaldem_url.__name__,
        return_value="http://fake.com",
    )
    requests_mock.get("http://fake.com", status_code="400", text="NO tiles")
    with pytest.raises(OpenTopoException):
        OpenTopoHandler.get_srtm_tile(bb_min_north=10, bb_min_east=10)
