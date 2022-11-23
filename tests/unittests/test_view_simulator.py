import numpy as np
import pytest
from shapely.geometry import box

from brooks.models import SimArea
from common_utils.exceptions import LayoutTriangulationException
from simulations.view.meshes import GeoreferencingTransformation
from simulations.view.meshes.observation_points import get_observation_points_by_area


def test_layout_mesh_obs_points_raises_if_invalid_observation_points(acute_triangle):
    from common_utils.constants import (
        DEFAULT_GRID_BUFFER,
        DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
    )

    areas = {SimArea(footprint=acute_triangle)}

    with pytest.raises(LayoutTriangulationException):
        get_observation_points_by_area(
            areas=areas,
            georeferencing_parameters=GeoreferencingTransformation(),
            resolution=DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
            buffer=DEFAULT_GRID_BUFFER,
            obs_height=999,
            level_baseline=0,
        )


def test_layout_mesh_obs_points_should_return_valid_observation_points():
    from common_utils.constants import (
        DEFAULT_GRID_BUFFER,
        DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
    )

    areas = {SimArea(footprint=box(0, 0, 1, 1))}

    observation_points = get_observation_points_by_area(
        areas=areas,
        georeferencing_parameters=GeoreferencingTransformation(),
        resolution=DEFAULT_GRID_RESOLUTION_POTENTIAL_VIEW,
        buffer=DEFAULT_GRID_BUFFER,
        obs_height=999,
        level_baseline=0,
    )
    assert len(observation_points) == 1
    assert observation_points[0][1] == pytest.approx(
        np.array([[1.00e-01, 9.00e-01, 9.99e02]])
    )
