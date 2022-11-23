import pytest
from deepdiff import DeepDiff
from shapely import wkb
from shapely.geometry import Polygon, box

from common_utils.constants import SurroundingType
from surroundings.triangle_remover import TriangleRemover


@pytest.mark.parametrize(
    "footprint,triangles_out",
    [
        (
            box(1.0, 1.0, 5.0, 5.0),
            [
                [(0, 0, 0), (1, 1, 1 / 3), (1, 1, 0)],
                [(5, 5, 1 / 3), (6, 6, 0), (5, 5, 0)],
            ],
        ),
        (
            box(0.0, 0.0, 2.0, 2.0),
            # NOTE due to the used triangulation method TriangleRemover._handle_vertical_triangle
            # yields more triangles than necessary
            [
                [
                    (4.623505, 4.623505, 0.458831),
                    (6.0, 6.0, 0.0),
                    (4.585786, 4.585786, 0.0),
                ],
                [(3.0, 3.0, 1.0), (4.585786, 4.585786, 0.0), (2, 2, 0.0)],
                [(2, 2, 0.0), (2, 2, 2 / 3), (3.0, 3.0, 1.0)],
                [
                    (4.585786, 4.585786, 0.0),
                    (3.0, 3.0, 1.0),
                    (4.623505, 4.623505, 0.458831),
                ],
            ],
        ),
    ],
)
def test_handle_vertical_triangle(footprint, triangles_out):
    triangle = Polygon([(0.0, 0.0, 0.0), (3.0, 3.0, 1.0), (6.0, 6.0, 0.0)])
    triangles = list(
        TriangleRemover._handle_vertical_triangle(
            footprint=footprint, triangle=triangle
        )
    )
    assert not DeepDiff(
        triangles_out,
        triangles,
        significant_digits=4,
        ignore_numeric_type_changes=True,
        ignore_order=True,
    )


def test_handle_vertical_triangle_handles_2d_vertical_case():
    """
    This test is to make sure we can handle a vertical triangle
    which is vertical in 2d and 3d (all x values are identical)
    """
    footprint = box(-0.5, -0.5, 0.5, 0.5)
    triangle = Polygon([(0, 0, 0), (0, 1, 1), (0, 1, 0), (0, 0, 0)])
    triangles = list(
        TriangleRemover._handle_vertical_triangle(
            footprint=footprint, triangle=triangle
        )
    )
    expected_triangles = [
        [(0.0, 0.5, 0.5), (0.0, 0.5, 0.0), (0.0, 1.0, 0.0)],
        [(0.0, 1.0, 0.0), (0.0, 1.0, 1.0), (0.0, 0.5, 0.5)],
    ]
    assert triangles == expected_triangles


def test_handle_plane_triangle_excludes_contained_triangles():
    """
    This test is to make sure that plane triangles which are contained in our footprint are removed
    """
    triangle = Polygon([(0, 0, 0), (1, 1, 0), (2, 0, 0), (0, 0, 0)])
    footprint = box(*triangle.bounds)
    triangles = list(
        TriangleRemover._handle_plane_triangle(footprint=footprint, triangle=triangle)
    )
    assert triangles == []


def test_handle_vertical_triangle_excludes_contained_triangles():
    """
    This test is to make sure that vertical triangles which are contained in our footprint are removed
    """
    triangle = Polygon([(0, 0, 0), (1, 1, 1 / 3), (1, 1, 0)])
    footprint = box(*triangle.bounds)
    triangles = list(
        TriangleRemover._handle_vertical_triangle(
            footprint=footprint, triangle=triangle
        )
    )
    assert triangles == []


def test_handle_vertical_triangle_not_sorted_by_x():
    invalid_polygon: Polygon = wkb.loads(
        b"\x01\x03\x00\x00\x80\x01\x00\x00\x00\x04\x00\x00\x00\xe8\xfb\xa9\x81\x83\x19DA@`\xe5\x90\x8d\xfe2A\x00\xb6\xf3\xfd\xd4\xa4z@\x10-\xb2}\x83\x19DA\xa0\x9b\xc4\xa0\x8d\xfe2A\x007\x89A`\xa3z@\xf8S\xe3\x85\x83\x19DA\x00\x00\x00\x80\x8d\xfe2A\x007\x89A`\xa3z@\xe8\xfb\xa9\x81\x83\x19DA@`\xe5\x90\x8d\xfe2A\x00\xb6\xf3\xfd\xd4\xa4z@"
    )  # actual triangle from production data
    footprint = box(2634503, 1244813.5, 2634503.046, 1244813.627999999)

    triangles = list(
        TriangleRemover._handle_vertical_triangle(
            footprint=footprint, triangle=invalid_polygon
        )
    )
    assert triangles == [
        [
            (2634502.982000001, 1244813.6279999986, 426.2109999999957),
            (2634503.0, 1244813.5920000002, 426.26383870826226),
            (2634503.0, 1244813.5920000002, 426.2109999999957),
        ]
    ]


