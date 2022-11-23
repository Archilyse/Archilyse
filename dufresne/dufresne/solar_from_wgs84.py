from typing import Tuple

import numpy as np
from pysolar.solar import get_altitude, get_azimuth


def get_solar_parameters_from_wgs84(
    latitude: float, longitude: float, date
) -> Tuple[float, float, float]:
    """Returns the solar position and iluminance for a given
       lat, lon pair in WGS84 coordinates.

    Args:
        latitude (float): The WGS84 latitude
        longitude (float): The WGS84 longitude
        date (datetime.datetime): The local time at the given lat, lon pair
    """
    # Use pysolar to get the correct position
    sun_azimuth = get_azimuth(latitude, longitude, date)
    sun_altitude = get_altitude(latitude, longitude, date)

    # Transform such that azimuth has format (0 = North, clockwise order)
    # and altitude has format (0 = horizon, pi/2 = zenith)
    sun_azimuth = np.abs(sun_azimuth)
    sun_azimuth_rad = np.deg2rad(sun_azimuth)
    sun_altitude_rad = np.deg2rad(sun_altitude)

    # Compute zenith luminance according to
    # Soler, A., and K. K. Gopinathan. "Analysis of zenith luminance data for all sky conditions."
    # Renewable energy 24, no. 2 (2001): 185-196.
    spring = [-0.65382, 0.10065, -0.00380, 7.95867e-5, -7.99933e-7, 3.21145e-9]
    summer = [-0.71899, 0.10976, -0.00491, 1.18805e-4, -1.36348e-6, 5.98443e-9]
    autumn = [-0.53256, 0.07056, -0.0016, 1.34303e-5, 0, 0]
    winter = [-0.60756, 0.08847, -0.00225, 1.92226e-5, 0, 0]
    month_to_params = [
        winter,
        winter,
        spring,
        spring,
        spring,
        summer,
        summer,
        summer,
        autumn,
        autumn,
        autumn,
        winter,
    ]
    zenith_luminance = 10 ** np.polynomial.Polynomial(month_to_params[date.month - 1])(
        sun_altitude
    )

    return sun_azimuth_rad, sun_altitude_rad, zenith_luminance
