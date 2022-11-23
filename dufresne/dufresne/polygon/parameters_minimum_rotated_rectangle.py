from math import atan2, pi
from typing import List, Tuple, Union

from shapely.affinity import rotate
from shapely.geometry import MultiPolygon, Point, Polygon


def get_parameters_of_minimum_rotated_rectangle(
    polygon: Union[MultiPolygon, Polygon],
    rotation_axis_convention: str = "upper_left",
    return_annotation_convention: bool = True,
    align_short_side_to_x_axis: bool = False,
) -> List[float]:
    """
    Returns a minimum rotated rectangle with annotation parametrization depending on the use case:
    1. If the resulting rectangle still needs to be processed in the backend, it will not have its Y-axis inverted
    2. If the resulting rectangle needs to fulfill the Editor requirements, it will have its Y-axis inverted and
        its angle will be a result of subtraction of 360 from the angle to X-axis.

    rotation_axis: the rotation point for the annotation rectangle on the lower left or upper left edge. The
        rotation axis is always determined after rotating the geometry to its equilibrium state, such that its
        longest edge is lined-up parallel to the X-axis.
        If align_short_side_to_x_axis is set to True, the short side is lined up parallel to the X-axis instead.
            This is necessary to be able to correctly represent elements in the react planner (see
            IfcToReactPlannerMapper._infer_angle_from_walls)
    return_annotation_convention: if True the angle is returned clockwise and the y coordinate inverted

    returns [x, y, dx, dy, angle] where:
    x: rotation axis x coordinate
    y: rotation axis y coordinate
    dx: x-extension of the axis aligned bounding box
    dy: y-extension of the axis aligned bounding box
    angle: rotation angle of the resulting annotation rectangle in degrees from its equilibrium state where
        negative values are counterclockwise and positive values are clockwise.
    """
    bounding_box = polygon.minimum_rotated_rectangle
    coords = [coord for coord in bounding_box.exterior.coords]

    i, j = (
        get_indexes_long_side(coords=coords)
        if not align_short_side_to_x_axis
        else get_indexes_short_side(coords=coords)
    )
    angle = get_angle_to_horizontal_axis(p1=coords[i], p2=coords[j])

    rotation_axis = get_rotation_axis(
        coords=coords,
        angle=angle,
        axis_index=i,
        rotation_axis_convention=rotation_axis_convention,
    )

    # offset the bounding box to the 'equilibrium state' such that it is aligned with X-axis
    axis_aligned_bounding_box = rotate(
        geom=bounding_box, angle=-angle, origin=rotation_axis
    )

    dx, dy = (
        abs(axis_aligned_bounding_box.bounds[0] - axis_aligned_bounding_box.bounds[2]),
        abs(axis_aligned_bounding_box.bounds[1] - axis_aligned_bounding_box.bounds[3]),
    )
    if return_annotation_convention:
        return [rotation_axis.x, -rotation_axis.y, dx, dy, 360 - angle]
    return [rotation_axis.x, rotation_axis.y, dx, dy, angle]


def get_indexes_long_side(coords: List[Tuple[float, float]]) -> Tuple[int, int]:
    if Point(coords[0]).distance(Point(coords[1])) > Point(coords[1]).distance(
        Point(coords[2])
    ):
        return 0, 1
    return 1, 2


def get_indexes_short_side(coords: List[Tuple[float, float]]) -> Tuple[int, int]:
    if Point(coords[0]).distance(Point(coords[1])) > Point(coords[1]).distance(
        Point(coords[2])
    ):
        return 1, 2
    return 0, 1


def get_angle_to_horizontal_axis(
    p1: Tuple[float, float], p2: Tuple[float, float]
) -> float:
    return (
        atan2(
            (p2[1] - p1[1]),
            (p2[0] - p1[0]),
        )
        * 360
        / (2 * pi)
    )


def get_rotation_axis(
    coords: List[Tuple[float, float]],
    angle: float,
    axis_index: int,
    rotation_axis_convention: str,
) -> Point:

    axis_alligned_coords = [
        rotate(geom=Point(coord), angle=-angle, origin=coords[axis_index])
        for coord in coords
    ]
    xmin, ymin, ymax = (
        min([coord.x for coord in axis_alligned_coords]),
        min([coord.y for coord in axis_alligned_coords]),
        max([coord.y for coord in axis_alligned_coords]),
    )

    upper_left_point = Point(xmin, ymax)
    lower_left_point = Point(xmin, ymin)

    current_rotation_axis = Point(coords[axis_index])

    if current_rotation_axis.distance(
        upper_left_point
    ) > current_rotation_axis.distance(lower_left_point):
        return (
            Point(coords[axis_index + 3])
            if rotation_axis_convention == "upper_left"
            else current_rotation_axis
        )
    return (
        current_rotation_axis
        if rotation_axis_convention == "upper_left"
        else Point(coords[axis_index + 3])
    )
