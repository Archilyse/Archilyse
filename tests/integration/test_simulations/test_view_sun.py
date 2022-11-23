import datetime
import random

import numpy as np
import pytest
from pytz import timezone
from timezonefinder import TimezoneFinder

from dufresne.solar_from_wgs84 import get_solar_parameters_from_wgs84
from simulations.view import ViewWrapper
from tests.integration.utils import (
    generate_icosphere,
    get_vtk_mesh_faces,
    get_vtk_mesh_vertices,
)
from tests.utils import quavis_test


def cart2sph(x, y, z):
    hxy = np.hypot(x, y)
    r = np.hypot(hxy, z)
    el = np.arctan2(z, hxy)
    az = np.arctan2(y, x)
    return az, el, r


@pytest.mark.vtk
@quavis_test
def test_sun_plot():
    random.seed(42)
    date = datetime.datetime(2019, 4, 2, 10, 0, 0, 0, tzinfo=datetime.timezone.utc)
    lat, lon = 49.0158279, 8.3394945
    expected_azimuth = 149.16
    expected_altitude = 41.93

    radius = 1000
    epsilon = 0.00001
    azimuth, altitude, zenith_luminance = get_solar_parameters_from_wgs84(
        lat, lon, date
    )

    icosphere = generate_icosphere(radius, np.array([0, 0, 0]), 5)
    icosphere_obs_points = generate_icosphere(radius + epsilon, np.array([0, 0, 0]), 5)

    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    for a, b, c in get_vtk_mesh_faces(mesh=icosphere):
        wrapper.add_triangles(
            [[vertices[a], vertices[b], vertices[c]]],
            group="sphere",
        )

    icosphere_obs_points_normals = []
    vertices_obs_points = get_vtk_mesh_vertices(icosphere_obs_points)
    for a, b, c in get_vtk_mesh_faces(icosphere_obs_points):
        centroid = np.array(
            [vertices_obs_points[a], vertices_obs_points[b], vertices_obs_points[c]]
        ).mean(axis=0)

        if centroid[-2] < 0:
            continue

        wrapper.add_observation_point(
            tuple(centroid.tolist()),
            solar_pos=[(azimuth, altitude)],
            solar_zenith_luminance=[zenith_luminance],
        )

        # since center = (0, 0, 0) the centroid vector is also the normal vector
        icosphere_obs_points_normals.append(centroid / np.linalg.norm(centroid, ord=2))

    # One observation point in center
    result = wrapper.run(run_sun=True)

    # Compute azimuth/altitude where sun is brightest
    x, y, z = [], [], []
    maxpos = None
    for idx, p in enumerate(result):
        normal = icosphere_obs_points_normals[idx]
        az, el, r = cart2sph(*normal)

        x.append(np.rad2deg(az))
        y.append(np.rad2deg(el))
        z.append(p["simulations"]["sun"][0])

        if maxpos is None or z[-1] > maxpos[-1]:
            maxpos = [x[-1], y[-1], z[-1]]

    brightest_azimuth = maxpos[0]
    brightest_altitude = maxpos[1]

    relative_error_azimuth = abs(
        (expected_azimuth - brightest_azimuth) / expected_azimuth
    )
    relative_error_altitude = abs(
        (expected_altitude - brightest_altitude) / expected_altitude
    )

    assert relative_error_azimuth < 0.061
    assert relative_error_altitude < 0.061


