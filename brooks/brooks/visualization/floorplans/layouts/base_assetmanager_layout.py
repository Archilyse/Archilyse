import io
from functools import partial
from typing import Callable, Dict, List, Optional, Set, Tuple, Type

from matplotlib import image as mpimg
from matplotlib.axes import Axes
from matplotlib.patches import Patch
from matplotlib.pyplot import Figure

from brooks.classifications import CLASSIFICATIONS
from brooks.models import SimLayout
from brooks.types import FeatureType
from brooks.visualization.floorplans.assetmanager_style import (
    AssetManagerFloorOverviewStyle,
)
from brooks.visualization.floorplans.base_figure_style import FigureStyle
from brooks.visualization.floorplans.layouts.assetmanager_layout_text import (
    BaseAssetManagerTextGenerator,
)
from brooks.visualization.floorplans.layouts.constants import LayoutLayers
from brooks.visualization.floorplans.layouts.utils import align_and_fit_axis, cm_to_inch
from brooks.visualization.floorplans.patches.generators import (
    ScaleBarGenerator,
    generate_area_patches,
    generate_dimension_patches,
    generate_dimension_texts,
    generate_door_patches,
    generate_feature_patches,
    generate_orientation_patches,
    generate_railings_patches,
    generate_room_texts,
    generate_wall_and_column_patches,
    generate_window_patches,
)
from common_utils.constants import SUPPORTED_LANGUAGES


