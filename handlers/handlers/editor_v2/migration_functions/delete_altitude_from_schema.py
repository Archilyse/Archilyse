from typing import Dict


def delete_altitude_from_schema(data: Dict) -> Dict:
    from handlers.editor_v2.schema import ReactPlannerVersions

    data["layers"]["layer-1"].pop("altitude", None)

    data["version"] = ReactPlannerVersions.V19.name
    return data
