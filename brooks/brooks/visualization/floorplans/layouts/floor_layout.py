from typing import List, Optional, Tuple

from matplotlib.figure import Figure

from brooks.models import SimLayout
from brooks.visualization.floorplans.assetmanager_style import AssetManagerFloorStyle
from brooks.visualization.floorplans.layouts.base_assetmanager_layout import (
    AssetManagerLayout,
)
from brooks.visualization.floorplans.layouts.constants import LayoutLayers
from brooks.visualization.floorplans.layouts.utils import align_and_fit_axis


class AssetManagerFloorLayout(AssetManagerLayout):
    def generate_layout(
        self,
        floor_layout: SimLayout,
        unit_layouts: List[SimLayout],
        unit_ids: List[str],
        angle_north: float = 0,
        logo_content: Optional[bytes] = None,
    ) -> Tuple[Figure, float]:

        ax_orientation = self.axis_orientation(
            angle_north=angle_north,
        )
        ax_metadata = self.axis_metadata()

        self.axis_logo(logo_content=logo_content)
        self.axis_legal_advise()
        ax_floor = self.axis_floor(
            floor_layout=floor_layout, unit_layouts=unit_layouts, unit_ids=unit_ids
        )
        ax_scale, scale = self.axis_scale(reference_axis=ax_floor)
        ax_separator = self.axis_separator()

        for ax in (ax_orientation, ax_metadata, ax_scale, ax_separator):
            self._set_axis_layer_and_group(axis=ax, layer=LayoutLayers.TITLE_BLOCK)

        return self._figure, scale

    # AXES

    def axis_floor(
        self,
        floor_layout: SimLayout,
        unit_layouts: List[SimLayout],
        unit_ids: List[str],
    ):
        ax = self.axis_main()
        self.generate_layout_patches(
            layout=floor_layout,
            axis=ax,
            style=AssetManagerFloorStyle,
            clipping=False,
            unit_layouts=unit_layouts,
        )
        self.generate_layout_texts(
            layout=floor_layout, axis=ax, style=AssetManagerFloorStyle
        )
        align_and_fit_axis(ax, "N")

        return ax
