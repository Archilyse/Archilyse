import numpy as np
import pytest
from shapely import wkt
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from brooks.models import SimArea, SimFeature
from brooks.types import AreaType, FeatureType
from common_utils.constants import SIMULATION_VERSION
from simulations.basic_features import CustomValuatorBasicFeatures2
from simulations.rectangulator import get_max_rectangle_in_convex_polygon
from tests.constants import FLAKY_RERUNS

EA_ACCURACY = 0.95
GENERATIONS = 20


def assert_accuracy_ea(
    solution_rectangle: Polygon,
    convex_polygon: Polygon,
    expected_area: float,
    accuracy: float = EA_ACCURACY,
):
    assert solution_rectangle.area >= expected_area * accuracy

    assert convex_polygon.contains(solution_rectangle)


def test_ea_get_biggest_rectangle_irregular_convex_polygon(
    mocker, area_with_holes_polygon
):
    """
    from brooks.visualization.debug.visualisation import draw
    draw([rectangle, area_footprint])
    """
    from simulations.rectangulator.ea_rectangulator import creator

    creator_spy = mocker.spy(creator, "create")

    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=area_with_holes_polygon, generations=GENERATIONS
    )
    assert_accuracy_ea(
        solution_rectangle=rectangle,
        expected_area=27.66,
        convex_polygon=area_with_holes_polygon,
    )

    creator_spy.assert_called()


def test_ea_get_biggest_rectangle_in_rectangular_polygon(mocker):
    from simulations.rectangulator.ea_rectangulator import creator

    area = box(0, 0, 10, 10)
    creator_spy = mocker.spy(creator, "create")
    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=area, generations=GENERATIONS
    )
    assert rectangle.area == area.area
    creator_spy.assert_not_called()


def test_ea_get_biggest_rectangle_in_almost_rectangular_polygon(mocker):
    from simulations.rectangulator.ea_rectangulator import creator

    area = Polygon(((0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, -1.0), (0.0, 0.0)))

    creator_spy = mocker.spy(creator, "create")
    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=area, generations=GENERATIONS
    )

    expected_perfect_area = 100.0
    assert_accuracy_ea(
        solution_rectangle=rectangle,
        expected_area=expected_perfect_area,
        convex_polygon=area,
    )
    creator_spy.assert_called()


def test_ea_get_biggest_rectangle_in_triangle():
    """Equilateral triangles should have half of the area"""
    area = Polygon(((0.0, 0.0), (2.0, 0.0), (1.0, 2.0), (0.0, 0.0)))
    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=area, generations=GENERATIONS
    )
    expected_perfect_area = area.area / 2.0
    assert_accuracy_ea(
        solution_rectangle=rectangle,
        expected_area=expected_perfect_area,
        convex_polygon=area,
    )


@pytest.mark.flaky(reruns=FLAKY_RERUNS)
def test_ea_get_biggest_rectangle_in_circle(circle_polygon):
    """Following the example of https://shapely.readthedocs.io/en/stable/manual.html#object.simplify"""
    diameter = (
        np.sqrt(circle_polygon.simplify(0.05, preserve_topology=False).area / np.pi) * 2
    )
    # Being the diameter equal to the maximum rectangle that can be fit into a circle
    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=circle_polygon, generations=GENERATIONS
    )
    assert_accuracy_ea(
        solution_rectangle=rectangle,
        expected_area=diameter,
        convex_polygon=circle_polygon,
        accuracy=0.85,  # The circle case in tests could be problematic
    )


def test_ea_basic_features_get_biggest_rectangle_with_areas():
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

    rectangle = CustomValuatorBasicFeatures2.biggest_rectangle_in_area(
        area=area,
        simulation_version=SIMULATION_VERSION.EXPERIMENTAL,
        generations=GENERATIONS,
    )
    assert_accuracy_ea(
        solution_rectangle=rectangle,
        expected_area=5 * 4,
        convex_polygon=area.footprint.difference(feature.footprint),
    )


def test_ea_optimize_tiny_area():
    polygon = wkt.loads(
        "POLYGON ((2385.7045350946586950 -2562.9688858424169666, 2385.4862705531068059 -2561.1915690978580642, "
        "2385.6215604450571846 -2561.1796197718599615, 2385.8442111066365214 -2562.9565491173507326, "
        "2385.7045350946586950 -2562.9688858424169666))"
    )
    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=polygon, generations=GENERATIONS
    )
    assert rectangle.area >= 0.0


def test_ea_almost_rectangular():
    # This is a case that could have failed without using the deterministic rectangulator seed
    pol = unary_union([box(0, 0, 10, 10), box(10, 2, 10.1, 8)])
    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=pol, generations=GENERATIONS
    )

    expected_perfect_area = 100.0

    assert_accuracy_ea(
        solution_rectangle=rectangle,
        expected_area=expected_perfect_area,
        convex_polygon=pol,
    )


def test_ea_rectangle_many_vertices():
    # This is a case of a rectangle with many vertices, we expect a rectangle with almost same area and 4 sides
    pol = Polygon(
        [
            (24.555065681581006, 13.363180158927962),
            (24.55506568158709, 15.038373414956),
            (26.003851515580997, 15.038373414956),
            (26.003851515580997, 13.36318015890828),
            (24.665065682781545, 13.36318015892562),
            (24.555065681581006, 13.363180158927962),
        ]
    )

    rectangle = get_max_rectangle_in_convex_polygon(
        target_convex_polygon=pol, generations=GENERATIONS
    )

    assert len(rectangle.exterior.coords) == 5
    assert rectangle.area == pytest.approx(pol.area)
