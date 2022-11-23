import pytest
from shapely.geometry import Polygon

from dufresne.polygon.polygon_triangulate import triangulate_polygon


@pytest.mark.parametrize("mode", ["pi", "pqa"])
def test_triangulate_polygon_non_convex_2d(non_convex_polygon_2d, mode):
    actual_triangulated_area_2d = sum(
        [
            Polygon(triangle).area
            for triangle in triangulate_polygon(non_convex_polygon_2d, mode=mode)
        ]
    )
    assert actual_triangulated_area_2d == pytest.approx(
        non_convex_polygon_2d.area, abs=1e-5
    )


@pytest.mark.parametrize("mode", ["pi", "pqa"])
def test_triangulate_polygon_non_convex_3d(non_convex_polygon_3d, mode):
    actual_triangulated_area_3d = sum(
        [
            Polygon(triangle).area
            for triangle in triangulate_polygon(non_convex_polygon_3d, mode=mode)
        ]
    )
    assert actual_triangulated_area_3d == pytest.approx(
        non_convex_polygon_3d.area, abs=1e-5
    )


@pytest.mark.parametrize("mode", ["pi", "pqa"])
def test_triangulate_polygon_with_holes(polygon_with_holes, mode):
    actual_triangulated_area = sum(
        [
            Polygon(triangle).area
            for triangle in triangulate_polygon(polygon_with_holes, mode=mode)
        ]
    )
    assert actual_triangulated_area == pytest.approx(polygon_with_holes.area, abs=1e-5)
