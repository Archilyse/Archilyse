from functools import cached_property
from typing import Optional

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

from handlers.charts.constants import FONT_DIR


class ArchilyseChart(plt.Figure):
    """
    Class for the basic chart layout:

    `                                            31.5 in
    ◄─────────────────────────────────────────────────────────────────────────────────────────────────►

    ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐   ▲ ▲
    │                                                                                                 │   │ │ DX = DY = 1.0 in
    │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐  │   │ ▼
    │  │TITLE                                                                                      │  │   │
    │  ├───────────────────────────────────────────────────────────────────────────────────────────┤  │   │
    │  │SUBTITLE                                                                                   │  │   │
    │  └───────────────────────────────────────────────────────────────────────────────────────────┘  │   │
    │                                                                                                 │   │
    │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │ 22.0 in
    │  ├                                          MAIN                                             ┤  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  │                                                                                           │  │   │
    │  └───────────────────────────────────────────────────────────────────────────────────────────┘  │   │
    │                                                                                                 │   │
    │  ┌───────────────────────────────────────────────────────────────────────────────────────────┐  │   │
    │  │BOTTOM_LEFT                                                                   BOTTOM_RIGHT │  │   │
    │  └───────────────────────────────────────────────────────────────────────────────────────────┘  │   │
    │                                                                                                 │   │
    └─────────────────────────────────────────────────────────────────────────────────────────────────┘   ▼
    """

    FIG_HEIGHT_INCHES = 22.0
    FIG_WIDTH_INCHES = 39.1
    DXY_INCHES = 1.0
    DPI = 72

    # dx, dy as fractions of figure size
    DY = DXY_INCHES / FIG_HEIGHT_INCHES
    DX = DXY_INCHES / FIG_WIDTH_INCHES

    # x, y, dx, dy (as multiples of DXY_INCHES)
    TITLE_AXIS = (1.0, 20.0, 37.0, 1.0)
    SUBTITLE_AXIS = (1.0, 19.0, 37.0, 1.0)
    BOTTOM_AXIS = (1.0, 0.5, 37.0, 0.5)
    MAIN_AXIS = (1.0, 3.25, 37.0, 15.25)

    # styling, note that this deviates from the chart styles
    FONTCOLOR_LIGHT = "#4a4a4a"
    FONTCOLOR_DARK = "#000000"

    # --------- Properties --------- #

    @cached_property
    def font_properties(self):
        return fm.FontProperties(
            fname=FONT_DIR.joinpath("Barlow-Regular.ttf").as_posix(),
            size=self.base_font_size,
        )

    @cached_property
    def font_properties_bold(self):
        return fm.FontProperties(
            fname=FONT_DIR.joinpath("Barlow-Bold.ttf").as_posix(),
            size=self.base_font_size,
        )

    @cached_property
    def base_font_size(self) -> float:
        return self.DXY_INCHES * self.DPI * 0.85

    # --------- Title, Description, Disclaimer, etc. --------- #

    def add_title(self, text: str, **kwargs):
        axis = self._add_invisible_axis(
            x0=self.TITLE_AXIS[0] * self.DX,
            y0=self.TITLE_AXIS[1] * self.DY,
            dx=self.TITLE_AXIS[2] * self.DX,
            dy=self.TITLE_AXIS[3] * self.DY,
        )

        axis.text(
            x=0,
            y=1,
            s=text,
            ha="left",
            va="top",
            transform=axis.transAxes,
            fontproperties=self.font_properties_bold,
            fontsize=self.base_font_size,
            color=self.FONTCOLOR_LIGHT,
            **kwargs
        )

        return axis

    def add_subtitle(self, text: str, **kwargs):
        axis = self._add_invisible_axis(
            x0=self.SUBTITLE_AXIS[0] * self.DX,
            y0=self.SUBTITLE_AXIS[1] * self.DY,
            dx=self.SUBTITLE_AXIS[2] * self.DX,
            dy=self.SUBTITLE_AXIS[3] * self.DY,
        )

        axis.text(
            x=0,
            y=1,
            s=text,
            ha="left",
            va="top",
            transform=axis.transAxes,
            fontproperties=self.font_properties,
            fontsize=self.base_font_size * 0.6,
            color=self.FONTCOLOR_DARK,
            **kwargs
        )

    def add_bottom_texts(
        self, text_left: str, text_right: Optional[str] = "", **kwargs
    ):
        axis = self._add_invisible_axis(
            x0=self.BOTTOM_AXIS[0] * self.DX,
            y0=self.BOTTOM_AXIS[1] * self.DY,
            dx=self.BOTTOM_AXIS[2] * self.DX,
            dy=self.BOTTOM_AXIS[3] * self.DY,
        )

        axis.text(
            x=0,
            y=0,
            s=text_left,
            ha="left",
            va="bottom",
            transform=axis.transAxes,
            fontproperties=self.font_properties,
            fontsize=20,
            color=self.FONTCOLOR_LIGHT,
            **kwargs
        )

        axis.text(
            x=1,
            y=0,
            s=text_right,
            ha="right",
            va="bottom",
            transform=axis.transAxes,
            fontproperties=self.font_properties,
            fontsize=20,
            color=self.FONTCOLOR_LIGHT,
            **kwargs
        )

    # --------- Utils --------- #

    @staticmethod
    def _make_axis_invisible(axis):
        for attr in (
            axis.get_xaxis(),
            axis.get_yaxis(),
            axis.patch,
            axis.spines["top"],
            axis.spines["left"],
            axis.spines["bottom"],
            axis.spines["right"],
        ):
            attr.set_visible(False)

    def _add_invisible_axis(self, x0: float, y0: float, dx: float, dy: float, **kwargs):
        ax = self.add_axes([x0, y0, dx, dy], **kwargs)
        self._make_axis_invisible(axis=ax)

        return ax
