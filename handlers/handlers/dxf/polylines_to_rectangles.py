from typing import List

from func_timeout import FunctionTimedOut, func_timeout
from shapely.affinity import scale
from shapely.geometry import LineString, Polygon, mapping
from shapely.ops import nearest_points, orient, unary_union

from common_utils.constants import (
    IS_RECTANGLE_THRESHOLD_IN_CM2,
    SKELETONIZE_TIMEOUT_IN_SECS,
)
from common_utils.logger import logger
from dufresne.linestring_add_width import add_width_to_linestring_improved
from dufresne.skeleton import skeletonize
from handlers.dxf.dxf_constants import (
    NEGLECTABLE_SKELETON_LINE_LENGTH_IN_CM,
    NEGLECTABLE_SKELETON_LINE_WIDTH_IN_CM,
)


def rectangles_from_skeleton(geometry: Polygon) -> List[Polygon]:
    if (
        abs(geometry.area - geometry.minimum_rotated_rectangle.area)
        < IS_RECTANGLE_THRESHOLD_IN_CM2
    ):
        return [
            geometry.minimum_rotated_rectangle
        ]  # This needs to be done as the skeleton approach doesn't work for a square
    geometry = orient(geom=geometry, sign=-1.0)
    try:
        skeleton = func_timeout(
            timeout=SKELETONIZE_TIMEOUT_IN_SECS,
            func=skeletonize,
            args=(
                geometry.exterior.coords[:],
                [interior.coords[:] for interior in geometry.interiors],
            ),
        )

    except FunctionTimedOut:
        logger.error(
            f"skeletonize not successful for polygon: \n {mapping(geometry)} in {SKELETONIZE_TIMEOUT_IN_SECS}s"
        )
        return []
    rectangles = []
    for arc in skeleton:
        sub_lines = [
            LineString([(arc.source.x, arc.source.y), (sink.x, sink.y)])
            for sink in arc.sinks
        ]
        sub_lines = [line for line in sub_lines if line.length]

        for selected_line in sub_lines:
            width = (
                max(
                    [
                        point.distance(selected_line)
                        for point in nearest_points(selected_line, geometry.exterior)
                    ]
                )
                * 2
            )

            # Extends the lines to its width (size) on each side to fill the missing gap
            if (
                not selected_line.length > NEGLECTABLE_SKELETON_LINE_LENGTH_IN_CM
                or not width
                or width < NEGLECTABLE_SKELETON_LINE_WIDTH_IN_CM
            ):
                continue
            scale_factor = width / selected_line.length + 1
            selected_line = scale(
                geom=selected_line,
                xfact=scale_factor,
                yfact=scale_factor,
                origin="center",
            )

            polygon = add_width_to_linestring_improved(line=selected_line, width=width)

            rectangles.append(polygon)

    return filtered_rectangles(original_geometry=geometry, rectangles=rectangles)


def filtered_rectangles(
    original_geometry: Polygon, rectangles: List[Polygon]
) -> List[Polygon]:
    """
    The original geometry gets split into rectangles but some of these rectangles are so small and or redundant that
    we need to filter them out
    """
    # we remove each rectangle from the initial geometry, and if the difference doesn't increase it means
    # it is redundant
    existing_difference = original_geometry.difference(unary_union(rectangles)).area
    rectangles_indexed = {
        i: rectangle
        for i, rectangle in enumerate(sorted(rectangles, key=lambda x: x.area))
    }
    to_remove = set()
    for i in rectangles_indexed.keys():
        all_but_rectangle = unary_union(
            [x for j, x in rectangles_indexed.items() if j != i and j not in to_remove]
        )
        difference = original_geometry.difference(all_but_rectangle)
        if difference.area - existing_difference < 1:
            to_remove.add(i)
            existing_difference = difference.area

    return [x for i, x in rectangles_indexed.items() if i not in to_remove]
