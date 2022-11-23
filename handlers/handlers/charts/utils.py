from functools import wraps
from typing import Iterable, List, Literal, Optional

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import pandas as pd

from handlers.charts.constants import CHART_STYLE, FONT_DIR


def histogram_per_group(
    dataframe: pd.DataFrame,
    group_columns: List[str],
    bins: Iterable,
    use_group_mean: bool = False,
    normalized: Literal["none", "group", "bin"] = "group",
    labels: Optional[Iterable] = None,
):
    """
    For each group returns the _count_ of each bin over _all_ columns.

     E.g. given this dataframe with bins=[0, 20, 40, 60, 80, 100] and group column `area_type`
         +-----------+----------------+---------------+
         | area_type | view_buildings | view_greenery |
         +-----------+----------------+---------------+
         | Bathroom  |      83.318379 |     62.147042 |
         | Bathroom  |      57.513063 |     57.982794 |
         | Corridor  |      38.402775 |     18.211906 |
         | Kitchen   |      40.910705 |     17.635008 |
         | Loggia    |      33.117683 |     15.003081 |
         +-----------+----------------+---------------+

     Unnormalized, the result looks like this (i.e. _count_ for each area type how often it falls
     into a particular bin):
         +------------+-------------+--------------+--------------+--------------+---------------+
         | area_type* | (0.0, 20.0] | (20.0, 40.0] | (40.0, 60.0] | (60.0, 80.0] | (80.0, 100.0] |
         +------------+-------------+--------------+--------------+--------------+---------------+
         | Bathroom   |           0 |            0 |            2 |            1 |             1 |
         | Corridor   |           1 |            1 |            0 |            0 |             0 |
         | Kitchen    |           1 |            0 |            1 |            0 |             0 |
         | Loggia     |           1 |            1 |            0 |            0 |             0 |
         +------------+-------------+--------------+--------------+--------------+---------------+

     However, we have 2 bathrooms, we might be interested to pass `use_group_mean=True`:
         +------------+-------------+--------------+--------------+--------------+---------------+
         | area_type* | (0.0, 20.0] | (20.0, 40.0] | (40.0, 60.0] | (60.0, 80.0] | (80.0, 100.0] |
         | Bathroom   |         0.0 |          0.0 |          1.0 |          0.5 |           0.5 |
         | Corridor   |         1.0 |          1.0 |          0.0 |          0.0 |           0.0 |
         | Kitchen    |         1.0 |          0.0 |          1.0 |          0.0 |           0.0 |
         | Loggia     |         1.0 |          1.0 |          0.0 |          0.0 |           0.0 |
         +------------+-------------+--------------+--------------+--------------+---------------+

     If we are interested in the frequency of each bin per area type, we might pass normalized="group"
     such that we get a probability function per row. E.g. in the example below, a bathroom falls
     in 50% of the cases into bin (40.0, 60.0], 25% into (60.0, 80.0] etc.:
         +------------+-------------+--------------+--------------+--------------+---------------+
         | area_type* | (0.0, 20.0] | (20.0, 40.0] | (40.0, 60.0] | (60.0, 80.0] | (80.0, 100.0] |
         +------------+-------------+--------------+--------------+--------------+---------------+
         | Bathroom   |         0.0 |          0.0 |          0.5 |         0.25 |          0.25 |
         | Corridor   |         0.5 |          0.5 |          0.0 |         0.00 |          0.00 |
         | Kitchen    |         0.5 |          0.0 |          0.5 |         0.00 |          0.00 |
         | Loggia     |         0.5 |          0.5 |          0.0 |         0.00 |          0.00 |
         +------------+-------------+--------------+--------------+--------------+---------------+

     Finally, for `normalized='bin'`, we can also retrieve the frequency per bin. E.g if we look at
     column (80.0, 100.0], all values in this bin are coming from the bathroom area type while
     bin (0.0, 20.0] does not contain any bathroom but is equally made up by Corridors, Kitchens and
     Loggias:
         +------------+-------------+--------------+--------------+--------------+---------------+
         | area_type* | (0.0, 20.0] | (20.0, 40.0] | (40.0, 60.0] | (60.0, 80.0] | (80.0, 100.0] |
         +------------+-------------+--------------+--------------+--------------+---------------+
         | Bathroom   |    0.000000 |          0.0 |     0.666667 |          1.0 |           1.0 |
         | Corridor   |    0.333333 |          0.5 |     0.000000 |          0.0 |           0.0 |
         | Kitchen    |    0.333333 |          0.0 |     0.333333 |          0.0 |           0.0 |
         | Loggia     |    0.333333 |          0.5 |     0.000000 |          0.0 |           0.0 |
         +------------+-------------+--------------+--------------+--------------+---------------+
    """
    melted_dataframe = dataframe.melt(
        id_vars=group_columns, var_name="dimension", value_name="value"
    )
    column_histogram = (
        melted_dataframe.groupby(
            [
                *group_columns,
                pd.cut(
                    melted_dataframe["value"],
                    bins=bins,
                    labels=labels,
                    include_lowest=True,
                ),
            ]
        )
        .size()
        .unstack()
    )
    column_histogram = column_histogram.loc[(column_histogram != 0).any(axis=1)]

    if use_group_mean:
        num_counts_per_group = pd.DataFrame(
            dataframe.groupby(group_columns).size()
        ).values
        column_histogram = column_histogram / num_counts_per_group

    if normalized == "group":
        num_values_per_group = pd.DataFrame(
            dataframe.groupby(group_columns).count().sum(axis=1)
        ).values
        return column_histogram / num_values_per_group

    if normalized == "bin":
        return (
            column_histogram.T / pd.DataFrame(column_histogram.sum(axis=0)).values
        ).T

    return column_histogram


def archilyse_chart_style(func):
    @wraps(func)
    def _apply_archilyse_chart_style(*args, **kwargs):
        with plt.rc_context(CHART_STYLE):
            return func(*args, **kwargs)

    return _apply_archilyse_chart_style


def load_archilyse_chart_fonts():
    for font_path in FONT_DIR.glob("*.ttf"):
        font_manager.fontManager.addfont(font_path.as_posix())


def find_closest_source_column_and_take_target_column(
    target_dataframe: pd.DataFrame,
    reference_dataframe: pd.DataFrame,
    groupby_columns: list[str],
    source_column: str,
    target_column: str,
):
    """
    For each source value in target_dataframe, finds the maximum value in `source_column` of
    the reference dataframe and replaces it with the target value of reference dataframe.
    """

    adjusted_target_dataframe = pd.DataFrame()
    target_group_dfs = dict(list(target_dataframe.groupby(groupby_columns)))

    for group, reference_group_df in reference_dataframe.groupby(groupby_columns):
        target_group_df = target_group_dfs.get(group)

        if target_group_df is None:
            continue

        indices = reference_group_df[source_column].searchsorted(
            target_group_df[source_column]
        )
        target_group_df[source_column] = (
            reference_group_df.iloc[indices - 1][target_column] * 100
        ).values
        adjusted_target_dataframe = adjusted_target_dataframe.append(target_group_df)

    return adjusted_target_dataframe
