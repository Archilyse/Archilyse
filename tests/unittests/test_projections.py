import pytest
from pygeos import Geometry, get_x, get_y, get_z
from shapely.geometry import box

from brooks.util.projections import project_geometry, project_xy, pygeos_project
from common_utils.constants import REGION

lat = 47.3903552
lon = 8.5172687
swiss_x = 2681438.40431827
swiss_y = 1249395.8194439558


@pytest.mark.parametrize(
    "pol", [box(0, 0, 1, 1), box(2784415, 1152707, 2784420, 1152720)]
)
def test_project_geometry(pol):
    recovered_pol = project_geometry(
        project_geometry(pol, crs_from=REGION.CH, crs_to=REGION.LAT_LON),
        crs_from=REGION.LAT_LON,
        crs_to=REGION.CH,
    )
    assert recovered_pol.equals_exact(pol, tolerance=0.01)


def test_project_xy():
    projected = project_xy(
        xs=swiss_x, ys=swiss_y, crs_from=REGION.CH, crs_to=REGION.LAT_LON
    )
    assert projected == pytest.approx((lon, lat), abs=10**-3)

    [projected_x], [projected_y] = project_xy(
        xs=[swiss_x], ys=[swiss_y], crs_from=REGION.CH, crs_to=REGION.LAT_LON
    )
    assert (projected_x, projected_y) == pytest.approx((lon, lat), abs=10**-3)


@pytest.mark.parametrize(
    "geometry, crs_from, crs_to, include_z, expected",
    [
        (
            f"POINT ({lat} {lon} 10.0)",
            REGION.LAT_LON,
            REGION.CH,
            True,
            (swiss_x, swiss_y, 10.0),
        ),
        (
            f"POINT ({swiss_x} {swiss_y} 10.0)",
            REGION.CH,
            REGION.LAT_LON,
            False,
            (lat, lon, 10.0),
        ),
    ],
)
def test_pygeos_project(
    geometry, expected, include_z: bool, crs_from: REGION, crs_to: REGION
):
    projected_geometry = pygeos_project(
        geometries=[Geometry(geometry)],
        crs_from=crs_from,
        crs_to=crs_to,
        include_z=include_z,
    )
    expected_x, expected_y, expected_z = expected
    assert get_x(projected_geometry)[0] == pytest.approx(expected_x, abs=10**-3)
    assert get_y(projected_geometry)[0] == pytest.approx(expected_y, abs=10**-3)
    if include_z:
        assert get_z(projected_geometry)[0] == pytest.approx(expected_z, abs=10**-3)
