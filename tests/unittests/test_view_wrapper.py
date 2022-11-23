import numpy as np
import pytest

from simulations.view.view_wrapper import ViewWrapper


def test_add_triangles():
    v1 = [0, 1, 2]
    v2 = [3, 4, 5]
    v3 = [6, 7, 8]
    v4 = [2, 1, 0]
    v5 = [5, 4, 3]
    v6 = [8, 7, 6]

    triangles = np.array([[v1, v2, v3], [v4, v5, v6]])
    wrapper = ViewWrapper()
    wrapper.add_observation_point([0, 0, 0])
    wrapper.add_triangles(triangles)
    quavis_input = wrapper.generate_input(run_area=True, run_sun=True, run_volume=True)

    positions = quavis_input["quavis"]["sceneObjects"][0]["positions"]
    indices = quavis_input["quavis"]["sceneObjects"][0]["indices"]

    assert len(positions) == 2 * 3 * 3
    assert len(indices) == 2 * 3

    actual_vertices = np.array(positions).reshape(-1, 3)
    for idx, vertex_indices in enumerate(np.array(indices).reshape(-1, 3)):
        actual_triangle = np.take(actual_vertices, vertex_indices, axis=0).flatten()
        expected_triangle = triangles[idx].flatten()
        assert pytest.approx(actual_triangle) == expected_triangle


def test_add_triangles_repititions():
    """tests that each vertex is only stored once if in the same group"""
    v1 = [0, 1, 2]
    v2 = [3, 4, 5]
    v3 = [6, 7, 8]
    v4 = [2, 1, 0]

    triangles = np.array([[v1, v2, v3], [v1, v2, v4]])
    wrapper = ViewWrapper()
    wrapper.add_observation_point([0, 0, 0])
    wrapper.add_triangles(triangles)
    quavis_input = wrapper.generate_input(run_area=True, run_sun=True, run_volume=True)

    positions = quavis_input["quavis"]["sceneObjects"][0]["positions"]
    indices = quavis_input["quavis"]["sceneObjects"][0]["indices"]

    assert len(positions) == 4 * 3
    assert len(indices) == 2 * 3

    actual_vertices = np.array(positions).reshape(-1, 3)
    for idx, vertex_indices in enumerate(np.array(indices).reshape(-1, 3)):
        actual_triangle = np.take(actual_vertices, vertex_indices, axis=0).flatten()
        expected_triangle = triangles[idx].flatten()
        assert pytest.approx(actual_triangle) == expected_triangle


def test_add_triangles_repitions_in_groups():
    """tests that duplicate vertices are stored multiple times w/ different
    colors when in different groups
    """
    v1 = [0, 1, 2]
    v2 = [3, 4, 5]
    v3 = [6, 7, 8]
    v4 = [2, 1, 0]

    triangles_group_1 = np.array([[v1, v2, v3]])
    triangles_group_2 = np.array([[v1, v2, v4]])
    wrapper = ViewWrapper()
    wrapper.add_observation_point([0, 0, 0])

    wrapper.add_triangles(triangles_group_1, group="a")
    wrapper.add_triangles(triangles_group_2, group="b")
    quavis_input = wrapper.generate_input(run_area=True, run_sun=True, run_volume=True)

    positions = quavis_input["quavis"]["sceneObjects"][0]["positions"]
    indices = quavis_input["quavis"]["sceneObjects"][0]["indices"]
    colors = quavis_input["quavis"]["sceneObjects"][0]["vertexData"]

    assert len(positions) == 2 * 3 * 3
    assert len(indices) == 2 * 3
    assert len(colors) == 2 * 3 * 4

    actual_vertices = np.array(positions).reshape(-1, 3)
    actual_colors = np.array(colors).reshape(-1, 4)
    actual_triangles = np.take(
        actual_vertices, np.array(indices).reshape(-1, 3), axis=0
    )
    actual_triangle_colors = np.take(
        actual_colors, np.array(indices).reshape(-1, 3), axis=0
    )

    expected_triangles = np.vstack([triangles_group_1, triangles_group_2])
    expected_num_colors = 2

    actual_colors = set()
    for triangle_colors in actual_triangle_colors:
        colors_in_triangle = set([tuple(c.tolist()) for c in triangle_colors])
        assert len(colors_in_triangle) == 1
        actual_colors.add(colors_in_triangle.pop())

    assert len(actual_colors) == expected_num_colors
    assert (
        pytest.approx(expected_triangles.flatten().tolist())
        == actual_triangles.flatten().tolist()
    )
