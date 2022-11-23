from typing import Dict, Tuple

from brooks.types import SIACategory
from brooks.visualization.floorplans.patches.collection import DimensionLinePatch

from .base_figure_style import FigureStyle
from .patches.door import EntranceDoorFlagPatch
from .patches.orientation import (
    NorthIndicatorPatch,
    OrientationCirclePatch,
    OrientationLinePatch,
    OrientationPatchCollection,
)


class AssetManagerUnitStyle(FigureStyle):
    """Style describing the main unit plot"""

    ORIENTATION_PATCH_STYLE = dict(alpha=0)
    IGNORE_CLIPPING: Tuple = (
        DimensionLinePatch,
        EntranceDoorFlagPatch,
    )
    AREA_PATCH_STYLE = dict(fill=False, linewidth=0)
    ADD_ROOM_TEXTS = True
    ADD_DIMENSION_TEXTS = False
    DIMENSION_PATH_STYLE = dict(
        facecolor="black", edgecolor="black", aa=True, visible=False
    )


class AssetManagerFloorStyle(AssetManagerUnitStyle):
    """Style describing the main plot for Full FLOOR"""

    ROOM_TEXT_STYLE: Dict = dict(
        size=4,
        name=FigureStyle.LIVIT_FONT,
        color="black",
        verticalalignment="center",
        horizontalalignment="center",
    )


class PostFloorStyle(FigureStyle):
    TEXT_ALIGNMENT = "center"
    FONT_WEIGHT = "heavy"
    FONT_COLOR = "red"
    FACE_COLOR = "#FFFFFF"
    DEFAULT_FONT_SIZE = 6
    AREA_PATCH_ALPHA = 0.8
    IMAGE_RESOLUTION = 300
    FONT_SCALE_FACTOR = 81e-5


class AssetManagerFloorOverviewStyle(FigureStyle):
    """Style describing the entire floor in the overview"""

    DIMENSION_PATH_STYLE = dict(alpha=0)
    IGNORE_CLIPPING: Tuple = (
        NorthIndicatorPatch,
        OrientationCirclePatch,
        OrientationLinePatch,
        OrientationPatchCollection,
    )
    AREA_PATCH_STYLE = dict(
        visible=False,
    )  # assetmanager red
    WINDOW_PATCH_STYLE = dict(visible=False)
    SHAFT_FEATURE_PATCH_STYLE = dict(visible=False)
    DOOR_STEP_PATCH_STYLE = dict(visible=False)
    FEATURE_PATCH_STYLE = dict(visible=False)
    ENTRANCE_DOOR_FLAG_STYLE = dict(visible=False)


class AssetManagerHighlightStyle(FigureStyle):
    """Style describing the highlighted unit in the overview"""

    IGNORE_CLIPPING: Tuple[()] = ()
    DIMENSION_PATH_STYLE = dict(alpha=0)
    ORIENTATION_PATCH_STYLE = dict(alpha=0)
    AREA_PATCH_STYLE = dict(
        facecolor=(238 / 255, 150 / 255, 150 / 255), edgecolor=None, alpha=1.0
    )  # assetmanager red
    WALL_PATCH_STYLE = dict(visible=False)
    RAILING_PATCH_STYLE = dict(visible=False)
    WINDOW_PATCH_STYLE = dict(visible=False)
    SHAFT_FEATURE_PATCH_STYLE = dict(visible=False)
    DOOR_STEP_PATCH_STYLE = dict(visible=False)
    FEATURE_PATCH_STYLE = dict(visible=False)
    ENTRANCE_DOOR_FLAG_STYLE = dict(visible=False)


class DXFUnitStyle(AssetManagerUnitStyle):
    """Style describing the main unit plot"""

    AREA_PATCH_STYLE: Dict = dict(fill=False, linewidth=0.1)
    WALL_PATCH_STYLE = dict(
        facecolor="black", aa=True, edgecolor="black", linewidth=0.1
    )
    RAILING_PATCH_STYLE = dict(edgecolor="black", linewidth=0.1, aa=True, fill=False)
    USE_SUPERSCRIPT_FOR_SQUAREMETERS = False
    ADD_DIMENSION_TEXTS = False
    DIMENSION_PATH_STYLE = dict(
        facecolor="black", edgecolor="black", aa=True, visible=True
    )


DXF_SIA_LAYER_ZORDER = 0  # necessary such that features etc are visible and not covered by the sia layer patches


class DXFSiaDefaultStyle(AssetManagerUnitStyle):
    AREA_PATCH_STYLE: Dict = dict(
        fill=False, linewidth=0.1, zorder=DXF_SIA_LAYER_ZORDER
    )
    USE_SUPERSCRIPT_FOR_SQUAREMETERS = False
    ADD_DIMENSION_TEXTS = True
    DIMENSION_PATH_STYLE = dict(
        facecolor="black", edgecolor="black", aa=True, visible=True
    )


class DXFSiaANFStyle(DXFSiaDefaultStyle):
    AREA_PATCH_STYLE: Dict = dict(
        facecolor="#df234c", hatch="////", linewidth=0.1, zorder=DXF_SIA_LAYER_ZORDER
    )


class DXFSiaHNFStyle(DXFSiaDefaultStyle):
    AREA_PATCH_STYLE: Dict = dict(
        facecolor="#df234c", linewidth=0.1, zorder=DXF_SIA_LAYER_ZORDER
    )


class DXFSiaNNFStyle(DXFSiaDefaultStyle):
    AREA_PATCH_STYLE: Dict = dict(
        facecolor="#f4b700", linewidth=0.1, zorder=DXF_SIA_LAYER_ZORDER
    )


class DXFSiaFFStyle(DXFSiaDefaultStyle):
    AREA_PATCH_STYLE: Dict = dict(
        facecolor="#00ade1", linewidth=0.1, zorder=DXF_SIA_LAYER_ZORDER
    )


class DXFSiaVFStyle(DXFSiaDefaultStyle):
    AREA_PATCH_STYLE: Dict = dict(
        facecolor="#f5eb00", linewidth=0.1, zorder=DXF_SIA_LAYER_ZORDER
    )


STYLES_BY_SIA416_LAYER = {
    SIACategory.ANF: DXFSiaANFStyle,
    SIACategory.HNF: DXFSiaHNFStyle,
    SIACategory.NNF: DXFSiaNNFStyle,
    SIACategory.FF: DXFSiaFFStyle,
    SIACategory.VF: DXFSiaVFStyle,
}
