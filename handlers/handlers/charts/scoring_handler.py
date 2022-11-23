from typing import List, Optional

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype

from handlers.charts.utils import histogram_per_group


class ScoringHandler:
    SCORE_LABELS = [
        "Lowest",
        "Below\nAverage",
        "Average",
        "Above\nAverage",
        "Highest",
    ]

    @classmethod
    def get_quality_level_counts_per_group(
        cls,
        dataframe: pd.DataFrame,
        group_columns: List[str] | str,
        only_quality_distribution: bool = False,
        quality_level_labels: Optional[List[str]] = None,
    ):
        """
        Returns a dataframe that gives for each group (based on group_columns) the number of
        dataframe cells with quality level 'Lowest', 'Below Average', 'Average', 'Above Average'
        and 'Highest.

        Note that each dataframe cell should be within 0 and 100 where a uniform distribution (average 50)
        is assumed.
        """
        if isinstance(group_columns, str):
            group_columns = [group_columns]

        columns = group_columns + [
            column
            for column in dataframe.columns
            if is_numeric_dtype(dataframe[column])
        ]

        quality_level_counts_per_group = histogram_per_group(
            dataframe=dataframe.reset_index()[columns].dropna(axis=1, how="all"),
            group_columns=group_columns,
            bins=np.linspace(0, 100, 6),
            labels=quality_level_labels,
        )

        if only_quality_distribution:
            frequency_per_quality_level = (
                quality_level_counts_per_group.sum(axis=0)
                .reset_index()
                .rename(columns={"value": "quality", 0: "frequency"})
            )
            frequency_per_quality_level["frequency"] /= frequency_per_quality_level[
                "frequency"
            ].sum(axis=0)
            return frequency_per_quality_level

        return quality_level_counts_per_group

    @staticmethod
    def _score(dataframe: pd.DataFrame, groupby=None):
        return ((dataframe * [-3, 1, 0, 1, 3]).sum(axis=1) + 3) / 6
