from collections import Counter
from dataclasses import asdict

import ezdxf
import pytest

from brooks.models import SimLayout
from brooks.types import OpeningType
from brooks.visualization.brooks_plotter import BrooksPlotter
from brooks.visualization.floorplans.layouts.base_assetmanager_layout import (
    AssetManagerLayout,
)
from brooks.visualization.floorplans.layouts.constants import LayoutLayers
from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES
from handlers import PlanLayoutHandler
from handlers.db import ReactPlannerProjectsDBHandler
from tests.utils import assert_dxf_audit, assert_dxf_visual_differences


def test_assetmanager_layout_features():
    res = AssetManagerLayout.get_feature_layers(layout=SimLayout())
    assert LayoutLayers.FEATURES in res
    assert LayoutLayers.SANITARY_AND_KITCHEN in res
    assert LayoutLayers.STAIRS_ELEVATORS in res
    assert LayoutLayers.SHAFTS in res

    features_layer = res[LayoutLayers.FEATURES][0].keywords["include_feature_types"]
    sanitary_layer = res[LayoutLayers.SANITARY_AND_KITCHEN][0].keywords[
        "include_feature_types"
    ]
    stairs_layer = res[LayoutLayers.STAIRS_ELEVATORS][0].keywords[
        "include_feature_types"
    ]
    shafts_layer = res[LayoutLayers.SHAFTS][0].keywords["include_feature_types"]

    assert features_layer.difference(sanitary_layer) == features_layer
    assert features_layer.difference(stairs_layer) == features_layer
    assert features_layer.difference(shafts_layer) == features_layer

    assert stairs_layer.difference(sanitary_layer) == stairs_layer
    assert stairs_layer.difference(shafts_layer) == stairs_layer

    assert shafts_layer.difference(sanitary_layer) == shafts_layer


def test_generate_dxf_with_non_rectangular_separators(
    mocker,
    mocked_gcp_upload_bytes_to_bucket,
    fixtures_path,
    react_planner_non_rectangular_walls,
    default_plan_info,
):

    mocker.patch.object(
        ReactPlannerProjectsDBHandler,
        "get_by",
        return_value={"data": asdict(react_planner_non_rectangular_walls)},
    )

    layout = PlanLayoutHandler(plan_info={"id": 1, **default_plan_info}).get_layout(
        scaled=True, postprocessed=False
    )

    io_image = BrooksPlotter().generate_floor_plot(
        angle_north=90,
        floor_plan_layout=layout,
        unit_layouts=[],
        unit_ids=[],
        metadata={
            "street": "street name",
            "housenumber": 1,
            "level": 0,
            "zipcode": 8049,
            "city": "Zurich",
        },
        logo_content=None,
        language=SUPPORTED_LANGUAGES.EN,
        file_format=SUPPORTED_OUTPUT_FILES.DXF,
    )

    drawing = ezdxf.read(io_image)
    assert_dxf_audit(drawing=drawing)
    expected_file_name = "dxf_react_non_rectangles.jpeg"
    assert_dxf_visual_differences(
        drawing=drawing,
        expected_image_file=fixtures_path.joinpath(
            f"images/dxf_images/{expected_file_name}"
        ),
    )

    doors = [opening for opening in layout.openings if opening.type == OpeningType.DOOR]
    assert len(doors) == 1
    assert doors[0].footprint.area == pytest.approx(expected=1.0, abs=1e-6)

    actual_layers = Counter([e.dxf.layer for e in drawing.modelspace()])

    assert actual_layers == {
        "Titleblock": 32,
        "Doors": 5,
        "Walls": 6,
        "Room Polygons": 1,
        "0": 1,
    }
