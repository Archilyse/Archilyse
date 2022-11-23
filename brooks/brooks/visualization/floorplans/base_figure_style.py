import contextlib
from typing import Dict, Tuple

from matplotlib.artist import setp
from matplotlib.patches import Polygon as PolygonPatch

from brooks.models import SimLayout
from brooks.visualization.floorplans.patches.collection import (
    DimensionLinePatch,
    RailingPatch,
    SeparatorPatch,
)

from .patches.door import DoorStepPatch, EntranceDoorFlagPatch
from .patches.feature import (
    AreasEdgesPatch,
    AreasPatch,
    GenericFeaturePatch,
    GenericPolygonFeaturePatch,
    KitchenCornerPatch,
    ScaledRoundedPatch,
    ShaftFeaturePatch,
    StairArrowHeadPatch,
    StairArrowTailPatch,
)
from .patches.orientation import OrientationPatchCollection


class FigureStyle:
    LINEWIDTH = 0.6
    WALL_PATCH_STYLE: Dict = dict(
        edgecolor="black",
        facecolor="black",
        linewidth=LINEWIDTH,
    )
    RAILING_PATCH_STYLE: Dict = dict(
        edgecolor="black",
        facecolor="w",
        linewidth=LINEWIDTH,
    )
    WINDOW_PATCH_STYLE: Dict = dict(
        facecolor="w", edgecolor="black", linewidth=LINEWIDTH * 0.5
    )
    WINDOW_CENTERLINE_STYLE: Dict = dict(
        facecolor="none", edgecolor="black", linewidth=LINEWIDTH * 0.5
    )
    DOOR_STEP_PATCH_STYLE: Dict = dict(
        facecolor="w", edgecolor="black", linewidth=LINEWIDTH
    )
    AREA_PATCH_STYLE: Dict = dict(facecolor="w", edgecolor="black", aa=True)
    SHAFT_FEATURE_PATCH_STYLE: Dict = dict(
        facecolor="lightgray", edgecolor="black", aa=True
    )
    DIMENSION_PATH_STYLE: Dict = dict(facecolor="black", edgecolor="black", aa=True)
    FEATURE_PATCH_STYLE: Dict = dict(
        edgecolor="black",
        aa=True,
        linewidth=0.2,
        fill=False,
    )
    STAIR_ARROW_HEAD_PATCH_STYLE: Dict = dict(facecolor="black", linewidth=0, aa=True)
    STAIR_ARROW_TAIL_PATCH_STYLE: Dict = dict(
        facecolor="none",
        edgecolor="black",
        linewidth=0.1,
        aa=True,
        fill=False,
    )
    ORIENTATION_PATCH_STYLE: Dict = dict(facecolor="black", edgecolor="black", aa=True)
    ENTRANCE_DOOR_FLAG_STYLE: Dict = dict(facecolor="black", edgecolor="black", aa=True)

    IGNORE_CLIPPING: Tuple = ()
    CLIPPING_BUFFER = 0.5 + LINEWIDTH
    LIVIT_FONT = "Liberation Sans"
    ADD_ROOM_TEXTS = False
    ADD_DIMENSION_TEXTS = False
    USE_SUPERSCRIPT_FOR_SQUAREMETERS = True

    ROOM_TEXT_STYLE: Dict = dict(
        size=7,
        name=LIVIT_FONT,
        color="black",
        verticalalignment="center",
        horizontalalignment="center",
    )

    DIMENSION_TEXT_STYLE: Dict = dict(
        size=6,
        name=LIVIT_FONT,
        color="black",
        verticalalignment="center",
        horizontalalignment="center",
    )

    TITLE_FONT_STYLE: Dict = dict(
        size=11,
        name=LIVIT_FONT,
        color="black",
        verticalalignment="bottom",
        horizontalalignment="left",
        weight="bold",
    )

    INFO_FONT_STYLE: Dict = dict(
        size=9,
        name=LIVIT_FONT,
        color="black",
        verticalalignment="bottom",
        horizontalalignment="left",
    )

    # used exclusively for defining the style of the letter 'N', which defines
    # the northern direction of the compass in the AssetManagerApartmentLayout
    N_INDICATOR_FONT_STYLE: Dict = dict(
        fontsize=9, name=LIVIT_FONT, color="Black", weight="50"
    )

    AREAS_EDGES_STYLE = dict(fill=False, linewidth=LINEWIDTH, edgecolor="black")

    @classmethod
    def _get_style(cls, artist):
        from brooks.visualization.floorplans.patches.window import (
            WindowCenterLinePatch,
            WindowPatch,
        )

        patch_styles = {
            SeparatorPatch: cls.WALL_PATCH_STYLE,
            AreasPatch: cls.AREA_PATCH_STYLE,
            ShaftFeaturePatch: cls.SHAFT_FEATURE_PATCH_STYLE,
            DimensionLinePatch: cls.DIMENSION_PATH_STYLE,
            DoorStepPatch: cls.DOOR_STEP_PATCH_STYLE,
            WindowPatch: cls.WINDOW_PATCH_STYLE,
            WindowCenterLinePatch: cls.WINDOW_CENTERLINE_STYLE,
            GenericFeaturePatch: cls.FEATURE_PATCH_STYLE,
            GenericPolygonFeaturePatch: cls.FEATURE_PATCH_STYLE,
            StairArrowHeadPatch: cls.STAIR_ARROW_HEAD_PATCH_STYLE,
            StairArrowTailPatch: cls.STAIR_ARROW_TAIL_PATCH_STYLE,
            ScaledRoundedPatch: cls.FEATURE_PATCH_STYLE,
            OrientationPatchCollection: cls.ORIENTATION_PATCH_STYLE,
            EntranceDoorFlagPatch: cls.ENTRANCE_DOOR_FLAG_STYLE,
            RailingPatch: cls.RAILING_PATCH_STYLE,
            KitchenCornerPatch: cls.FEATURE_PATCH_STYLE,
            AreasEdgesPatch: cls.AREAS_EDGES_STYLE,
        }

        return patch_styles[type(artist)]

    @classmethod
    def apply(cls, artists):
        for artist in artists:
            with contextlib.suppress(KeyError):
                setp(artist, **cls._get_style(artist))

    @classmethod
    def clip(cls, ax, patches, layout: SimLayout):
        """This clipping method is using the polygon return by the SpaceConnector and then clipping everything that is
        outside of this space. The root problem is that we don't have a clear view in the Brooks model of the
        separators that strictly and uniquely belong to each apartment.
        """
        clipping_geometries = layout.get_polygon_of_spaces_and_doors(
            layout=layout, clipping_buffer=cls.CLIPPING_BUFFER
        )
        # TODO: some polygons here are not valid, coords are an empty list.
        if clipping_geometries.exterior.coords:
            polygon_patch = PolygonPatch(
                clipping_geometries.exterior.coords, fc="none", ec="none"
            )
            ax.add_patch(polygon_patch)
            for patch in patches:
                if not isinstance(patch, cls.IGNORE_CLIPPING):
                    patch.set_clip_path(polygon_patch)
