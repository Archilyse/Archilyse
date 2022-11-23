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
def test_area_by_group_uniformly_random():
    random.seed(42)

    num_groups = 16
    icosphere = generate_icosphere(1000, np.array([0, 0, 0]), 5)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere with random groups
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    faces = get_vtk_mesh_faces(mesh=icosphere)
    grp_counts = [0 for x in range(num_groups)]
    for a, b, c in faces:
        grp = random.randint(0, num_groups - 1)
        grp_counts[grp] += 1
        wrapper.add_triangles(
            [[vertices[a], vertices[b], vertices[c]]],
            group=str(grp),
        )

    # One observation point in center
    wrapper.add_observation_point((0, 0, 0))
    result = wrapper.run()

    # Compute mean error
    mean_error = 0
    for grp, grp_count in enumerate(grp_counts):
        area = result[0]["simulations"]["area_by_group"][str(grp)]
        percent = area / (4 * np.pi)
        expected_percent = grp_count / faces.shape[0]
        mean_error += np.abs(percent - expected_percent)

    mean_error /= num_groups

    assert mean_error < 0.01


@pytest.mark.vtk
@quavis_test
def test_area_by_group_uniformly_random_translated():
    random.seed(42)

    num_groups = 16
    icosphere = generate_icosphere(1000, np.array([1000, 1000, 1000]), 5)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere with random groups
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    faces = get_vtk_mesh_faces(mesh=icosphere)
    grp_counts = [0 for x in range(num_groups)]
    for a, b, c in faces:
        grp = random.randint(0, num_groups - 1)
        grp_counts[grp] += 1
        wrapper.add_triangles(
            [[vertices[a], vertices[b], vertices[c]]],
            group=str(grp),
        )

    # One observation point in center
    wrapper.add_observation_point((1000, 1000, 1000))
    result = wrapper.run()

    # Compute mean error
    mean_error = 0
    for grp, grp_count in enumerate(grp_counts):
        area = result[0]["simulations"]["area_by_group"][str(grp)]
        percent = area / (4 * np.pi)
        expected_percent = grp_count / faces.shape[0]
        mean_error += np.abs(percent - expected_percent)

    mean_error /= num_groups

    assert mean_error < 0.01


@pytest.mark.vtk
@quavis_test
def test_area_by_group_non_uniformly_random():
    np.random.seed(42)

    num_groups = 16
    icosphere = generate_icosphere(1000, np.array([0, 0, 0]), 5)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of icosphere with random groups (binomial sampling)
    vertices = get_vtk_mesh_vertices(mesh=icosphere)
    faces = get_vtk_mesh_faces(mesh=icosphere)
    grp_counts = [0 for x in range(num_groups)]
    for a, b, c in faces:
        grp = np.random.binomial(num_groups, 0.3)
        grp_counts[grp] += 1
        wrapper.add_triangles(
            [[vertices[a], vertices[b], vertices[c]]],
            group=str(grp),
        )

    # One observation point in center
    wrapper.add_observation_point((0, 0, 0))
    result = wrapper.run()

    # Compute mean error
    mean_error = 0
    for grp, grp_count in enumerate(grp_counts):
        if str(grp) not in result[0]["simulations"]["area_by_group"]:
            continue

        area = result[0]["simulations"]["area_by_group"][str(grp)]
        percent = area / (4 * np.pi)
        expected_percent = grp_count / faces.shape[0]
        mean_error += np.abs(percent - expected_percent)

    mean_error /= num_groups

    assert mean_error < 0.01


@pytest.mark.vtk
@quavis_test
def test_area_by_group_view_blocked_uniformly_random():
    random.seed(42)

    small_icosphere = generate_icosphere(1, np.array([0, 0, 0]), 5)
    small_icosphere_vertices = get_vtk_mesh_vertices(mesh=small_icosphere)
    small_icosphere_faces = get_vtk_mesh_faces(mesh=small_icosphere)

    big_icosphere = generate_icosphere(1.5, np.array([0, 0, 0]), 4)
    big_icosphere_vertices = get_vtk_mesh_vertices(mesh=big_icosphere)
    big_icosphere_faces = get_vtk_mesh_faces(mesh=big_icosphere)
    wrapper = ViewWrapper(resolution=128)

    # Add triangles of small icosphere with one group
    # randomly remove patches
    num_unblocked = 0
    for a, b, c in small_icosphere_faces:
        if random.choice([True, False]):
            num_unblocked += 1
            continue

        wrapper.add_triangles(
            [
                [
                    small_icosphere_vertices[a],
                    small_icosphere_vertices[b],
                    small_icosphere_vertices[c],
                ]
            ],
            group="small",
        )

    # Add triangles of big icosphere with other group
    for a, b, c in big_icosphere_faces:
        wrapper.add_triangles(
            [
                [
                    big_icosphere_vertices[a],
                    big_icosphere_vertices[b],
                    big_icosphere_vertices[c],
                ]
            ],
            group="big",
        )

    # One observation point in center
    wrapper.add_observation_point((0, 0, 0))
    result = wrapper.run()

    # Compute relative errors
    expected_area_big_icosphere = (
        4 * np.pi / small_icosphere_faces.shape[0] * num_unblocked
    )
    area_big_icosphere = result[0]["simulations"]["area_by_group"]["big"]
    relative_error_big_icosphere = abs(
        (expected_area_big_icosphere - area_big_icosphere) / expected_area_big_icosphere
    )
    assert relative_error_big_icosphere < 0.01

    expected_area_small_icosphere = 4 * np.pi - expected_area_big_icosphere
    area_small_icosphere = result[0]["simulations"]["area_by_group"]["small"]
    relative_error_small_icosphere = abs(
        (expected_area_small_icosphere - area_small_icosphere)
        / expected_area_small_icosphere
    )

    assert relative_error_small_icosphere < 0.01
