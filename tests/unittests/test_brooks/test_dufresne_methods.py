import numpy as np
import pytest
from shapely.geometry import box

from dufresne.polygon import get_polygon_from_coordinates
from dufresne.polygon.parameters_minimum_rotated_rectangle import (
    get_parameters_of_minimum_rotated_rectangle,
)
from dufresne.rotation.quaternion_conjugate import conjugate_quaternion
from dufresne.rotation.quaternion_hamilton_product import hamilton_product


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (
            [1.0, 2.0, 0.3, 0.7777],
            [3.0, 4.5, 1.31871623, 0.0001],
            [-6.395757, 9.4742903, 5.7189069, 3.6208088],
        ),
        (
            [0.33005856, 0.32061029, 0.30158694, 0.39429525],
            [0.907287, 0.10494761, 0.77348121, 0.70152641],
            [-0.244, 0.232, 0.345, 0.806],
        ),
        (
            [0.0, 0.0, 0.0, 0.0],
            [0.907287, 0.10494761, 0.77348121, 0.70152641],
            [0.0, 0.0, 0.0, 0.0],
        ),
    ],
)
def test_hamilton_product(a, b, expected):
    a = np.array(a)
    b = np.array(b)
    expected = np.array(expected)
    result = hamilton_product(a=a, b=b)
    np.testing.assert_almost_equal(result, expected, decimal=3)


def test_conjugate_quaternion():
    q = np.array([1.0, 2.0, 3.0, -1.0])
    expected = np.array([1.0, -2.0, -3.0, 1.0])
    result = conjugate_quaternion(q=q)
    np.testing.assert_almost_equal(result, expected, decimal=3)


@pytest.mark.parametrize(
    "coordinates, area_expected",
    [
        (
            [
                [
                    [
                        [67.15830172314872, 64.0472062068634],
                        [67.15830172314872, -63.13722607532475],
                        [-66.84169827685128, -64.9527937931366],
                        [-66.84169827685128, 64.0472062068634],
                        [67.15830172314872, 64.0472062068634],
                    ]
                ],
                [
                    [
                        [-66.84169827685128, -64.9527937931366],
                        [-66.82814926403171, -65.9527937931366],
                        [-66.84169827685128, -65.9527937931366],
                        [-66.84169827685128, -64.9527937931366],
                    ]
                ],
            ],
            17164.350188400196,
        ),
        (
            [
                [
                    [-15.02111508085045, 11.46412563632498],
                    [14.97888491914955, 11.659429088353363],
                    [14.97888491914955, -11.561914823945472],
                    [-15.02111508085045, -11.561914823945472],
                    [-15.02111508085045, 11.46412563632498],
                ]
            ],
            693.7107655885393,
        ),
        (
            [
                [
                    [53.32292761021881, -304.1270820396576],
                    [-2623.677072389781, -321.5546600756652],
                    [-2623.677072389781, 182.3472220056799],
                    [-2625.677072389781, 182.3472220056799],
                    [-2625.677072389781, 186.3472220056799],
                    [-3071.677072389781, 186.3472220056799],
                    [-3071.677072389781, 354.3472220056799],
                    [-3050.677072389781, 354.3472220056799],
                    [-3050.677072389781, 356.3472220056799],
                    [-2929.677072389781, 356.3472220056799],
                    [-2929.677072389781, 355.3472220056799],
                    [-2926.677072389781, 355.3472220056799],
                    [-2926.677072389781, 270.3472220056799],
                    [-2926.677072389781, 263.3472220056799],
                    [-2919.677072389781, 263.3472220056799],
                    [-2628.677072389781, 263.3472220056799],
                    [-2628.677072389781, 262.3472220056799],
                    [-2623.677072389781, 262.3472220056799],
                    [-2623.677072389781, 263.3472220056799],
                    [-2623.677072389781, 270.3472220056799],
                    [-2623.677072389781, 350.3472220056799],
                    [-2615.677072389781, 350.3472220056799],
                    [-2615.677072389781, 400.3472220056799],
                    [-2218.677072389781, 400.3472220056799],
                    [-2218.677072389781, 273.34768906051954],
                    [-2218.782943357317, 273.34675496901775],
                    [-2218.677072389781, 261.3472220056799],
                    [2782.322927610219, 305.47066499829555],
                    [2782.322927610219, -54.652777994320104],
                    [2781.322927610219, -54.652777994320104],
                    [2781.322927610219, -286.3674881352017],
                    [71.32292761021881, -304.00989996844055],
                    [71.32292761021881, -213.6527779943201],
                    [53.32292761021881, -213.6527779943201],
                    [53.32292761021881, -304.1270820396576],
                ],
                [
                    [-2184.677072389781, -153.6527779943201],
                    [-2053.677072389781, -153.6527779943201],
                    [-2053.677072389781, -152.6527779943201],
                    [-2047.6770723897812, -152.6527779943201],
                    [-2047.6770723897812, -30.652777994320104],
                    [-2052.677072389781, -30.652777994320104],
                    [-2062.677072389781, -30.652777994320104],
                    [-2186.677072389781, -30.652777994320104],
                    [-2186.677072389781, -45.652777994320104],
                    [-2184.677072389781, -45.652777994320104],
                    [-2184.677072389781, -138.6527779943201],
                    [-2184.677072389781, -146.6527779943201],
                    [-2184.677072389781, -153.6527779943201],
                ],
                [
                    [2322.322927610219, -101.6527779943201],
                    [2322.322927610219, -8.652777994320104],
                    [2323.322927610219, -8.652777994320104],
                    [2323.322927610219, 6.347222005679896],
                    [2201.322927610219, 6.347222005679896],
                    [2186.322927610219, 6.347222005679896],
                    [2151.322927610219, 6.347222005679896],
                    [2151.322927610219, 5.347222005679896],
                    [2144.322927610219, 5.347222005679896],
                    [2144.322927610219, -116.6527779943201],
                    [2147.322927610219, -116.6527779943201],
                    [2159.322927610219, -116.6527779943201],
                    [2322.322927610219, -116.6527779943201],
                    [2322.322927610219, -110.6527779943201],
                    [2322.322927610219, -101.6527779943201],
                ],
                [
                    [-408.6770723897812, -125.6527779943201],
                    [-409.6770723897812, -125.6527779943201],
                    [-409.6770723897812, -31.652777994320104],
                    [-408.6770723897812, -31.652777994320104],
                    [-408.6770723897812, -16.652777994320104],
                    [-529.6770723897812, -16.652777994320104],
                    [-539.6770723897812, -16.652777994320104],
                    [-544.6770723897812, -16.652777994320104],
                    [-544.6770723897812, -138.6527779943201],
                    [-535.6770723897812, -138.6527779943201],
                    [-535.6770723897812, -140.6527779943201],
                    [-408.6770723897812, -140.6527779943201],
                    [-408.6770723897812, -125.6527779943201],
                ],
            ],
            3212814.8915988994,
        ),
    ],
)
def test_get_polygon_from_coordinates(coordinates, area_expected):
    polygon = get_polygon_from_coordinates(coordinates)
    assert polygon.area == area_expected


