from typing import Dict


def remove_orphan_vertices(data: Dict) -> Dict:
    from handlers.editor_v2.schema import ReactPlannerVersions

    referenced_vertices = set()
    for line in data["layers"]["layer-1"]["lines"].values():
        referenced_vertices.update(line["vertices"] + line["auxVertices"])

    non_referenced_vertices = set(data["layers"]["layer-1"]["vertices"]).difference(
        referenced_vertices
    )
    for non_referenced_vertex in non_referenced_vertices:
        del data["layers"]["layer-1"]["vertices"][non_referenced_vertex]

    data["version"] = ReactPlannerVersions.V17.name
    return data
