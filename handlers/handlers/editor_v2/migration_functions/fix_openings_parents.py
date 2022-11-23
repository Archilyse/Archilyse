from typing import Dict

from shapely.geometry import Polygon


def fix_opening_parents(data: Dict) -> Dict:
    from handlers.editor_v2.schema import ReactPlannerVersions

    lines = data["layers"]["layer-1"]["lines"]
    holes = data["layers"]["layer-1"]["holes"]
    for hole in holes.values():
        parent_polygon = Polygon(lines[hole["line"]]["coordinates"][0])
        hole_polygon = Polygon(hole["coordinates"][0])
        if not hole_polygon.intersects(parent_polygon):
            max_intersection = 0
            best_candidate = hole["line"]
            for line in lines.values():
                candidate_polygon = Polygon(line["coordinates"][0])
                if candidate_polygon.intersects(hole_polygon):
                    intersection_area = candidate_polygon.intersection(
                        hole_polygon
                    ).area
                    if intersection_area > max_intersection:
                        max_intersection = intersection_area
                        best_candidate = line["id"]
            hole["line"] = best_candidate

    data["version"] = ReactPlannerVersions.V18.name
    return data