class TestAnnotationContract:
    """
    A test suite testing basic contract of the low-level annotation creation methods. Shows basic dependencies
    between different steps in the annotation creation.

    The annotations are created by the Editor app (slam/ui/pipeline) which has an inverted Y-axis orientation, where
    it is pointing downwards instead of upwards as in the classical Cartesian coordinate system. Additional steps in
    the pipeline, such as Classification, Splitting, etc show actually in the non-inverted Y-axis orientation. This
    requires manipulation of the annotation orientation, so that it is presented correctly in the pipeline.
    """

    @pytest.mark.parametrize("xmin,ymin,xmax,ymax", [(0, 0, 1, -3)])
    def test_get_parameters_of_minimum_rotated_rectangle_geometry_in_IV_quadrant(
        self, xmin, ymin, xmax, ymax
    ):
        """
        Given an input geometry with coordinates in IV quadrant in Cartesian plane
        When getting the annotation parameters of that geometry
        Then the output annotation must have following parameters:
            1. x == xmin, y == -ymax
            2. dy == xmax - xmin, dx == ymin - ymax
            3. angle == 360 - angle
        """
        polygon = box(xmin, ymin, xmax, ymax)

        annotation = get_parameters_of_minimum_rotated_rectangle(polygon)

        x, y, width, height, angle = annotation
        assert x == xmin
        assert y == -ymax
        assert width == ymin - ymax
        assert height == xmax - xmin

        assert angle == 270

    @pytest.mark.parametrize("xmin,ymin,xmax,ymax", [(0, 0, 3, 1)])
    def test_get_parameters_of_minimum_rotated_rectangle_geometry_in_I_quadrant(
        self, xmin, ymin, xmax, ymax
    ):
        """
        Given an input geometry with coordinates in I quadrant in Cartesian plane
        When getting the annotation parameters of that geometry
        Then the output annotation must have following parameters:
            1. x == xmax, y == ymin
            2. dx == xmax - xmin, dy == ymax - ymin
            3. angle == 360 - angle
        This means, that the set rotation axis is the upper-left corner of the polygon and rotated by 180 deg instead
        of having the rotation axis in the lower-left corner and keeping the rotation 0 deg
        """
        polygon = box(xmin, ymin, xmax, ymax)
        annotation = get_parameters_of_minimum_rotated_rectangle(polygon)
        x, y, width, height, angle = annotation
        assert x == xmax
        assert y == ymin
        assert width == xmax - xmin
        assert height == ymax - ymin
        assert angle == 180

    @pytest.mark.parametrize("xmin,ymin,xmax,ymax", [(-1, -3, 0, 0)])
    def test_get_parameters_of_minimum_rotated_rectangle_geometry_in_III_quadrant(
        self, xmin, ymin, xmax, ymax
    ):
        """
        Given an input geometry with coordinates in III quadrant in Cartesian plane
        When getting the annotation parameters of that geometry
        Then the output annotation must have following parameters:
            1. x == xmin, y == -ymin
            2. dx == ymax - ymin, dy == xmax - xmin
            3. angle == 360 - angle
        The initial axis for the rotation is again, the upper-left corner of the geometry and it is rotated such, that
        moving clockwise it lands in its target position. Then, it has its Y component of the rotation point inverted,
        because of the inverted-Y axis in the editor. So in other words, in order to have the annotation display in the
        Cartesian plane as rotated -90 deg with rotation axis (-1, 0), the editor convention requires it to set the
        rotation axis as the upper-left corner of the geometry in its equilibrium state (-1, -3), rotate it 270 deg
        and in the end invert the Y-component.
        """
        polygon = box(xmin, ymin, xmax, ymax)
        annotation = get_parameters_of_minimum_rotated_rectangle(polygon)
        x, y, width, height, angle = annotation
        assert x == xmin
        assert y == -ymin
        assert width == ymax - ymin
        assert height == xmax - xmin
        assert angle == 270

    @pytest.mark.parametrize("xmin,ymin,xmax,ymax", [(-3, -1, 0, 0)])
    def test_get_parameters_of_minimum_rotated_rectangle_geometry_in_II_quadrant(
        self, xmin, ymin, xmax, ymax
    ):
        """
        Given an input geometry with coordinates in II quadrant in Cartesian plane
        When getting the annotation parameters of that geometry
        Then the output annotation must have following parameters:
            1. x == xmax, y == -ymin
            2. dx == xmax - xmin, dy == ymax - ymin
            3. angle == 360 - angle
        The default rotation axis is lower-left (0, 1), because input geometry is being reversed to its equilibrium
        state, where its coordinates are [(0, 1), (0, 2), (2, 3), (3, 1), (0, 1)]. So to match the original placement
        of the geometry in the plane, it is rotated 180 deg using that rotation axis.
        """
        polygon = box(xmin, ymin, xmax, ymax)
        annotation = get_parameters_of_minimum_rotated_rectangle(polygon)
        x, y, width, height, angle = annotation
        assert x == xmax
        assert y == -ymin
        assert width == xmax - xmin
        assert height == ymax - ymin
        assert angle == 180

    @pytest.mark.parametrize(
        "rotation_from_horizontal,expected_annotation_rotation",
        [
            (0, 360),
            (-45, 405),
            (90, 270),
            (180, 180),
            (270, 90),
            (-30, 390),
            (30, 330),
            (360, 0),
        ],
    )
    def test_get_parameters_of_minimum_rotated_rectangle_should_shift_angle(
        self, mocker, rotation_from_horizontal, expected_annotation_rotation
    ):
        """
        The angle is shifted by an offset of -/+ 90 deg between the editor and the classical Cartesian plane. This
        test shows the relationship between the rotation_from_horizontal, which is the deviation of the annotation
        geometry from its equilibrium state and the expected_annotation_rotation, which needs to take this offset into
        account such that the annotation can be displayed properly in the editor.
        """
        polygon = box(0, 0, 3, 1)
        from dufresne.polygon import parameters_minimum_rotated_rectangle

        mocker.patch.object(
            parameters_minimum_rotated_rectangle,
            "get_angle_to_horizontal_axis",
            return_value=rotation_from_horizontal,
        )
        assert (
            expected_annotation_rotation
            == get_parameters_of_minimum_rotated_rectangle(polygon)[-1]
        )
