import random

import numpy as np
import pytest

from simulations.view import ViewWrapper
from tests.integration.utils import (
    generate_icosphere,
    get_vtk_mesh_faces,
    get_vtk_mesh_vertices,
)
from tests.utils import quavis_test


@pytest.mark.vtk
@quavis_test
def test_volume_sphere():
    random.seed(42)

    radius = 1
    subdivision = 5
    icosphere = generate_icosphere(radius, np.array([0, 0, 0]), subdivision)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere with random groups
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    faces = get_vtk_mesh_faces(mesh=icosphere)
    for a, b, c in faces:
        wrapper.add_triangles([[vertices[a], vertices[b], vertices[c]]])

    # One observation point in center
    wrapper.add_observation_point((0, 0, 0))
    result = wrapper.run()

    # Compute mean error
    expected_volume = 4 / 3 * np.pi * radius**3
    volume = result[0]["simulations"]["volume"]
    relative_error = abs(expected_volume - volume) / expected_volume

    assert relative_error < 0.01


@pytest.mark.vtk
@quavis_test
def test_volume_big_sphere():
    random.seed(42)

    radius = 9999
    subdivision = 5
    icosphere = generate_icosphere(radius, np.array([0, 0, 0]), subdivision)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere with random groups
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    faces = get_vtk_mesh_faces(mesh=icosphere)
    for a, b, c in faces:
        wrapper.add_triangles([[vertices[a], vertices[b], vertices[c]]])

    # One observation point in center
    wrapper.add_observation_point((0, 0, 0))
    result = wrapper.run()

    # Compute mean error
    expected_volume = 4 / 3 * np.pi * radius**3
    volume = result[0]["simulations"]["volume"]
    relative_error = abs(expected_volume - volume) / expected_volume

    assert relative_error < 0.01


@pytest.mark.vtk
@quavis_test
def test_volume_sphere_with_holes():
    random.seed(42)

    radius = 1
    subdivision = 5
    icosphere = generate_icosphere(radius, np.array([0, 0, 0]), subdivision)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere with random groups
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    faces = get_vtk_mesh_faces(mesh=icosphere)
    num_removed = 0
    for a, b, c in faces:
        if random.choice([True, False, True]):
            num_removed += 1
            continue

        wrapper.add_triangles([[vertices[a], vertices[b], vertices[c]]])

    # One observation point in center
    wrapper.add_observation_point((0, 0, 0))
    result = wrapper.run()

    # Compute mean error
    expected_volume = (
        4 / 3 * np.pi * radius**3 * (faces.shape[0] - num_removed) / faces.shape[0]
    )
    volume = result[0]["simulations"]["volume"]
    relative_error = abs(expected_volume - volume) / expected_volume

    assert relative_error < 0.01
