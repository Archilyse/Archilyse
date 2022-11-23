import pkgutil

import pytest

from simulations.suntimes.suntimes_handler import SuntimesHandler


@pytest.mark.parametrize(
    "lat, lon, expected_obs_times",
    [
        (
            # Zurich Switzerland
            47.5642388562567,
            7.636568666258004,
            {
                "2018-03-21 08:00:00+01:00",
                "2018-03-21 10:00:00+01:00",
                "2018-03-21 12:00:00+01:00",
                "2018-03-21 14:00:00+01:00",
                "2018-03-21 16:00:00+01:00",
                "2018-03-21 18:00:00+01:00",
                "2018-06-21 06:00:00+02:00",
                "2018-06-21 08:00:00+02:00",
                "2018-06-21 10:00:00+02:00",
                "2018-06-21 12:00:00+02:00",
                "2018-06-21 14:00:00+02:00",
                "2018-06-21 16:00:00+02:00",
                "2018-06-21 18:00:00+02:00",
                "2018-06-21 20:00:00+02:00",
                "2018-12-21 10:00:00+01:00",
                "2018-12-21 12:00:00+01:00",
                "2018-12-21 14:00:00+01:00",
                "2018-12-21 16:00:00+01:00",
            },
        ),
        (
            # Boston USA
            42.343452,
            -71.067827,
            {
                "2018-03-21 08:00:00-04:00",
                "2018-03-21 10:00:00-04:00",
                "2018-03-21 12:00:00-04:00",
                "2018-03-21 14:00:00-04:00",
                "2018-03-21 16:00:00-04:00",
                "2018-03-21 18:00:00-04:00",
                "2018-06-21 06:00:00-04:00",
                "2018-06-21 08:00:00-04:00",
                "2018-06-21 10:00:00-04:00",
                "2018-06-21 12:00:00-04:00",
                "2018-06-21 14:00:00-04:00",
                "2018-06-21 16:00:00-04:00",
                "2018-06-21 18:00:00-04:00",
                "2018-06-21 20:00:00-04:00",
                "2018-12-21 08:00:00-05:00",
                "2018-12-21 10:00:00-05:00",
                "2018-12-21 12:00:00-05:00",
                "2018-12-21 14:00:00-05:00",
                "2018-12-21 16:00:00-05:00",
            },
        ),
    ],
)
def test_get_sun_obs_times_from_wgs84(lat, lon, expected_obs_times):
    obs_times = {
        str(dt) for dt in SuntimesHandler.get_sun_obs_times_from_wgs84(lat=lat, lon=lon)
    }
    assert obs_times == expected_obs_times


def test_celery_conf_includes_all_tasks():
    import tasks
    from workers_config.celery_app import celery_app

    routes_loaded = {
        path[0] for path in celery_app.conf.get("task_routes")[0] if "*" in path[0]
    } - {"celery.*"}
    modules = {
        f"tasks.{module.name}.*"
        for module in pkgutil.iter_modules(tasks.__path__)
        if module.name != "utils"
    }
    includes = {f"{x}.*" for x in celery_app.conf.get("include")}
    assert modules == routes_loaded
    assert modules == includes
