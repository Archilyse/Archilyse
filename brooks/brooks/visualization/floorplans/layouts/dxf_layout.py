from typing import List, Optional, Tuple

from matplotlib.axes import Axes

from brooks.models import SimLayout
from brooks.visualization.floorplans.assetmanager_style import DXFUnitStyle
from brooks.visualization.floorplans.layouts.constants import LayoutLayers
from brooks.visualization.floorplans.layouts.floor_layout import AssetManagerFloorLayout
from brooks.visualization.floorplans.layouts.utils import align_and_fit_axis, cm_to_inch
from brooks.visualization.floorplans.patches.generators import (
    generate_layout_footprint_patches,
    generate_sia_patches,
)


class DXFFloorLayout(AssetManagerFloorLayout):
    def axis_scale(
        self,
        reference_axis: Axes,
        add_texts: Optional[bool] = True,
        dxf_axis_shift: Optional[float] = 0.0,
    ) -> Tuple[Axes, float]:
        return super().axis_scale(
            reference_axis=reference_axis, add_texts=True, dxf_axis_shift=cm_to_inch(1)
        )

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
            style=DXFUnitStyle,
            clipping=False,
            unit_layouts=unit_layouts,
            exclude_layers={LayoutLayers.DIMENSIONING},
        )

        # add hatched sia416 categories
        for unit_layout in unit_layouts:
            for layer_info in self.classification_scheme().DXF_SIA_LAYERS:
                patches = []
                for patch in generate_sia_patches(
                    layout=unit_layout,
                    sia_category=layer_info["sia_area_type"],
                ):
                    ax.add_patch(patch)
                    self._set_artist_layer_and_group(
                        artist=patch, layer=layer_info["sia_area_type"]
                    )
                    patches.append(patch)
                layer_info["style"].apply(patches)

        # add area patches per apartment with unit_id = dxf_group
        patches = []
        for unit_layout, unit_id in zip(unit_layouts, unit_ids):
            for patch in generate_layout_footprint_patches(
                layout=unit_layout,
            ):
                ax.add_patch(patch)
                self._set_artist_layer_and_group(
                    artist=patch, layer=LayoutLayers.UNITS, group=unit_id
                )
                patches.append(patch)
        DXFUnitStyle.apply(patches)

        self.generate_layout_texts(layout=floor_layout, axis=ax, style=DXFUnitStyle)
        align_and_fit_axis(ax, "N")

        return ax

    def axis_legal_advise(self):
        """
        Overwrites method of SuperClass as we
        don't want to add the legal advise for the dxf
        files for now
        """
        pass
