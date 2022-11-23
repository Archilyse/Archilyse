import pytest
from shapely.geometry import box

from brooks.types import AnnotationType


@pytest.fixture
def walls_vertical_aligned():
    return {
        "1": box(0, 0, 2, 4),
        "2": box(0, 4, 2, 8),
    }


@pytest.fixture
def walls_cross_shaped():
    return {
        AnnotationType.WALL.value: [
            [1, 2, 1, 4, 90],
            [-2, 0, 1, 4, 0],
        ]
    }


@pytest.fixture
def walls_complex_case():
    aa_prime = [11.0, 1.0, 9.0, 2.0, 270.0]
    bb_prime = [12.0, -5.0, 4.0, 1.0, 180.0]
    c = [10.0, 6.0, 6.0, 4.0, 270.0]
    dd_prime = [16.0, 2.0, 2.5, 1.0, 180.0]
    return {AnnotationType.WALL.value: [aa_prime, bb_prime, c, dd_prime]}
