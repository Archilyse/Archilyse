import json

import pytest
import shapely
from shapely.affinity import rotate, scale
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
    box,
    shape,
)

from brooks.util.geometry_ops import (
    dot_product_normalised_linestrings,
    get_center_line_from_rectangle,
    get_line_strings,
    get_polygons,
    remove_small_holes_from_polygon,
    safe_simplify,
)


@pytest.mark.parametrize(
    "polygon,expected",
    [
        (
            """POLYGON ((550 -500, 550 -200, 650 -200, 650 -500, 550 -500))""",
            [[600.0, 600.0], [-500.0, -200.0]],
        ),
        (
            """POLYGON ((105.3658536585365937 168.2926829268292863, -144.6341463414634347 -31.7073170731707279, -50.0000000000000000 -150.0000000000000000, 200.0000000000000000 49.9999999999999858, 105.3658536585365937 168.2926829268292863))""",
            [
                [-97.31707317073172, 152.6829268292683],
                [-90.85365853658536, 109.14634146341463],
            ],
        ),
    ],
)
def test_get_center_line_from_rectangle(polygon, expected):
    """To visualize:
    from brooks.visualization.debug.visualisation import draw
    draw([result, polygon])
    """
    polygon = shapely.wkt.loads(polygon)

    result = get_center_line_from_rectangle(polygon=polygon)[0]

    assert polygon.intersects(result)
    assert result.xy[0].tolist() == pytest.approx(expected[0], rel=0.1)  # x coordinates
    assert result.xy[1].tolist() == pytest.approx(expected[1], rel=0.1)  # y coordinates


def test_get_centerline_from_square():
    """
    This test ensures that the centerline returned for a square
    is either the horizontal or the vertical one but not the diagonal
    """
    square = box(0, 0, 1, 1)
    result = get_center_line_from_rectangle(polygon=square)[0]
    x1, y1, x2, y2 = (
        result.coords[0][0],
        result.coords[0][1],
        result.coords[1][0],
        result.coords[1][1],
    )
    dx, dy = abs(x2 - x1), abs(y2 - y1)
    assert dx == pytest.approx(expected=0.0) or dy == pytest.approx(expected=0.0)


@pytest.mark.parametrize(
    "angle,expected_value",
    [
        (0, 1.000),
        (45, 0.707),
        (90, 0.000),
        (135, -0.707),
        (180, -1.000),
        (225, -0.707),
        (270, 0.000),
        (315, 0.707),
        (360, 1.000),
    ],
)
def test_dot_product_linestrings(angle, expected_value):
    line_a = LineString([(0, 0), (5, 0)])
    line_b = rotate(geom=scale(geom=line_a, xfact=2), angle=angle)
    assert dot_product_normalised_linestrings(
        line_a=line_a, line_b=line_b
    ) == pytest.approx(expected=expected_value, abs=0.001)


def test_dot_product_failing_case():
    """
    We need to round the dot product before returning
    as otherwise in some cases we return values smaller than -1 or values bigger than 1
    due to precision errors
    """
    line_a = LineString(
        [
            (1068.0957216659726, 1545.3768403340964),
            (1551.9419207919009, 1547.9642531636468),
        ]
    )
    line_b = LineString(
        [
            (2192.7232972939887, 1551.3908915406637),
            (1551.9419207919009, 1547.9642531636468),
        ]
    )
    assert dot_product_normalised_linestrings(line_a=line_a, line_b=line_b) >= -1.0


class TestGetLineStrings:
    dummy_line_string = LineString([(0, 0), (1, 1)])

    @pytest.mark.parametrize(
        "input_geometry, expected_line_strings",
        [
            (dummy_line_string, [dummy_line_string]),
            (MultiLineString([dummy_line_string]), [dummy_line_string]),
            (Point(0, 0), []),
            (MultiPoint([Point(0, 0)]), []),
            (GeometryCollection([Point(0, 0), dummy_line_string]), [dummy_line_string]),
            (
                GeometryCollection([Point(0, 0), MultiLineString([dummy_line_string])]),
                [dummy_line_string],
            ),
            (LineString(), []),
        ],
    )
    def test_get_line_strings(self, input_geometry, expected_line_strings):
        assert list(get_line_strings(geometry=input_geometry)) == expected_line_strings

    @pytest.mark.parametrize(
        "input_geometry",
        [
            Polygon([(0, 0), (1, 0), (1, 1)]),
            GeometryCollection([Polygon([(0, 0), (1, 0), (1, 1)])]),
        ],
    )
    def test_get_line_strings_raises_exception_on_unsupported_geometry_type(
        self, input_geometry
    ):
        with pytest.raises(Exception):
            list(get_line_strings(geometry=input_geometry))


class TestGetPolygons:
    dummy_polygon = Polygon([(0, 0), (1, 0), (1, 1)])

    @pytest.mark.parametrize(
        "input_geometry, expected_polygons",
        [
            (dummy_polygon, [dummy_polygon]),
            (MultiPolygon([dummy_polygon]), [dummy_polygon]),
            (GeometryCollection([Point(0, 0), dummy_polygon]), [dummy_polygon]),
            (
                GeometryCollection([Point(0, 0), MultiPolygon([dummy_polygon])]),
                [dummy_polygon],
            ),
            (Point(0, 0), []),
            (MultiPoint([Point(0, 0)]), []),
            (LineString([(0, 0), (1, 1)]), []),
            (Polygon(), []),
        ],
    )
    def test_get_polygons(self, input_geometry, expected_polygons):
        assert list(get_polygons(geometry=input_geometry)) == expected_polygons

    @pytest.mark.parametrize("input_geometry", [{"some nonsense"}])
    def test_get_polygons_raises_exception_on_unsupported_geometry_type(
        self, input_geometry
    ):
        with pytest.raises(Exception):
            list(get_polygons(geometry=input_geometry))


def test_remove_small_holes_from_polygon(fixtures_path):
    with fixtures_path.joinpath("geometries/footprint_with_small_holes.json").open(
        "r"
    ) as f:
        footprint = shape(json.load(f))
    cleaned_footprint = remove_small_holes_from_polygon(polygon=footprint)
    assert len(footprint.interiors) == 69
    assert len(cleaned_footprint.interiors) == 8
    assert footprint.area == pytest.approx(expected=443.4474, abs=1e-4)
    assert cleaned_footprint.area == pytest.approx(expected=445.6016, abs=1e-4)


def test_safe_simplify():
    pol = Polygon(
        [(0, 0), (0, 20), (20, 20), (20, 20), (20, 0), (0, 0)],
    )
    assert safe_simplify(pol).area == pol.area
