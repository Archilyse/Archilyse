import pytest

from common_utils.exceptions import MissingSunDimensionException
from simulations.suntimes.suntimes_handler import SuntimesHandler


def test_slam_sun_v2(site):
    from pytz import timezone

    europe_zurich = timezone("Europe/Zurich")
    from datetime import datetime

    from simulations.suntimes.suntimes_handler import SuntimesHandler

    assert SuntimesHandler.get_sun_times_v2(site_id=site["id"]) == [
        europe_zurich.localize(datetime(2018, 3, 21, 8, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 3, 21, 10, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 3, 21, 12, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 3, 21, 14, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 3, 21, 16, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 3, 21, 18, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 6, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 8, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 10, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 12, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 14, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 16, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 18, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 6, 21, 20, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 12, 21, 10, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 12, 21, 12, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 12, 21, 14, 0), is_dst=True),
        europe_zurich.localize(datetime(2018, 12, 21, 16, 0), is_dst=True),
    ]


def test_get_first_sun_key_summer_midday_raises(mocker, site):
    from datetime import datetime

    mocker.patch.object(
        SuntimesHandler,
        "get_sun_times_v2",
        return_value=[datetime(2018, 12, 21, 16, 0)],
    )
    with pytest.raises(MissingSunDimensionException):
        SuntimesHandler.get_first_sun_key_summer_midday(site_id=site["id"])
