import io
from typing import Any, Dict, List, Optional, Union

import matplotlib
from matplotlib.backend_bases import register_backend

from brooks.constants import IMAGES_DPI
from brooks.models.layout import SimLayout
from brooks.visualization.backends.dxf import FigureCanvasDXF
from brooks.visualization.floorplans.layouts.apartment_layout import (
    AssetManagerApartmentLayout,
)
from brooks.visualization.floorplans.layouts.assetmanager_layout_text import (
    ApartmentAssetManagerTextGenerator,
    FloorAssetManagerTextGenerator,
)
from brooks.visualization.floorplans.layouts.dxf_layout import DXFFloorLayout
from brooks.visualization.floorplans.layouts.floor_layout import AssetManagerFloorLayout
from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES

register_backend("dxf", FigureCanvasDXF, "DXF Format")


class BrooksPlotter:
    def __init__(self):
        self.fig = None
        self.dxf_scale_factor = 1.0

    @staticmethod
    def dxf_scale_factor_correction(dpi: int) -> float:
        """For different dpis the behavior doesn't seem to be linear,
        so using this 2 points we don't know yet what is the relationship between the dpis"""

        return {200: 203.09632, 300: 517.968747}[dpi]

    def _get_io_image(
        self, file_format: SUPPORTED_OUTPUT_FILES, dpi: int
    ) -> Union[io.BytesIO, io.StringIO]:
        matplotlib.use("Agg")
        if file_format == SUPPORTED_OUTPUT_FILES.DXF:
            self.fig.patch.set_visible(False)
            io_file = io.StringIO()
        else:
            io_file = io.BytesIO()  # type: ignore

        self.fig.savefig(
            io_file,
            format=file_format.name.lower(),
            transparent=False,
            dpi=dpi,
            dxf_scale_factor=self.dxf_scale_factor,
        )
        io_file.seek(0)
        matplotlib.pyplot.close()
        return io_file

    def generate_unit_plot(
        self,
        unit_target_layout: SimLayout,
        floor_plan_layout: SimLayout,
        metadata: Dict[str, Any],
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
        angle_north: int = 0,
        logo_content: Optional[bytes] = None,
    ) -> Union[io.BytesIO, io.StringIO]:
        """Plots the apartment onto a matplotlib axes object.If no axis is provided,
        a 4:3 figure will be generated at 200dpi.
        """
        self.fig = AssetManagerApartmentLayout(
            language=language,
            assetmanager_text_generator=ApartmentAssetManagerTextGenerator(
                metadata=metadata, language=language
            ),
        ).generate_layout(
            floor_layout=floor_plan_layout,
            unit_layout=unit_target_layout,
            angle_north=angle_north,
            logo_content=logo_content,
        )

        return self._get_io_image(
            file_format=file_format,
            dpi=3 * IMAGES_DPI if unit_target_layout.is_large_layout else IMAGES_DPI,
        )

    def generate_floor_plot(
        self,
        floor_plan_layout: SimLayout,
        unit_layouts: List[SimLayout],
        unit_ids: List[str],
        metadata: Dict[str, Any],
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
        angle_north: int = 0,
        logo_content: Optional[bytes] = None,
    ) -> Union[io.BytesIO, io.StringIO]:
        """Plots the apartment onto a matplotlib axes object. If no axis is provided,
        a 4:3 figure will be generated at 200dpi.
        """
        # later we can make a differentiation by client here
        layout = {
            SUPPORTED_OUTPUT_FILES.PNG: AssetManagerFloorLayout,
            SUPPORTED_OUTPUT_FILES.PDF: AssetManagerFloorLayout,
            SUPPORTED_OUTPUT_FILES.DXF: DXFFloorLayout,
        }[file_format]
        self.fig, self.dxf_scale_factor = layout(
            language=language,
            assetmanager_text_generator=FloorAssetManagerTextGenerator(
                metadata=metadata, language=language
            ),
        ).generate_layout(
            floor_layout=floor_plan_layout,
            unit_layouts=unit_layouts,
            unit_ids=unit_ids,
            angle_north=angle_north,
            logo_content=logo_content,
        )
        dpi = IMAGES_DPI
        if floor_plan_layout.is_large_layout and file_format in {
            SUPPORTED_OUTPUT_FILES.PNG,
            SUPPORTED_OUTPUT_FILES.PDF,
        }:
            dpi = IMAGES_DPI * 3

        if file_format in {SUPPORTED_OUTPUT_FILES.DXF, SUPPORTED_OUTPUT_FILES.DWG}:
            self.dxf_scale_factor = 1 / (
                self.dxf_scale_factor * self.dxf_scale_factor_correction(dpi=dpi)
            )
        return self._get_io_image(file_format=file_format, dpi=dpi)
