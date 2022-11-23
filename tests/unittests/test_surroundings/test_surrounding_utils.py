import pytest
from shapely.geometry import Point

from brooks.util.projections import project_geometry
from common_utils.constants import REGION
from ifc_reader.utils import from_deg_min_sec_to_degrees, from_lat_lon_to_deg_min_sec


def test_lv95_to_84():
    projected_point = project_geometry(
        geometry=Point(2682413.2, 1248515.6),
        crs_from=REGION.CH,
        crs_to=REGION.LAT_LON,
    )
    expected_lat, expected_lon = 47.38231, 8.530015

    assert pytest.approx(projected_point.y) == expected_lat
    assert pytest.approx(projected_point.x) == expected_lon


def test_degrees_to_minutes():
    lon = 8.530687554806144
    lat = 47.18287204815751
    lon_time_display = from_lat_lon_to_deg_min_sec(lon)
    lat_time_display = from_lat_lon_to_deg_min_sec(lat)

    final_lon = from_deg_min_sec_to_degrees(
        degrees=lon_time_display[0],
        min=lon_time_display[1],
        sec=lon_time_display[2],
        micro_sec=lon_time_display[3],
    )

    final_lat = from_deg_min_sec_to_degrees(
        degrees=lat_time_display[0],
        min=lat_time_display[1],
        sec=lat_time_display[2],
        micro_sec=lat_time_display[3],
    )

    assert final_lon == pytest.approx(expected=lon, abs=1e-8)
    assert final_lat == pytest.approx(expected=lat, abs=1e-8)
