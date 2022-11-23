from typing import Dict


def remove_enable_postprocessing(data: Dict) -> Dict:
    from handlers.editor_v2.schema import ReactPlannerVersions

    data.pop("enablePostProcessing", None)

    data["version"] = ReactPlannerVersions.V16.name
    return data