class AssetManagerLayout:
    """
    A figure layout according to AssetManager's final proposal as
    of 01/10/19.
                                   4:3                       (W,H)
        +-----------------------------------------------------+
        |                                                     | 1cm
        |   +------------------------------+--------------+   +
        |   |            METADATA          | OVERVIEW | N |   | 2.5cm
        |   +------------------------------+--------------+   +
        |   |                                             |   | 1cm
        |   |.............................................|   +
        |   |                                             |   |
        |   |                                             |   |
        |   |                    MAIN                     |   |
        |   |                                             |   |
        |   |                                             |   |
        |   +-----------------------+---------------------+   +
        |   | SCALE                 |                LOGO |   | 1.7cm
        |   +-----------------------+---------------------+   +
        |                                                     |
        +-----------------------------------------------------+
      (0,0)

    The overview height and margin have not been specified
    by AssetManager and have been set to 2.5cm and 0.5cm, respectively.
    """

    PAGE_MARGIN = cm_to_inch(1.0)
    PAGE_WIDTH = cm_to_inch(28.0)
    PAGE_HEIGHT = cm_to_inch(21.0)

    MARGIN_TOP_UNIT = cm_to_inch(1.0)  # assetmanager
    BOTTOM_HEIGHT = cm_to_inch(1.7)  # assetmanager

    TOP_HEIGHT = cm_to_inch(2.5)
    LOGO_WIDTH = 0.15 * (PAGE_WIDTH - 2 * PAGE_MARGIN)
    LEGAL_DISCLAIMER_WIDTH = 0.25 * (PAGE_WIDTH - 2 * PAGE_MARGIN)
    OVERVIEW_WIDTH = 0.2 * (PAGE_WIDTH - 2 * PAGE_MARGIN)
    NORTH_INDICATOR_WIDTH = 0.15 * (PAGE_WIDTH - 2 * PAGE_MARGIN)
    SPACE_BETWEEN_OVERVIEW_AND_METADATA = 0.1 * (PAGE_WIDTH - 2 * PAGE_MARGIN)

    def __init__(
        self,
        language: SUPPORTED_LANGUAGES,
        assetmanager_text_generator: BaseAssetManagerTextGenerator,
        classification: CLASSIFICATIONS = CLASSIFICATIONS.UNIFIED,
    ):
        self.language = language
        self.assetmanager_text_generator = assetmanager_text_generator
        self._classification = classification
        self._figure = Figure(
            figsize=(AssetManagerLayout.PAGE_WIDTH, AssetManagerLayout.PAGE_HEIGHT)
        )
        self._axes: Dict[str, Axes] = {}

    # PROPERTIES

    @property
    def classification_scheme(self):
        return self._classification.value

    def _add_axis(self, x, y, w, h, label=None):
        """[summary]
        Args:
            x (float): x position in inches
            y (float): y position in inches
            w (float): width in inches
            h (float): height in inches
        """
        width = self._figure.get_figwidth()
        height = self._figure.get_figheight()

        x0, y0 = x / width, y / height
        dx, dy = w / width, h / height

        label = label or str(len(self._axes))

        self._axes[label] = self._figure.add_axes([x0, y0, dx, dy], label=label)
        for attr in (
            self._axes[label].axes.get_xaxis(),
            self._axes[label].axes.get_yaxis(),
            self._axes[label].patch,
            self._axes[label].spines["top"],
            self._axes[label].spines["left"],
            self._axes[label].spines["bottom"],
            self._axes[label].spines["right"],
        ):
            attr.set_visible(False)

        return self._axes[label]

    # AXES

    def axis_separator(self):
        x = self.PAGE_MARGIN
        y = self.PAGE_MARGIN + self.BOTTOM_HEIGHT
        w = self.PAGE_WIDTH - 2 * self.PAGE_MARGIN
        h = (
            self.PAGE_HEIGHT
            - 2 * self.PAGE_MARGIN
            - self.BOTTOM_HEIGHT
            - self.TOP_HEIGHT
        )

        ax = self._add_axis(x, y, w, h, label="separator")
        ax.spines["top"].set_visible(True)

        return ax

    def axis_main(self):
        x = self.PAGE_MARGIN
        y = self.PAGE_MARGIN + self.BOTTOM_HEIGHT
        w = self.PAGE_WIDTH - 2 * self.PAGE_MARGIN
        h = (
            self.PAGE_HEIGHT
            - 2 * self.PAGE_MARGIN
            - self.BOTTOM_HEIGHT
            - self.TOP_HEIGHT
            - self.MARGIN_TOP_UNIT
        )

        return self._add_axis(x, y, w, h, label="main")

    def axis_scale(
        self,
        reference_axis: Axes,
        add_texts: bool = True,
        dxf_axis_shift: float = 0.0,
    ) -> Tuple[Axes, float]:
        """
        dxf_axis_shift: for some reason autocad has problems displaying
        the generated dxf file if the scale axis is not slightly shifted
        away from the page margin
        """
        x = self.PAGE_MARGIN + dxf_axis_shift
        y = self.PAGE_MARGIN + dxf_axis_shift
        w = self.PAGE_WIDTH - 2 * self.PAGE_MARGIN - self.LOGO_WIDTH
        h = self.BOTTOM_HEIGHT

        ax = self._add_axis(x, y, w, h, label="scale")
        scale = ScaleBarGenerator().add_scale_bar_to_axis(
            scale_bar_axis=ax, reference_axis=reference_axis, add_texts=add_texts
        )

        return ax, scale

    def axis_logo(self, logo_content: Optional[bytes] = None):
        if logo_content:
            x = self.PAGE_WIDTH - self.PAGE_MARGIN - self.LOGO_WIDTH
            y = self.PAGE_MARGIN
            w = self.LOGO_WIDTH
            h = 0.5 * self.BOTTOM_HEIGHT

            ax = self._add_axis(x, y, w, h, label="logo")

            image_io = io.BytesIO(logo_content)
            img = mpimg.imread(image_io)
            self._axes["logo"].imshow(img)

            return ax

    def axis_legal_advise(self):
        x = (
            self.PAGE_WIDTH
            - self.PAGE_MARGIN
            - self.LOGO_WIDTH
            - self.LEGAL_DISCLAIMER_WIDTH
        )
        y = self.PAGE_MARGIN
        w = self.LEGAL_DISCLAIMER_WIDTH
        h = 0.5 * self.BOTTOM_HEIGHT

        ax = self._add_axis(x, y, w, h, label="legal_advise")

        ax.text(
            x=1,
            y=0.5,
            s=self.assetmanager_text_generator.legal_advise,
            color="black",
            size=6,
            horizontalalignment="right",
            verticalalignment="center",
        )

        return ax

    def axis_metadata(self):
        x = self.PAGE_MARGIN
        y = self.PAGE_HEIGHT - self.PAGE_MARGIN - self.TOP_HEIGHT
        w = (
            self.PAGE_WIDTH
            - 2 * self.PAGE_MARGIN
            - self.OVERVIEW_WIDTH
            - self.NORTH_INDICATOR_WIDTH
            - self.SPACE_BETWEEN_OVERVIEW_AND_METADATA
        )
        h = self.TOP_HEIGHT

        ax = self._add_axis(x, y, w, h, label="metadata")
        self.assetmanager_text_generator.generate_metadata_texts(axis=ax, w=w, h=h)
        align_and_fit_axis(ax, "NW", autoscale=False)

        return ax

    def axis_orientation(self, angle_north: float):
        x = self.PAGE_WIDTH - self.PAGE_MARGIN - self.NORTH_INDICATOR_WIDTH
        y = self.PAGE_HEIGHT - self.PAGE_MARGIN - self.TOP_HEIGHT * 5 / 6
        w = self.NORTH_INDICATOR_WIDTH
        h = self.TOP_HEIGHT * 4 / 6
        ax = self._add_axis(x, y, w, h, label="orientation")
        orientation_patches = self.generate_north_indicator_patch(
            angle_north=angle_north,
            axis=ax,
        )
        ax.set_aspect("equal")
        ax.autoscale()
        AssetManagerFloorOverviewStyle.apply(artists=orientation_patches)

        return ax

    # PATCH GENERATIONS
    def generate_layout_patches(
        self,
        layout: SimLayout,
        axis,
        style: Type[FigureStyle],
        clipping: bool,
        unit_layouts: Optional[List[SimLayout]] = None,
        exclude_layers: Optional[Set[LayoutLayers]] = None,
    ):
        unit_db_area_ids: Set[int] = set()
        if unit_layouts is not None:
            unit_db_area_ids = {
                area.db_area_id for unit in unit_layouts for area in unit.areas
            }.intersection({area.db_area_id for area in layout.areas})

        exclude_layers = exclude_layers or set()
        layers = {
            **self.get_feature_layers(layout=layout),
            LayoutLayers.RAILINGS: (generate_railings_patches, dict(layout=layout)),
            LayoutLayers.WALLS: (
                generate_wall_and_column_patches,
                dict(
                    layout=layout,
                ),
            ),
            LayoutLayers.WINDOWS: (generate_window_patches, dict(layout=layout)),
            LayoutLayers.DOORS: (
                generate_door_patches,
                dict(layout=layout, unit_db_area_ids=unit_db_area_ids),
            ),
            LayoutLayers.ROOM_POLYGONS: (
                generate_area_patches,
                dict(layout=layout),
            ),
            LayoutLayers.DIMENSIONING: (
                generate_dimension_patches,
                dict(layout=layout),
            ),
        }

        patches = []
        for layer, (generator, args) in layers.items():
            if layer not in exclude_layers:
                for patch in generator(**args):  # type: ignore
                    self._set_artist_layer_and_group(artist=patch, layer=layer)
                    axis.add_patch(patch)
                    patches.append(patch)

        style.apply(artists=patches)
        if clipping:
            style.clip(ax=axis, patches=patches, layout=layout)

    @staticmethod
    def get_feature_layers(
        layout: SimLayout,
    ) -> Dict[LayoutLayers, Tuple[Callable, Dict]]:
        feature_types_per_layer = {
            LayoutLayers.SHAFTS: {FeatureType.SHAFT},
            LayoutLayers.STAIRS_ELEVATORS: {FeatureType.STAIRS, FeatureType.ELEVATOR},
            LayoutLayers.SANITARY_AND_KITCHEN: {
                FeatureType.SINK,
                FeatureType.SHOWER,
                FeatureType.BATHTUB,
                FeatureType.TOILET,
                FeatureType.KITCHEN,
                FeatureType.WASHING_MACHINE,
            },
        }
        feature_types_per_layer[LayoutLayers.FEATURES] = set(FeatureType) - {
            feature_type
            for feature_types in feature_types_per_layer.values()
            for feature_type in feature_types
        }
        return {
            layer: (
                partial(generate_feature_patches, include_feature_types=feature_types),
                dict(layout=layout),
            )
            for layer, feature_types in feature_types_per_layer.items()
        }

    @staticmethod
    def generate_north_indicator_patch(angle_north: float, axis) -> List[Patch]:
        patches = []
        for patch in generate_orientation_patches(
            angle_north=angle_north,
            axis=axis,
        ):
            axis.add_patch(patch)
            patches.append(patch)

        return patches

    # TEXT GENERATIONS

    def generate_layout_texts(self, layout: SimLayout, axis, style):
        room_stamp_font_size = (
            1 if layout.is_large_layout else style.ROOM_TEXT_STYLE["size"]
        )
        if style.ADD_ROOM_TEXTS:
            for x, y, text, angle in generate_room_texts(
                layout=layout,
                area_type_to_name=self.assetmanager_text_generator.area_type_to_name_mapping,
                axis=axis,
                use_superscript_for_squaremeters=style.USE_SUPERSCRIPT_FOR_SQUAREMETERS,
            ):
                text = axis.text(
                    x=x,
                    y=y,
                    s=text,
                    rotation=angle,
                    size=room_stamp_font_size,
                    name=style.ROOM_TEXT_STYLE["name"],
                    color=style.ROOM_TEXT_STYLE["color"],
                    verticalalignment=style.ROOM_TEXT_STYLE["verticalalignment"],
                    horizontalalignment=style.ROOM_TEXT_STYLE["horizontalalignment"],
                )
                self._set_artist_layer_and_group(
                    artist=text, layer=LayoutLayers.ROOM_STAMP
                )

        if style.ADD_DIMENSION_TEXTS:
            for x, y, text, angle in generate_dimension_texts(layout=layout):
                text = axis.text(
                    x=x,
                    y=y,
                    s=text,
                    rotation=angle,
                    size=style.DIMENSION_TEXT_STYLE["size"],
                    name=style.DIMENSION_TEXT_STYLE["name"],
                    color=style.DIMENSION_TEXT_STYLE["color"],
                    verticalalignment=style.DIMENSION_TEXT_STYLE["verticalalignment"],
                    horizontalalignment=style.DIMENSION_TEXT_STYLE[
                        "horizontalalignment"
                    ],
                )
                self._set_artist_layer_and_group(
                    artist=text, layer=LayoutLayers.DIMENSIONING
                )

    # VERBOSE TEXTS

    # UTILS

    @staticmethod
    def _reassign_axis_limits_based_on_brook_areas(ax, floor_layout):
        x0s = [area.footprint.bounds[0] for area in floor_layout.areas]
        y0s = [area.footprint.bounds[1] for area in floor_layout.areas]
        x1s = [area.footprint.bounds[2] for area in floor_layout.areas]
        y1s = [area.footprint.bounds[3] for area in floor_layout.areas]
        x0, y0 = min(x0s), min(y0s)
        x1, y1 = max(x1s), max(y1s)
        dx = x1 - x0
        dy = y1 - y0
        mindelta = min([x1 - x0, y1 - y0])
        padding = mindelta * 0.1  # This can potentially remove the measurement lines
        ax.set_xlim(x0 - padding, x0 + dx + padding)
        ax.set_ylim(y0 - padding, y0 + dy + padding)
        ax.set_aspect("equal")

    def _set_axis_layer_and_group(self, axis, layer: LayoutLayers, group: str = None):
        for patch in axis.patches:
            self._set_artist_layer_and_group(artist=patch, layer=layer, group=group)

        for text in axis.texts:
            self._set_artist_layer_and_group(artist=text, layer=layer, group=group)

    def _set_artist_layer_and_group(
        self, artist, layer: LayoutLayers, group: str = None
    ):
        artist.set_gid(
            (self.assetmanager_text_generator._verbose_layer(layer=layer), group)
        )