@pytest.mark.slow
@pytest.mark.vtk
@quavis_test
def test_sun_v2():
    """
    We create an icosphere, the icosphere's surface is composed of many tiny triangles.
    For each triangle, we add an observation point on the triangle's centroid
    (a little bit shifted outside the sphere). Then we add a cylinder around this
    observation point such that the observation point can only "look" towards it's
    triangle's normal direction. Now the intensity of light going to that point should
    approximately match the sky model's intensity when we translate the normal vector
    to spherical coordinates.
    """
    random.seed(42)
    lat, lon = 47.3649378, 8.5361227

    tz_info = timezone(TimezoneFinder().timezone_at(lng=lon, lat=lat))
    dates = [
        tz_info.localize(datetime.datetime(2018, 6, 21, h, m, 0, 0))
        for h in range(0, 24)
        for m in [0, 15, 30, 45]
    ]

    radius = 1000
    epsilon = 1
    azimuth, altitude, zenith_luminance = zip(
        *[get_solar_parameters_from_wgs84(lat, lon, date) for date in dates]
    )

    icosphere = generate_icosphere(radius, np.array([0, 0, 0]), 4)
    icosphere_obs_points = generate_icosphere(radius + epsilon, np.array([0, 0, 0]), 4)

    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    for a, b, c in get_vtk_mesh_faces(mesh=icosphere):
        wrapper.add_triangles(
            [[vertices[a], vertices[b], vertices[c]]],
            group="sphere",
        )

    icosphere_obs_points_normals = []
    vertices_obs_points = get_vtk_mesh_vertices(icosphere_obs_points)
    for a, b, c in get_vtk_mesh_faces(icosphere_obs_points):
        centroid = np.array(
            [vertices_obs_points[a], vertices_obs_points[b], vertices_obs_points[c]]
        ).mean(axis=0)

        wrapper.add_observation_point(
            tuple(centroid.tolist()),
            solar_pos=list(zip(azimuth, altitude)),
            solar_zenith_luminance=zenith_luminance,
        )

        # since center = (0, 0, 0) the centroid vector is also the normal vector
        icosphere_obs_points_normals.append(centroid / np.linalg.norm(centroid, ord=2))

        a0, b0, c0 = np.array(
            [vertices_obs_points[a], vertices_obs_points[b], vertices_obs_points[c]]
        )
        a1, b1, c1 = (icosphere_obs_points_normals[-1] * 250 + p for p in (a0, b0, c0))
        cylinders = (
            (a0, a1, b0),
            (a1, b1, b0),
            (b0, b1, c0),
            (b1, c1, c0),
            (c0, c1, a0),
            (c1, a1, a0),
        )
        wrapper.add_triangles(cylinders, group="cylinders")

    # One observation point in center
    result = wrapper.run(run_sun=True, use_sun_v2=True)

    actual_az, actual_al = [], []
    expected_az, expected_al = [], []
    for i, _ in enumerate(dates):
        idx, brightest_point = max(
            enumerate(result), key=lambda z: z[1]["simulations"]["sun"][i]
        )
        az, el, r = cart2sph(*icosphere_obs_points_normals[idx])
        if az < 0:
            az = 2 * np.pi + az

        actual_az.append(np.rad2deg(az))
        actual_al.append(np.rad2deg(el))
        expected_az.append(np.rad2deg(azimuth[i]))
        expected_al.append(np.rad2deg(altitude[i]))

    absolute_error_azimuth = np.abs((np.array(expected_az) - actual_az))
    absolute_error_altitude = np.abs((np.array(expected_al) - actual_al))

    # we are checking the 10%, 20% etc. percentiles of the errors
    expected_absolute_error_azimuth_distribution = [
        0.030,
        0.352,
        0.643,
        0.961,
        1.270,
        1.480,
        1.678,
        2.184,
        2.918,
        3.670,
        8.951,
    ]
    expected_absolute_error_altitude_distribution = [
        0.023,
        0.566,
        0.871,
        1.352,
        1.733,
        2.155,
        2.648,
        3.720,
        5.496,
        6.744,
        8.213,
    ]

    assert [
        np.percentile(absolute_error_azimuth, k) for k in range(0, 110, 10)
    ] == pytest.approx(expected_absolute_error_azimuth_distribution, abs=0.1)
    assert [
        np.percentile(absolute_error_altitude, k) for k in range(0, 110, 10)
    ] == pytest.approx(expected_absolute_error_altitude_distribution, abs=0.1)
