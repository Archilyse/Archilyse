from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from pandas.io.formats.printing import pprint_thing


class ChartHandler:
    CMAP_5 = (
        "#dd7e6b",
        "#e6b8af",
        "#efefef",
        "#cfe2f3",
        "#9fc5e8",
    )
    CMAP_2 = ("#a61c00", "#3d85c6")

    @classmethod
    def donut_chart(
        cls,
        dataframe: pd.DataFrame,
        group_column: str,
        value_column: str,
        ax: plt.Axes,
        colors: Optional[Tuple] = None,
        score: Optional[float] = None,
        compact: bool = False,
    ) -> plt.Axes:
        """Creates a donut chart where `value_column` contains the fractions
        that are being plotted and `group_column` contains the category names.

        Example input:
        +---------------+----------+
        |   category    |  count   |
        +---------------+----------+
        | Lowest        | 0.083333 |
        | Below Average | 0.159483 |
        | Average       | 0.060345 |
        | Above Average | 0.319684 |
        | Highest       | 0.377155 |
        +---------------+----------+
        """
        groups = dataframe[group_column].values
        values = dataframe[value_column].values

        if colors is None:
            colors = cls.CMAP_5

        labels = [
            f"{label}\n{np.round(100*value):.0f}%" if value > 1e-5 else ""
            for label, value in zip(groups, values)
        ]
        radius = 1.1 if not compact else 1.0
        ax.pie(
            values,
            labels=labels if not compact else ["" for _ in labels],
            startangle=90,
            counterclock=True,
            colors=colors,
            labeldistance=0.9,
            radius=radius,
            wedgeprops={"linewidth": 7, "edgecolor": "white"},
            textprops={"weight": "bold"},
        )
        circle = plt.Circle((0, 0), 0.7 * radius, color="white", zorder=1)
        ax.add_artist(circle)

        if score is not None:
            ax.pie(
                [score, (1 - score)],
                startangle=90,
                counterclock=False,
                colors=[(0.4, 0.4, 0.4, 1), (1, 1, 1, 0)],
                radius=0.65 * radius,
            )
            circle = plt.Circle((0, 0), 0.575 * radius, color="white")
            ax.add_artist(circle)
            t = ax.text(
                0,
                0,
                f"{score*100:.0f}/100" if not compact else f"{score*100:.0f}",
                ha="center",
                va="center",
                fontsize="xx-large",
                weight="bold",
                zorder=3,
            )
            # since xx-large is still too small
            t.set_fontsize(t.get_fontsize() * 1.4)
        return ax

    @classmethod
    def parallel_coordinates(
        cls,
        dataframe: pd.DataFrame,
        group_column: str,
        ylim: Tuple,
        ytickcolors: Tuple,
        yticklabels: Tuple,
        ax: Optional[plt.Axes] = None,
        color=None,
        **kwds,
    ) -> plt.Axes:

        if ax is None:
            ax = plt.gca()

        n = len(dataframe)
        class_col = dataframe[group_column]
        df = dataframe.drop(group_column, axis=1)
        ncols = len(df.columns)
        x = list(range(ncols))
        xlim = (x[0] - 0.5, x[-1] + 0.075)

        for i in range(n):
            y = df.iloc[i].values
            kls = class_col.iat[i]
            label = pprint_thing(kls)

            ax.text(
                x=x[0],
                y=y[0],
                s=f"{label}   ",
                ha="right",
                va="center",
                bbox={
                    "facecolor": "white",
                    "boxstyle": "square",
                    "edgecolor": "none",
                    "zorder": 0,
                },
                zorder=0,
            )

            ax.plot(
                x,
                y,
                linewidth=20,
                linestyle="solid",
                color="#ffffff",
                zorder=1,
            )

            ax.plot(x, y, zorder=2, marker="o", **kwds)

        # --------- P20, P80 marker lines --------- #
        percentiles = [20, 80]
        percentile_colors = cls.CMAP_2

        for y, color in zip(percentiles, percentile_colors):
            ax.plot(xlim, (y, y), linewidth=2, color=color, zorder=-1)
            ax.text(
                x=xlim[1] + 0.025,
                y=y,
                s=f"P{y:.0f}",
                ha="left",
                va="center",
                color=color,
            )

        # --------- Y-Axis --------- #
        dy = (ylim[1] - ylim[0]) / len(ytickcolors)
        yticks = np.arange(dy / 2, ylim[1], dy)
        for y, color in zip(yticks, ytickcolors):
            ax.axhspan(
                ymin=y - dy / 2,
                ymax=y + dy / 2,
                color=color,
                zorder=-2,
            )
        ax.set_yticks(yticks)
        ax.set_yticklabels(yticklabels, ha="center", va="center", rotation=-90)
        ax.set_ylim(*ylim)

        # --------- X-Axis --------- #

        for i in x:
            ax.axvline(i, linewidth=2, color="white", zorder=0)
        ax.set_xticks(x)
        ax.set_xticklabels(df.columns, rotation=30, weight="bold")
        ax.set_xlim(*xlim)

        ax.grid(False, axis="y")

        return ax

    @classmethod
    def bar_chart(
        cls,
        dataframe: pd.DataFrame,
        ax: plt.Axes,
        colors: Optional[Tuple] = None,
        scores: Optional[pd.Series] = None,
        vertical: bool = False,
        multi_vertical: bool = False,
        xticks: Optional[Tuple] = None,
        mean_score: Optional[float] = None,
    ) -> plt.Axes:
        if colors is None:
            colors = cls.CMAP_5

        dataframe.plot(
            kind="bar" if not vertical else "barh",
            stacked=True,
            ax=ax,
            edgecolor="white",
            linewidth=2,
            colormap=ListedColormap(colors),
            zorder=5,
            width=0.8 if not vertical or multi_vertical else 1,
        )

        if scores is not None:
            score_labels = [f"{s*100:.0f}" for s in scores.values]

            if vertical:
                ys = list(range(len(scores)))
                xs = (scores * 0.95 * (ax.get_xlim()[1] - ax.get_xlim()[0])).values
            else:
                xs = list(range(len(scores)))
                ys = (scores * (ax.get_ylim()[1] - ax.get_ylim()[0])).values

            ax.plot(xs, ys, marker="o", zorder=7)
            for x, y, l in zip(xs, ys, score_labels):
                ax.text(
                    x=x,
                    y=y + (0.05 if not vertical else 0.2),
                    s=l,
                    ha="center",
                    va="bottom",
                    zorder=7,
                )

        if mean_score is not None:
            if not vertical:
                dx = ax.get_xlim()[1] - ax.get_xlim()[0]
                xs = [
                    ax.get_xlim()[0] + dx * 0.2,
                    ax.get_xlim()[1] - dx * 0.15,
                ]
                ys = [(ax.get_ylim()[1] - ax.get_ylim()[0]) * mean_score] * 2
                ax.text(
                    xs[1],
                    ys[1],
                    s=f"{mean_score*100:.0f}",
                    va="center",
                    ha="left",
                    zorder=8,
                )
            else:
                dy = ax.get_ylim()[1] - ax.get_ylim()[0]
                ys = [ax.get_ylim()[0] + dy * 0.2, ax.get_ylim()[1] - dy * 0.15]
                xs = [(ax.get_xlim()[1] - ax.get_xlim()[0]) * mean_score] * 2
                ax.text(
                    xs[1],
                    ys[1],
                    s=f"{mean_score*100:.0f}",
                    va="bottom",
                    ha="center",
                    zorder=8,
                )

            ax.plot(xs, ys, linestyle="solid", zorder=6)

        if not vertical:
            ax.spines["bottom"].set_visible(True)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=30, weight="bold")
            ax.get_xaxis().set_visible(True)
            ax.get_yaxis().set_visible(False)
        elif not multi_vertical:
            if xticks:
                ax.set_xticks(xticks)
                ax.get_xaxis().set_visible(True)
            ax.set_ylabel("")
            ax.get_yaxis().set_visible(False)
        else:
            ax.spines["left"].set_visible(True)
            ax.set_yticklabels(ax.get_yticklabels(), weight="bold")
            ax.get_yaxis().set_visible(True)
            ax.get_yaxis().set_label_position("left")
            ax.get_yaxis().tick_left()
            ax.set_ylabel("")
            if xticks:
                ax.set_xticks(xticks)
                ax.get_xaxis().set_visible(True)
            else:
                ax.get_xaxis().set_visible(False)
                ax.set_xticks([])

        ax.set_xlabel("")
        ax.get_legend().set_visible(False)
        return ax