def test_exclude_triangles_production_exception(mocker):
    """
    This test is based on an exception encountered in production, what makes the invalid polygon special is that
    it is invalid but calling .intersection() with the footprint returns true which is why it was originally handled as
    a plane polygon even though it is a vertical polygon (which resulted in an exception)
    """
    # actual triangle from production data, had to use wkb as using wkt was resulting in a
    # slightly different polygon which did not replicate that exact case
    invalid_polygon: Polygon = wkb.loads(
        b"\x01\x03\x00\x00\x80\x01\x00\x00\x00\x04\x00\x00\x00\xe8\xfb\xa9\x81\x83\x19DA@`\xe5\x90\x8d\xfe2A\x00\xb6\xf3\xfd\xd4\xa4z@\x10-\xb2}\x83\x19DA\xa0\x9b\xc4\xa0\x8d\xfe2A\x007\x89A`\xa3z@\xf8S\xe3\x85\x83\x19DA\x00\x00\x00\x80\x8d\xfe2A\x007\x89A`\xa3z@\xe8\xfb\xa9\x81\x83\x19DA@`\xe5\x90\x8d\xfe2A\x00\xb6\xf3\xfd\xd4\xa4z@"
    )
    # actual footprint from production data
    footprint: Polygon = wkb.loads(
        b'\x01\x03\x00\x00\x00\x01\x00\x00\x00\x0b\x00\x00\x00\x12t\xfc\xc6\x85\x19DA]\xf42\xfc\x89\xfe2A\xf3o\xa6x\x83\x19DA\xa7\x7f\x9f\xa3\x87\xfe2A2z}\xbc\x83\x19DA}#\x10\xa1\x86\xfe2Aw\x86\x7f\xc7\x81\x19DA\xc6\\\xc4\xa9\x84\xfe2A\x10"D\xb8\x7f\x19DAh\xcb\xd6\xac\x8c\xfe2A`\x84T\xf0\x80\x19DA\xa0%;\xe8\x8d\xfe2A\x9ac\xa4m\x80\x19DA\x94\xfa\xb3\xf1\x8f\xfe2A\xa9\xe49\x81\x83\x19DAjJA\t\x93\xfe2AjY\xcdI\x84\x19DAQoG\xea\x8f\xfe2A\xe2\x17m\x94\x84\x19DA\xb6\xacQ\xc1\x8e\xfe2A\x12t\xfc\xc6\x85\x19DA]\xf42\xfc\x89\xfe2A'
    )
    vertical_triangle_handler_spy = mocker.spy(
        TriangleRemover, "_handle_vertical_triangle"
    )

    triangles = list(
        TriangleRemover.exclude_2d_intersections(
            triangles=[
                (SurroundingType.BUILDINGS, invalid_polygon.exterior.coords[:3])
            ],
            footprint=footprint,
        )
    )

    assert vertical_triangle_handler_spy.call_count == 1
    assert triangles == []


@pytest.mark.parametrize(
    "footprint, expected_triangles",
    [
        (box(0, 0, 1, 1), [[(1, 1, 1), (2, 0, 0), (1, 0, 0)]]),
        (
            box(0, 0, 0.5, 0.5),
            [
                [(0.5, 0, 0), (0.5, 0.5, 0.5), (2, 0, 0)],
                [(1, 1, 1), (2, 0, 0), (0.5, 0.5, 0.5)],
            ],
        ),
    ],
)
def test_handle_plane_triangle(footprint, expected_triangles):
    triangle = Polygon([(0, 0, 0), (1, 1, 1), (2, 0, 0)])

    triangles = list(
        TriangleRemover._handle_plane_triangle(triangle=triangle, footprint=footprint)
    )

    assert not DeepDiff(
        expected_triangles,
        triangles,
        significant_digits=5,
        ignore_numeric_type_changes=True,
        ignore_order=True,
    )
