import pytest
from shapely.affinity import rotate
from shapely.geometry import box

from simulations.rectangulator.rectangle_dims_handler import RectangleDimsHandler


@pytest.mark.parametrize(
    "rect, angle",
    [
        (box(0.0, 0.0, 10.0, 10.0), 0),
        (box(0.0, 0.0, 10.0, 8.0), 0),
        (box(0.0, 0.0, 10.0, 8.0), 5),
        (box(0.0, 0.0, 10.0, 8.0), 20),
        (box(0.0, 0.0, 10.0, 8.0), 90),
        (box(0.0, 0.0, 10.0, 8.0), 95),
        (box(0.0, 0.0, 10.0, 8.0), 106),
        (box(0.0, 0.0, 10.0, 8.0), 180),
        (box(0.0, 0.0, 10.0, 8.0), 185),
        (box(0.0, 0.0, 10.0, 8.0), -15),
        (box(0.0, 0.0, 10.0, 10.0), 56),
    ],
)
def test_box_pol_to_dims_to_pol(rect, angle):
    rect = rotate(rect, angle)
    dims = RectangleDimsHandler.polygon_to_dims(rect)
    rect_recovered = RectangleDimsHandler.dims_to_polygon(dims)
    assert rect.intersection(rect_recovered).area == pytest.approx(rect.area)
