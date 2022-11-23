from common_utils.constants import BENCHMARK_DATASET_CLUSTER_SIZES_PATH
from handlers.charts.chart_data_handler import ChartDataHandler
from handlers.charts.constants import CLUSTER_COLUMNS

reference_dataframe = ChartDataHandler(site_id=1).reference_dataframe
reference_sizes = reference_dataframe.groupby(CLUSTER_COLUMNS).count()[["area_id"]]
reference_sizes.to_csv(BENCHMARK_DATASET_CLUSTER_SIZES_PATH)
