from datetime import datetime, timedelta
from typing import Iterator

import pysolar.util
from pytz import timezone
from tenacity import retry, retry_if_exception, stop_after_attempt
from timezonefinder import TimezoneFinder

from common_utils.constants import (
    DEFAULT_SUN_OBS_DATES,
    DEFAULT_SUN_OBS_FREQ_IN_HOURS_POTENTIAL_VIEW,
)
from common_utils.exceptions import MissingSunDimensionException

timezone_finder = TimezoneFinder()


class SuntimesHandler:
    @classmethod
    @retry(
        retry=retry_if_exception(IndexError), stop=stop_after_attempt(3), reraise=True
    )
    def get_sun_obs_times_from_wgs84(cls, lat: float, lon: float) -> Iterator[datetime]:
        tz_info = timezone(timezone_finder.timezone_at(lng=lon, lat=lat))
        return (
            obs_time
            for day_date in DEFAULT_SUN_OBS_DATES.values()
            for obs_time in cls._get_obs_times(
                day=tz_info.localize(dt=day_date), lat=lat, lon=lon
            )
        )

    @staticmethod
    def _get_obs_times(day: datetime, lat: float, lon: float) -> Iterator[datetime]:
        sunrise, sunset = pysolar.util.get_sunrise_sunset(
            latitude_deg=lat, longitude_deg=lon, when=day
        )
        return (
            day + timedelta(hours=hours)
            for hours in range(0, 24, DEFAULT_SUN_OBS_FREQ_IN_HOURS_POTENTIAL_VIEW)
            if sunrise < day + timedelta(hours=hours) < sunset
        )

    @classmethod
    def get_sun_times_v2(cls, site_id: int) -> list[datetime]:
        from handlers import SiteHandler
        from handlers.db import SiteDBHandler

        site_info = SiteDBHandler.get_by(id=site_id, output_columns=["lat", "lon"])
        latlon = SiteHandler.get_lat_lon_location(site_info=site_info)
        return list(cls.get_sun_obs_times_from_wgs84(lat=latlon.y, lon=latlon.x))

    @staticmethod
    def get_sun_key_from_datetime(dt: datetime) -> str:
        return "sun-" + str(dt)

    @staticmethod
    def get_datetime_from_sun_key(key: str) -> datetime:
        return datetime.strptime(key[4:], "%Y-%m-%d %H:%M:%S%z")

    @classmethod
    def get_first_sun_key_summer_midday(cls, site_id) -> str:
        for date in cls.get_sun_times_v2(site_id=site_id):
            if date.date() == DEFAULT_SUN_OBS_DATES["june"].date():
                if 18 >= date.hour >= 12:
                    return cls.get_sun_key_from_datetime(date)
        raise MissingSunDimensionException(
            f"{site_id} missing sun values for June at midday"
        )
