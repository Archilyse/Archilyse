from handlers.editor_v2.migration_functions.remove_enable_postprocessing import (
    remove_enable_postprocessing,
)
from handlers.editor_v2.migration_functions.remove_orphan_vertex import (
    remove_orphan_vertices,
)


def test_remove_enable_postprocessing():
    data = {"enablePostProcessing": True}
    updated_data = remove_enable_postprocessing(data=data)
    assert updated_data["version"] == "V16"
    assert "enablePostProcessing" not in updated_data


def test_remove_orphan_vertices():
    data = {
        "layers": {
            "layer-1": {
                "lines": {"a": {"vertices": ["1", "3"], "auxVertices": ["2", "4"]}},
                "vertices": {"1": None, "2": None, "3": None, "4": None, "5": None},
            }
        }
    }
    updated_data = remove_orphan_vertices(data=data)
    assert updated_data["version"] == "V17"
    assert set(updated_data["layers"]["layer-1"]["vertices"].keys()) == {
        "1",
        "2",
        "3",
        "4",
    }
