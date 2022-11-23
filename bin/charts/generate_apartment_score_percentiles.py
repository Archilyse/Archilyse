import random
from collections import defaultdict

import numpy as np
import pandas as pd
from tqdm import tqdm

from common_utils.constants import BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH
from handlers.charts.chart_data_handler import ChartDataHandler
from handlers.charts.constants import (
    CLUSTER_COLUMNS,
    AllDimensionsSimulationCategoryConfiguration,
    CentralitySimulationCategoryConfiguration,
    NoiseSimulationCategoryConfiguration,
    RoomLayoutSimulationCategoryConfiguration,
    SunSimulationCategoryConfiguration,
    ViewSimulationCategoryConfiguration,
)

DEFAULT_CATEGORIES = {
    ViewSimulationCategoryConfiguration,
    SunSimulationCategoryConfiguration,
    NoiseSimulationCategoryConfiguration,
    CentralitySimulationCategoryConfiguration,
    RoomLayoutSimulationCategoryConfiguration,
    AllDimensionsSimulationCategoryConfiguration,
}

random.seed(42)
handler = ChartDataHandler(site_id=1)
reference_dataframe = handler.reference_dataframe
reference_dataframe_percentiles_per_cluster = (
    handler.reference_dataframe_percentiles_per_cluster
)
site_ids = list(reference_dataframe["site_id"].unique())
random.shuffle(site_ids)

handlers = {}
apartment_scores = defaultdict(dict)


def _load_site(site_id):
    ChartDataHandler._reference_dataframe = reference_dataframe
    ChartDataHandler._reference_dataframe_percentiles_per_cluster = (
        reference_dataframe_percentiles_per_cluster
    )
    handler = ChartDataHandler(
        site_id=site_id, use_reference_data_for_target_dataframe=True
    )
    for category in DEFAULT_CATEGORIES:
        apartment_scores[site_id][category] = handler.apartment_area_type_scores(
            configuration=category
        )
    return handler


for site_id, handler in [(site_id, _load_site(site_id)) for site_id in tqdm(site_ids)]:
    handlers[site_id] = handler

category_dfs = []
for category in DEFAULT_CATEGORIES:
    category_df = pd.concat(
        [apartment_scores[site_id][category] for site_id in apartment_scores]
    )
    category_df["configuration"] = category.__name__
    category_dfs.append(category_df)

apartment_score_df = pd.concat(category_dfs).merge(
    reference_dataframe[["apartment_id", *CLUSTER_COLUMNS]],
    on=["apartment_id"],
    how="left",
)
apartment_score_bins = pd.DataFrame()
for cluster_group, df in apartment_score_df.groupby(
    ["configuration", *CLUSTER_COLUMNS]
):
    bins = df[["score"]].quantile(q=np.arange(0, 1, 0.01))
    bins[["configuration", *CLUSTER_COLUMNS]] = cluster_group
    apartment_score_bins = apartment_score_bins.append(bins)

apartment_score_bins.reset_index(inplace=True)
apartment_score_bins.rename({"index": "percentile"}, axis="columns", inplace=True)
apartment_score_bins.to_csv(BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH)
