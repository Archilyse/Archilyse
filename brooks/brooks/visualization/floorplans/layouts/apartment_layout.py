from typing import Optional

from brooks.models import SimLayout
from brooks.visualization.floorplans.assetmanager_style import (
    AssetManagerFloorOverviewStyle,
    AssetManagerHighlightStyle,
    AssetManagerUnitStyle,
)
from brooks.visualization.floorplans.layouts.base_assetmanager_layout import (
    AssetManagerLayout,
)
from brooks.visualization.floorplans.layouts.constants import LayoutLayers
from brooks.visualization.floorplans.layouts.utils import align_and_fit_axis


class AssetManagerApartmentLayout(AssetManagerLayout):
    def generate_layout(
        self,
        floor_layout: SimLayout,
        unit_layout: SimLayout,
        angle_north: float = 0,
        logo_content: Optional[bytes] = None,
    ):

        ax_orientation = self.axis_orientation(
            angle_north=angle_north,
        )
        ax_floor_overview = self.axis_floor_overview(
            floor_layout=floor_layout, unit_layout=unit_layout
        )
        ax_metadata = self.axis_metadata()

        self.axis_logo(logo_content=logo_content)
        self.axis_legal_advise()
        ax_unit = self.axis_unit(unit_layout=unit_layout)
        ax_scale, scale_factor = self.axis_scale(reference_axis=ax_unit)
        ax_separator = self.axis_separator()

        for ax in (
            ax_orientation,
            ax_floor_overview,
            ax_metadata,
            ax_scale,
            ax_separator,
        ):
            self._set_axis_layer_and_group(axis=ax, layer=LayoutLayers.TITLE_BLOCK)

        return self._figure

    # AXES

    def axis_floor_overview(self, floor_layout: SimLayout, unit_layout: SimLayout):
        x = (
            self.PAGE_WIDTH
            - self.PAGE_MARGIN
            - self.OVERVIEW_WIDTH
            - self.NORTH_INDICATOR_WIDTH
        )
        y = self.PAGE_HEIGHT - self.PAGE_MARGIN - self.TOP_HEIGHT
        w = self.OVERVIEW_WIDTH
        h = self.TOP_HEIGHT

        ax = self._add_axis(x, y, w, h, label="overview")
        # Generates the entire floor plan in the upper right corner
        self.generate_layout_patches(
            layout=floor_layout,
            axis=ax,
            style=AssetManagerFloorOverviewStyle,
            clipping=False,
        )

        # Generates the highlighted areas of the unit over the floor plan in the upper right corner
        self.generate_layout_patches(
            layout=unit_layout, axis=ax, style=AssetManagerHighlightStyle, clipping=True
        )
        self._reassign_axis_limits_based_on_brook_areas(
            ax=ax, floor_layout=floor_layout
        )

        return ax

    def axis_unit(self, unit_layout: SimLayout):
        ax = self.axis_main()
        self.generate_layout_patches(
            layout=unit_layout, axis=ax, style=AssetManagerUnitStyle, clipping=True
        )
        self.generate_layout_texts(
            layout=unit_layout, axis=ax, style=AssetManagerUnitStyle
        )
        align_and_fit_axis(ax, "C")
        return ax
