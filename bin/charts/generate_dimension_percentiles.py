import json
from collections import defaultdict

import numpy as np

from common_utils.constants import BENCHMARK_PERCENTILES_DIMENSIONS_PATH
from handlers.charts.chart_data_handler import ChartDataHandler
from handlers.charts.constants import CLUSTER_COLUMNS

handler = ChartDataHandler(site_id=1)


def compute_percentiles(reference_dataframe):
    reference_dataframe_ranks = defaultdict(dict)
    for cluster_group, df in reference_dataframe.groupby([*CLUSTER_COLUMNS]):
        reference_dataframe_ranks[cluster_group[0]][cluster_group[1]] = (
            df.select_dtypes(include=np.number)
            .quantile(q=np.arange(0, 1, 0.01))
            .to_dict()
        )

    with BENCHMARK_PERCENTILES_DIMENSIONS_PATH.open("w") as fh:
        json.dump(reference_dataframe_ranks, fh)


# NOTE: We need two passes because the final dataframe requires percentiles of the original
#       columns to be computed already.
compute_percentiles(
    reference_dataframe=handler._add_extra_vector_columns(
        dataframe=handler._unprocessed_reference_dataframe
    )
)
compute_percentiles(reference_dataframe=handler.reference_dataframe)
