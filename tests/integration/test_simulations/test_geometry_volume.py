import numpy as np
import pytest

from simulations.geometry import compute_volume
from tests.integration.utils import (
    generate_box,
    generate_icosphere,
    get_vtk_mesh_faces,
    get_vtk_mesh_vertices,
)
from tests.utils import quavis_test


@pytest.mark.skip
@quavis_test
def test_sphere():
    icosphere = generate_icosphere(1, np.array([0, 0, 0]), 4)

    # Add triangles of icosphere
    vertices = get_vtk_mesh_vertices(icosphere)
    faces = get_vtk_mesh_faces(icosphere)
    triangles = []
    for ai, bi, ci in faces:
        a, b, c = (
            vertices[ai],
            vertices[bi],
            vertices[ci],
        )
        triangles.append((a, b, c))

    vol = compute_volume(triangles)
    expected_vol = 4 / 3 * np.pi
    assert abs(expected_vol - vol) / expected_vol < 0.05


@pytest.mark.skip
@quavis_test
def test_l_shape():
    #  todo Needs to be fixed
    triangles = []

    box = generate_box((0, 0, 0), (1, 1, 1))
    vertices, faces = get_vtk_mesh_vertices(box), get_vtk_mesh_faces(box)
    for ai, bi, ci in faces:
        a, b, c = vertices[ai], vertices[bi], vertices[ci]
        triangles.append((a, b, c))

    box = generate_box((1, 0, 0), (2, 1, 1))
    vertices, faces = get_vtk_mesh_vertices(box), get_vtk_mesh_faces(box)
    for ai, bi, ci in faces:
        a, b, c = vertices[ai], vertices[bi], vertices[ci]
        triangles.append((a, b, c))

    box = generate_box((1, 1, 0), (2, 2, 1))
    vertices, faces = get_vtk_mesh_vertices(box), get_vtk_mesh_faces(box)
    for ai, bi, ci in faces:
        a, b, c = vertices[ai], vertices[bi], vertices[ci]
        triangles.append((a, b, c))

    vol = compute_volume(triangles)
    assert vol == pytest.approx(3)
