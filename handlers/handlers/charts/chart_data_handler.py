import json
from functools import cached_property, lru_cache
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from common_utils.constants import (
    BENCHMARK_DATASET_CLUSTER_SIZES_PATH,
    BENCHMARK_DATASET_SIMULATIONS_PATH,
    BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH,
    BENCHMARK_PERCENTILES_DIMENSIONS_PATH,
    PRICEHUBBLE_AREA_TYPES,
    RESULT_VECTORS,
)
from common_utils.logger import logger
from handlers.charts.constants import CLUSTER_COLUMNS
from handlers.charts.scoring_handler import ScoringHandler
from handlers.charts.utils import find_closest_source_column_and_take_target_column
from handlers.ph_vector.ph2022 import NeufertResultVectorHandler


class ChartDataHandler:
    _rerference_dataframe = None
    _reference_dataframe_percentiles_per_cluster = None

    def __init__(
        self, site_id: int, use_reference_data_for_target_dataframe: bool = False
    ):
        self.use_reference_data_for_target_dataframe = (
            use_reference_data_for_target_dataframe
        )
        self.site_id = site_id

    @property
    def _unprocessed_target_dataframe(self) -> pd.DataFrame:
        logger.info(f"Loading target dataframe for site {self.site_id}...")
        return pd.DataFrame(
            NeufertResultVectorHandler.generate_vectors(
                site_id=self.site_id, representative_units_only=False, anonymized=False
            )[RESULT_VECTORS.NEUFERT_AREA_SIMULATIONS]
        )

    @property
    def _unprocessed_reference_dataframe(self) -> pd.DataFrame:
        logger.info("Loading reference dataframe...")
        return pd.read_csv(BENCHMARK_DATASET_SIMULATIONS_PATH)

    @cached_property
    def target_dataframe(self) -> pd.DataFrame:
        if (
            self.use_reference_data_for_target_dataframe
            and self.site_id in self.reference_dataframe["site_id"].unique()
        ):
            logger.debug("Loading target dataframe from reference dataframe")
            return self.reference_dataframe[
                self.reference_dataframe["site_id"] == self.site_id
            ].copy()

        # NOTE: The vector uses "None" instead of nan for optional values that are not set
        target_dataframe = self._add_extra_vector_columns(
            self._unprocessed_target_dataframe
        )
        target_dataframe.fillna(value=np.nan, inplace=True)
        dataframe = self._add_extra_room_features_percentile_based(
            dataframe=target_dataframe
        )
        return dataframe

    @cached_property
    def reference_dataframe(self) -> pd.DataFrame:
        if self._rerference_dataframe is None:
            dataframe = self._add_extra_vector_columns(
                self._unprocessed_reference_dataframe
            )
            dataframe = self._add_extra_room_features_percentile_based(
                dataframe=dataframe
            )
            ChartDataHandler._rerference_dataframe = dataframe
        else:
            return self._rerference_dataframe

        return dataframe

    @cached_property
    def reference_sizes(self) -> pd.DataFrame:
        return pd.read_csv(BENCHMARK_DATASET_CLUSTER_SIZES_PATH).set_index(
            CLUSTER_COLUMNS
        )

    @cached_property
    def reference_dataframe_percentiles_per_cluster(self) -> dict:
        if self._reference_dataframe_percentiles_per_cluster is None:
            with BENCHMARK_PERCENTILES_DIMENSIONS_PATH.open() as fh:
                percentile_dimensions = json.load(fh)
                for (
                    apartment_type,
                    area_type_percentiles,
                ) in percentile_dimensions.items():
                    for area_type, percentiles in area_type_percentiles.items():
                        percentile_dimensions[apartment_type][area_type] = pd.DataFrame(
                            percentiles
                        )
            self._reference_dataframe_percentiles_per_cluster = percentile_dimensions

        return self._reference_dataframe_percentiles_per_cluster

    @cached_property
    def apartment_score_bins_dataframe(self) -> pd.DataFrame:
        return pd.read_csv(BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH)

    @lru_cache
    def percentile_dataframe(self, configuration) -> pd.DataFrame:
        return self.get_dataframe_per_room_type_as_cluster_percentiles(
            dataframe=self.target_dataframe,
            output_columns=configuration().columns,
            weights=configuration().column_desirabilities,
        ).rename(columns=configuration().column_names)

    # --------- Add extra vector columns --------- #

    def _add_extra_vector_columns(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe = dataframe.copy()
        self._add_extra_apartment_features(dataframe=dataframe)
        self._add_extra_room_features(dataframe=dataframe)
        self._add_apartment_cluster_columns(dataframe=dataframe)

        return dataframe

    @staticmethod
    def _add_extra_apartment_features(dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe["apartment_aggregate_room_count"] = dataframe.groupby("apartment_id")[
            ["layout_room_count"]
        ].transform("sum")
        dataframe["apartment_aggregate_net_area"] = dataframe.groupby("apartment_id")[
            ["layout_net_area"]
        ].transform("sum")
        dataframe["apartment_aggregate_floor_number"] = dataframe.groupby(
            "apartment_id"
        )[["floor_number"]].transform("min")
        dataframe["apartment_aggregate_is_maisonette"] = (
            dataframe.groupby("apartment_id")[["floor_number"]].transform("nunique") > 1
        )
        return dataframe

    @staticmethod
    def _add_extra_room_features(dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe["room_aggregate_largest_rectangle_area"] = (
            dataframe["layout_biggest_rectangle_width"]
            * dataframe["layout_biggest_rectangle_length"]
        )
        dataframe["room_aggregate_area_share"] = dataframe[
            "layout_area"
        ] / dataframe.groupby("apartment_id")["layout_area"].transform("sum")

        dataframe["room_name"] = (
            dataframe["layout_area_type"]
            + " "
            + dataframe["layout_area"].round(0).astype(int).astype(str)
            + "m²"
        )
        return dataframe

    def _add_extra_room_features_percentile_based(
        self, dataframe: pd.DataFrame
    ) -> pd.DataFrame:
        percentile_columns = [
            "layout_open_perimeter",
            "sun_201803211200_p80",
            "sun_201806211200_p80",
            "window_noise_traffic_day_max",
            "connectivity_eigen_centrality_p80",
            "connectivity_closeness_centrality_p80",
            "connectivity_betweenness_centrality_p80",
            "connectivity_entrance_door_distance_p80",
            "connectivity_room_distance_p20",
            "connectivity_living_dining_distance_p20",
            "connectivity_bathroom_distance_p20",
            "connectivity_kitchen_distance_p20",
            "connectivity_balcony_distance_p20",
            "connectivity_loggia_distance_p20",
        ]

        percentile_dataframe = self.get_dataframe_per_room_type_as_cluster_percentiles(
            dataframe=dataframe,
            output_columns=percentile_columns,
            index_columns=tuple(["index"]),
        )

        dataframe["room_aggregate_privacy"] = (
            percentile_dataframe["connectivity_entrance_door_distance_p80"]
            * (100 - percentile_dataframe["connectivity_betweenness_centrality_p80"])
            * (100 - percentile_dataframe["layout_open_perimeter"])
        )

        dataframe["room_aggregate_heat_risk"] = (
            percentile_dataframe["sun_201803211200_p80"]
            * percentile_dataframe["sun_201806211200_p80"]
            * percentile_dataframe["window_noise_traffic_day_max"]
        )

        dataframe["room_aggregate_seclusion"] = (
            (100 - percentile_dataframe["connectivity_eigen_centrality_p80"])
            * (100 - percentile_dataframe["connectivity_closeness_centrality_p80"])
            * (100 - percentile_dataframe["connectivity_betweenness_centrality_p80"])
        )

        dataframe[
            "room_aggregate_functional_accessibility"
        ] = percentile_dataframe.apply(self._functional_accessibility, axis=1)

        return dataframe

    def _functional_accessibility(self, row):
        match row["layout_area_type"]:
            case PRICEHUBBLE_AREA_TYPES.ROOM.value | PRICEHUBBLE_AREA_TYPES.KITCHEN_DINING.value:
                factors = [
                    "connectivity_bathroom_distance_p20",
                    "connectivity_kitchen_distance_p20",
                ]
            case PRICEHUBBLE_AREA_TYPES.BATHROOM.value:
                factors = [
                    "connectivity_room_distance_p20",
                    "connectivity_living_dining_distance_p20",
                ]
            case PRICEHUBBLE_AREA_TYPES.KITCHEN.value:
                factors = [
                    "connectivity_room_distance_p20",
                    "connectivity_living_dining_distance_p20",
                    "connectivity_balcony_distance_p20",
                    "connectivity_loggia_distance_p20",
                ]
            case PRICEHUBBLE_AREA_TYPES.BALCONY.value | PRICEHUBBLE_AREA_TYPES.LOGGIA.value | PRICEHUBBLE_AREA_TYPES.WINTERGARTEN.value:
                factors = [
                    "connectivity_room_distance_p20",
                    "connectivity_living_dining_distance_p20",
                    "connectivity_kitchen_distance_p20",
                ]
            case PRICEHUBBLE_AREA_TYPES.CORRIDOR.value:
                factors = [
                    "connectivity_bathroom_distance_p20",
                    "connectivity_kitchen_distance_p20",
                ]
            case PRICEHUBBLE_AREA_TYPES.STOREROOM.value:
                factors = ["connectivity_kitchen_distance_p20"]
            case _:
                logger.warning(row["layout_area_type"])
                factors = []

        result = 1
        for factor in factors:
            result *= 100 - row[factor]

        return result

    @staticmethod
    def _add_apartment_cluster_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
        dataframe["tmp_is_building_max_floor"] = dataframe.groupby("apartment_id")[
            "floor_number"
        ].transform("max") == dataframe.groupby("building_id")[
            "floor_number"
        ].transform(
            "max"
        )

        dataframe["tmp_room_cluster"] = dataframe[
            ["apartment_aggregate_room_count"]
        ].replace(
            {
                "apartment_aggregate_room_count": {
                    room_count: f"{int(room_count)}.X" if room_count < 6 else "7+.X"
                    for room_count in dataframe["apartment_aggregate_room_count"].values
                }
            }
        )[
            "apartment_aggregate_room_count"
        ]

        dataframe["tmp_floor_cluster"] = ""
        dataframe.loc[
            dataframe[dataframe["tmp_is_building_max_floor"]].index,
            "tmp_floor_cluster",
        ] = "TOP_LEVEL"
        dataframe.loc[
            dataframe[dataframe["apartment_aggregate_floor_number"] == 0].index,
            "tmp_floor_cluster",
        ] = "GROUND_LEVEL"
        dataframe.loc[
            dataframe[dataframe["tmp_floor_cluster"] == ""].index, "tmp_floor_cluster"
        ] = "MEDIUM_LEVEL"
        dataframe["apartment_aggregate_cluster"] = dataframe[
            ["tmp_floor_cluster", "tmp_room_cluster"]
        ].agg("_".join, axis=1)

        dataframe.drop(
            ["tmp_is_building_max_floor", "tmp_room_cluster", "tmp_floor_cluster"],
            axis="columns",
            inplace=True,
        )

        return dataframe

    # --------- Percentiles --------- #

    def get_dataframe_per_room_type_as_cluster_percentiles(
        self,
        dataframe: pd.DataFrame,
        output_columns: List[str],
        index_columns: Tuple = (
            "site_id",
            "building_id",
            "floor_id",
            "floor_number",
            "apartment_aggregate_room_count",
            "apartment_id",
            "area_id",
            "room_name",
        ),
        weights: Optional[dict] = None,
    ) -> pd.DataFrame:
        percentiles_dataframe = pd.DataFrame(
            columns=CLUSTER_COLUMNS + output_columns + list(index_columns)
        )
        for (apartment_type, area_type), df in dataframe.groupby(CLUSTER_COLUMNS):
            reference_percentiles = self.reference_dataframe_percentiles_per_cluster[
                apartment_type
            ][area_type]
            for column in output_columns:
                # NOTE: We always order such that apartment has "good" quality rather than bad quality
                #       e.g. lets say 20% of rooms have a water view of 0, then the score of all these
                #       rooms in the water dimension is 20. However, if 20% of rooms have no railway_track view
                #       then all these rooms have score 80 (because weight = -1).
                indices = (
                    reference_percentiles[column]
                    .searchsorted(
                        df[column],
                        side="right" if not weights or weights[column] > 0 else "left",
                    )
                    .clip(1, 100)
                )
                df[column] = (
                    reference_percentiles.index[indices - 1].values.astype(float) * 100
                )
                if weights:
                    df[column] *= weights[column]
                    if weights[column] < 0:
                        df[column] = 100 + df[column]

            df.reset_index(inplace=True)
            percentiles_dataframe = percentiles_dataframe.append(
                df[CLUSTER_COLUMNS + output_columns + list(index_columns)]
            )

        percentiles_dataframe.set_index(list(index_columns), drop=True, inplace=True)
        return percentiles_dataframe

    # --------- Entity Quality Distributions --------- #

    @lru_cache
    def area_quality_distribution_dataframe(self, configuration) -> pd.DataFrame:
        dataframe = ScoringHandler.get_quality_level_counts_per_group(
            dataframe=self.percentile_dataframe(configuration=configuration),
            group_columns=["apartment_id", "room_name"],
            quality_level_labels=ScoringHandler.SCORE_LABELS,
        )

        return dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)

    @lru_cache
    def area_type_quality_distribution_dataframe(self, configuration) -> pd.DataFrame:
        dataframe = ScoringHandler.get_quality_level_counts_per_group(
            dataframe=self.percentile_dataframe(configuration=configuration),
            group_columns=["apartment_id", "layout_area_type"],
            quality_level_labels=ScoringHandler.SCORE_LABELS,
        )

        return dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)

    @lru_cache
    def apartment_area_type_quality_frequencies_dataframe(
        self, configuration
    ) -> pd.DataFrame:
        dataframe = (
            self.area_type_quality_distribution_dataframe(configuration=configuration)
            .groupby("apartment_id")
            .sum()
        )

        return dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)

    @lru_cache
    def building_area_type_quality_distribution_dataframe(
        self, configuration
    ) -> pd.DataFrame:
        dataframe = (
            self.apartment_scores_adjusted(configuration=configuration)
            .merge(self.target_dataframe, on="apartment_id")[
                ["building_id", "apartment_id", "score"]
            ]
            .drop_duplicates()
            .set_index(["building_id", "apartment_id"], drop=True)
        )

        dataframe = ScoringHandler.get_quality_level_counts_per_group(
            dataframe=dataframe,
            group_columns=["building_id", "apartment_id"],
            quality_level_labels=ScoringHandler.SCORE_LABELS,
        )
        dataframe = dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)
        dataframe = dataframe.groupby("building_id").sum()
        return dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)

    @lru_cache
    def floor_area_type_quality_distribution_dataframe(
        self, configuration
    ) -> pd.DataFrame:
        dataframe = ScoringHandler.get_quality_level_counts_per_group(
            dataframe=self.apartment_scores_adjusted(configuration=configuration)
            .merge(self.target_dataframe, on="apartment_id")[
                ["floor_id", "apartment_id", "score"]
            ]
            .drop_duplicates()
            .set_index(["floor_id", "apartment_id"], drop=True),
            group_columns=["floor_id", "apartment_id"],
            quality_level_labels=ScoringHandler.SCORE_LABELS,
        )
        dataframe = dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)
        dataframe = dataframe.groupby("floor_id").sum()
        return dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)

    @lru_cache
    def room_count_area_type_quality_distribution_dataframe(
        self, configuration
    ) -> pd.DataFrame:

        dataframe = ScoringHandler.get_quality_level_counts_per_group(
            dataframe=self.apartment_scores_adjusted(configuration=configuration)
            .merge(self.target_dataframe, on="apartment_id")[
                ["apartment_aggregate_room_count", "apartment_id", "score"]
            ]
            .drop_duplicates()
            .set_index(["apartment_aggregate_room_count", "apartment_id"], drop=True),
            group_columns=["apartment_aggregate_room_count", "apartment_id"],
            quality_level_labels=ScoringHandler.SCORE_LABELS,
        )
        dataframe = dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)
        dataframe = dataframe.groupby("apartment_aggregate_room_count").sum()
        return dataframe.apply(lambda z: z / dataframe.sum(axis=1).values)

    @lru_cache
    def building_cluster_quality_distribution_dataframe(
        self, configuration
    ) -> pd.DataFrame:
        return ScoringHandler.get_quality_level_counts_per_group(
            dataframe=self.building_cluster_apartment_scores(
                configuration=configuration
            ),
            group_columns=["building_id", "apartment_aggregate_cluster"],
            quality_level_labels=ScoringHandler.SCORE_LABELS,
        )

    # --------- Entity Scores --------- #

    @lru_cache
    def area_scores(self, configuration) -> pd.DataFrame:
        return (
            pd.DataFrame(
                ScoringHandler._score(
                    dataframe=self.area_quality_distribution_dataframe(
                        configuration=configuration
                    )
                ),
                columns=["score"],
            )
            * 100.0
        )

    @lru_cache
    def apartment_area_type_scores(self, configuration) -> pd.DataFrame:
        return (
            pd.DataFrame(
                ScoringHandler._score(
                    dataframe=self.area_type_quality_distribution_dataframe(
                        configuration=configuration
                    )
                ),
                columns=["score"],
            )
            * 100.0
        )

    @lru_cache
    def apartment_scores(self, configuration) -> pd.DataFrame:
        return (
            pd.DataFrame(
                ScoringHandler._score(
                    dataframe=self.apartment_area_type_quality_frequencies_dataframe(
                        configuration=configuration
                    )
                ),
                columns=["score"],
            )
            * 100.0
        )

    @lru_cache
    def apartment_scores_adjusted(self, configuration) -> pd.DataFrame:
        apartment_scores_dataframe = self.apartment_scores(
            configuration=configuration
        ).merge(
            self.target_dataframe[
                ["apartment_id", CLUSTER_COLUMNS[0]]
            ].drop_duplicates(),
            on=["apartment_id"],
            how="left",
        )[
            ["apartment_id", CLUSTER_COLUMNS[0], "score"]
        ]

        return (
            find_closest_source_column_and_take_target_column(
                target_dataframe=apartment_scores_dataframe.drop_duplicates(),
                reference_dataframe=self.apartment_score_bins_dataframe[
                    self.apartment_score_bins_dataframe["configuration"]
                    == configuration.__name__
                ],
                groupby_columns=[CLUSTER_COLUMNS[0]],
                source_column="score",
                target_column="percentile",
            )[["apartment_id", "score"]]
            .drop_duplicates()
            .set_index("apartment_id")
        )

    @lru_cache
    def building_scores(self, configuration) -> pd.DataFrame:
        dataframe = self.building_area_type_quality_distribution_dataframe(
            configuration=configuration
        )
        return (
            pd.DataFrame(
                ScoringHandler._score(
                    dataframe=dataframe.apply(
                        lambda z: z / dataframe.sum(axis=1).values
                    )
                ),
                columns=["score"],
            )
            * 100.0
        )

    @lru_cache
    def floor_scores(self, configuration) -> pd.DataFrame:
        dataframe = self.floor_area_type_quality_distribution_dataframe(
            configuration=configuration
        )
        return (
            pd.DataFrame(
                ScoringHandler._score(
                    dataframe=dataframe.apply(
                        lambda z: z / dataframe.sum(axis=1).values
                    )
                ),
                columns=["score"],
            )
            * 100.0
        )

    @lru_cache
    def room_count_scores(self, configuration) -> pd.DataFrame:
        dataframe = self.room_count_area_type_quality_distribution_dataframe(
            configuration=configuration
        )
        return (
            pd.DataFrame(
                ScoringHandler._score(
                    dataframe=dataframe.apply(
                        lambda z: z / dataframe.sum(axis=1).values
                    )
                ),
                columns=["score"],
            )
            * 100.0
        )

    @lru_cache
    def building_cluster_apartment_scores(self, configuration):
        return (
            self.percentile_dataframe(configuration=configuration)
            .reset_index()[
                ["building_id", "apartment_aggregate_cluster", "apartment_id"]
            ]
            .drop_duplicates()
            .set_index(["building_id", "apartment_aggregate_cluster", "apartment_id"])
            .merge(
                self.apartment_scores_adjusted(configuration=configuration),
                left_index=True,
                right_index=True,
            )
            .reset_index()
            .set_index(["building_id", "apartment_aggregate_cluster"])[["score"]]
        )
