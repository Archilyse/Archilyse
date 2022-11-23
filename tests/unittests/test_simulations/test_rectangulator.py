import numpy as np
import pytest
from shapely.geometry import Point, box

from brooks.models import SimArea, SimFeature
from brooks.types import AreaType, FeatureType
from simulations.basic_features import CustomValuatorBasicFeatures2
from simulations.rectangulator import DeterministicRectangulator


def test_get_biggest_rectangle_irregular_convex_polygon(area_with_holes_polygon):
    """
    from brooks.visualization.debug.visualisation import draw
    draw([rectangle, area_with_holes_polygon])
    """
    rectangle = DeterministicRectangulator(
        polygon=area_with_holes_polygon
    ).get_biggest_rectangle()

    assert rectangle.area == pytest.approx(expected=27.66, abs=0.1)


@pytest.mark.xfail(
    reason="The algorithm doesn't return a maximum value correctly for a box. Returns 87.46 instead of 100"
)
def test_get_biggest_rectangle_in_regular_polygons():
    area = box(0, 0, 10, 10)
    rectangle = DeterministicRectangulator(polygon=area).get_biggest_rectangle()

    assert rectangle.area == pytest.approx(expected=area.area, abs=0.1)


def test_get_biggest_rectangle_in_triangle(triangle_polygon):
    """Equilateral triangles work ok and the max rectangle is always half of the area"""
    rectangle = DeterministicRectangulator(
        polygon=triangle_polygon
    ).get_biggest_rectangle()
    assert rectangle.area == pytest.approx(
        expected=triangle_polygon.area / 2.0, abs=0.1
    )


@pytest.mark.xfail(reason="It returns around 0.30 when it should return around 1.97m")
def test_get_biggest_rectangle_in_circle():
    """Following the example of https://shapely.readthedocs.io/en/stable/manual.html#object.simplify"""
    p = Point(0.0, 0.0)
    area = p.buffer(1.0)
    diameter = np.sqrt(area.simplify(0.05, preserve_topology=False).area / np.pi) * 2
    # Being the diameter equal to the maximum rectangle that can be fit into a circle
    rectangle = DeterministicRectangulator(polygon=area).get_biggest_rectangle()
    assert rectangle.area == pytest.approx(expected=diameter, abs=0.1)


@pytest.mark.xfail(
    reason="The algorithm doesn't cover the upper part, return 18.6m instead of almost 20.0"
)
def test_basic_features_get_biggest_rectangle_with_areas():
    """
                                5,5
     +-------------------------+
     |                         |
     |                         |
     |                         |
     |                         |
     |      Area               |
     |                         |
     |                         |
     |               3,1       |
     +----------------+        |
     |  Feature       |        |
     |                |        |
     +----------------+--------+
    0,0               3, 0
    """

    area = SimArea(
        footprint=box(minx=0, miny=0, maxx=5, maxy=5), area_type=AreaType.BALCONY
    )
    feature = SimFeature(
        footprint=box(minx=0, miny=0, maxx=3, maxy=1), feature_type=FeatureType.SHAFT
    )
    area.features = {feature}

    rectangle = CustomValuatorBasicFeatures2.biggest_rectangle_in_area(area=area)

    assert rectangle.area == pytest.approx(expected=20.0, abs=0.1)
