from math import isclose

import numpy as np
import pytest
from shapely.affinity import rotate, scale, translate
from shapely.geometry import Point, Polygon

from simulations.view.meshes import GeoreferencingTransformation

np.random.seed(5)


def test_apply_should_translate_x_y_z_vectors():
    elevation = 558.80639648
    translate_x = 1.23
    translate_y = 4.56
    vertices = [
        (2.59965212e06, 1.20025204e06, 4.45000000e00),
        (2.59965312e06, 1.20025204e06, 4.45000000e00),
        (2.59965162e06, 1.20025118e06, 4.45000000e00),
    ]
    gt = GeoreferencingTransformation()
    gt.set_translation(translate_x, translate_y, elevation)

    moved_vertices = gt.apply(vertices)

    expected_vertices = [
        (2599653.35, 1200256.6, 563.25639648),
        (2599654.35, 1200256.6, 563.25639648),
        (2599652.85, 1200255.74, 563.25639648),
    ]

    for i in range(3):
        for j in range(3):
            assert isclose(expected_vertices[i][j], moved_vertices[i][j], rel_tol=0.01)


def test_apply_should_translate_only_z_vector():
    elevation = 558.80639648
    vertices = [
        (2.59965212e06, 1.20025204e06, 4.45000000e00),
        (2.59965312e06, 1.20025204e06, 4.45000000e00),
        (2.59965162e06, 1.20025118e06, 4.45000000e00),
    ]
    gt = GeoreferencingTransformation()
    gt.set_translation(0, 0, elevation)
    moved_vertices = gt.apply(vertices)

    for i in range(3):
        assert isclose(vertices[i][1], moved_vertices[i][1], rel_tol=0.01)
        assert isclose(vertices[i][0], moved_vertices[i][0], rel_tol=0.01)
        assert isclose(moved_vertices[i][2], 563.25, rel_tol=0.01)


@pytest.mark.parametrize(
    "scaling_factor,pivot_x,pivot_y,xoff,yoff,zoff,rotation_angle",
    np.random.rand(20, 7).tolist(),
)
def test_georef_consistency(
    scaling_factor, pivot_x, pivot_y, xoff, yoff, zoff, rotation_angle
):
    georef_transform = GeoreferencingTransformation()
    georef_transform.set_scaling(pivot_x, pivot_y, scaling_factor)
    georef_transform.set_rotation(pivot_x, pivot_y, rotation_angle * 360)
    georef_transform.set_translation(xoff, yoff, zoff)

    coords_3d = np.random.rand(3, 3)
    coords_3d_transformed = georef_transform.apply(coords_3d)
    coords_3d_inverted = georef_transform.invert(coords_3d_transformed)

    polygon_3d = Polygon(coords_3d)
    polygon_3d_transformed = georef_transform.apply_shapely(polygon_3d)
    polygon_3d_inverted = georef_transform.invert_shapely(polygon_3d_transformed)

    # first we make sure our class does the same as shapely does when
    # we apply the functions individually
    polygon_3d_expected = scale(
        geom=polygon_3d,
        xfact=scaling_factor,
        yfact=scaling_factor,
        origin=Point(pivot_x, pivot_y),
    )
    polygon_3d_expected = rotate(
        geom=polygon_3d_expected,
        angle=rotation_angle * 360,
        origin=Point(pivot_x, pivot_y),
    )
    polygon_3d_expected = translate(
        geom=polygon_3d_expected,
        xoff=xoff,
        yoff=yoff,
        zoff=zoff,
    )

    np.testing.assert_allclose(
        np.array(polygon_3d_expected.exterior.coords),
        np.array(polygon_3d_transformed.exterior.coords),
    )

    # now we make sure that inversion works
    np.testing.assert_allclose(
        np.array(polygon_3d_inverted.exterior.coords),
        np.array(polygon_3d.exterior.coords),
    )

    # now we make sure that the methods apply and invert are equivalent
    # to apply_shapely and invert_shapely, respectively
    np.testing.assert_allclose(
        np.array(polygon_3d_transformed.exterior.coords)[:-1], coords_3d_transformed
    )
    np.testing.assert_allclose(
        np.array(polygon_3d_inverted.exterior.coords)[:-1], coords_3d_inverted
    )
