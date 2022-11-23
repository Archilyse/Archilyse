from functools import cached_property
from pathlib import Path
from typing import Iterator, Tuple, Type

import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm

from common_utils.constants import UNIT_USAGE
from handlers.charts.chart import ArchilyseChart
from handlers.charts.chart_data_handler import ChartDataHandler
from handlers.charts.chart_handler import ChartHandler
from handlers.charts.constants import (
    CLUSTER_COLUMNS,
    AllDimensionsSimulationCategoryConfiguration,
    CentralitySimulationCategoryConfiguration,
    ChartType,
    NoiseSimulationCategoryConfiguration,
    RoomLayoutSimulationCategoryConfiguration,
    SimulationCategoryConfiguration,
    SunSimulationCategoryConfiguration,
    ViewSimulationCategoryConfiguration,
)
from handlers.charts.scoring_handler import ScoringHandler
from handlers.charts.utils import archilyse_chart_style, load_archilyse_chart_fonts
from handlers.db import BuildingDBHandler, UnitDBHandler


class ApartmentChartGenerator:
    DEFAULT_CHART_CONFIGURATIONS = {
        ViewSimulationCategoryConfiguration,
        SunSimulationCategoryConfiguration,
        NoiseSimulationCategoryConfiguration,
        CentralitySimulationCategoryConfiguration,
        RoomLayoutSimulationCategoryConfiguration,
    }

    INDEX_COLUMN_ORDER = [
        "apartment_id",
        "city",
        "street",
        "housenumber",
        "floor_number",
        "is_maisonette",
        "room_count",
        "net_area",
        "All",
        "View",
        "Daylight",
        "Noise",
        "Accessibility",
        "Layout",
    ]

    def __init__(self, site_id: int, output_dir: Path):
        self.site_id = site_id
        self.output_dir = output_dir
        self.thumbnail_dir = output_dir.joinpath("Preview")
        self.data_handler = ChartDataHandler(site_id=site_id)
        load_archilyse_chart_fonts()

    def generate_default_charts(self):
        for building_id in tqdm(self.building_infos):
            for (
                configuration,
                chart_type,
                chart_path,
                thumbnail_path,
            ) in self.get_building_chart_paths(building_id=building_id):
                chart = self.generate_building_chart(
                    building_id=building_id,
                    configuration=configuration,
                    chart_type=chart_type,
                )
                chart.savefig(chart_path.as_posix())
                chart.savefig(thumbnail_path.as_posix() + ".png", dpi=10)

        for apartment_id in tqdm(self.apartment_ids):
            for (
                configuration,
                chart_type,
                chart_path,
                thumbnail_path,
            ) in self.get_apartment_chart_paths(apartment_id=apartment_id):
                chart = self.generate_apartment_chart(
                    apartment_id=apartment_id,
                    configuration=configuration,
                    chart_type=chart_type,
                )
                chart.savefig(chart_path.as_posix())
                chart.savefig(thumbnail_path.as_posix() + ".png", dpi=10)

    def generate_default_chart_index(self):
        index = []
        for apartment_id in tqdm(sorted(self.apartment_ids)):
            apartment_row = self.get_metadata_dict(apartment_id=apartment_id)
            for (
                configuration,
                _,
                chart_path,
                thumbnail_path,
            ) in self.get_apartment_chart_paths(apartment_id=apartment_id):
                relative_chart_path = chart_path.relative_to(self.output_dir)
                relative_thumbnail_path = thumbnail_path.relative_to(self.output_dir)
                apartment_row[
                    configuration().category_name
                ] = f"<a href='{relative_chart_path.as_posix()}'><img src='{relative_thumbnail_path.as_posix()}.png' /><a/>"

            index.append(apartment_row)

        index_df = pd.DataFrame(index)
        index_df = index_df.reindex(columns=self.INDEX_COLUMN_ORDER)
        index_df = index_df.sort_values(self.INDEX_COLUMN_ORDER[1:])
        index_df.to_html(self.output_dir.joinpath("index.html"), escape=False)

    def generate_default_data_sheets(self):
        percentiles = self.data_handler.percentile_dataframe(
            configuration=AllDimensionsSimulationCategoryConfiguration
        ).reset_index()

        score_index = []
        for apartment_id in sorted(self.apartment_ids):
            apartment_row = self.get_metadata_dict(apartment_id=apartment_id)
            for configuration in [
                AllDimensionsSimulationCategoryConfiguration,
                *self.DEFAULT_CHART_CONFIGURATIONS,
            ]:
                apartment_row[
                    f"{configuration().category_name} Score"
                ] = self.data_handler.apartment_scores_adjusted(
                    configuration=configuration
                ).loc[
                    apartment_id
                ][
                    "score"
                ]
            score_index.append(apartment_row)

        pd.DataFrame(score_index).to_csv(
            self.output_dir.joinpath("apartment_scores.csv"), index=None
        )
        pd.DataFrame(percentiles).to_csv(
            self.output_dir.joinpath("area_percentiles.csv"), index=None
        )

    def generate_apartment_chart(
        self,
        apartment_id: str,
        configuration: Type[SimulationCategoryConfiguration],
        chart_type: ChartType,
    ) -> ArchilyseChart:
        chart_type_to_method = {
            ChartType.UNIT_ROOM_SUMMARY: self.unit_room_summary,
            ChartType.UNIT_SUMMARY: self.unit_summary,
        }

        return chart_type_to_method[chart_type](
            apartment_id=apartment_id,
            configuration=configuration,
        )

    def generate_building_chart(
        self,
        building_id: str,
        configuration: Type[SimulationCategoryConfiguration],
        chart_type: ChartType,
    ) -> ArchilyseChart:
        chart_type_to_method = {
            ChartType.BUILDING_SUMMARY: self.building_summary,
        }

        return chart_type_to_method[chart_type](
            building_id=building_id,
            configuration=configuration,
        )

    def get_apartment_chart_paths(
        self, apartment_id: str
    ) -> Iterator[Tuple[Type[SimulationCategoryConfiguration], ChartType, Path, Path]]:
        metadata = self.get_metadata_dict(apartment_id=apartment_id)
        subfolder = f"{metadata['street']} {metadata['housenumber']}/{metadata['room_count']} Rooms/{apartment_id}"

        apartment_dir = self.output_dir.joinpath(subfolder)
        apartment_dir.mkdir(parents=True, exist_ok=True)

        apartment_thumbnail_dir = self.thumbnail_dir.joinpath(subfolder)
        apartment_thumbnail_dir.mkdir(parents=True, exist_ok=True)

        for configuration in self.DEFAULT_CHART_CONFIGURATIONS:
            yield (
                configuration,
                ChartType.UNIT_ROOM_SUMMARY,
                apartment_dir.joinpath(f"{configuration().category_name}.pdf"),
                apartment_thumbnail_dir.joinpath(
                    f"{configuration().category_name}.pdf"
                ),
            )

        yield (
            AllDimensionsSimulationCategoryConfiguration,
            ChartType.UNIT_SUMMARY,
            apartment_dir.joinpath("Summary.pdf"),
            apartment_thumbnail_dir.joinpath("Summary.pdf"),
        )

    def get_building_chart_paths(
        self, building_id: int
    ) -> Iterator[Tuple[Type[SimulationCategoryConfiguration], ChartType, Path, Path]]:
        street = self.building_infos[building_id]["street"]
        housenumber = self.building_infos[building_id]["housenumber"]
        building_dir = self.output_dir.joinpath(f"{street} {housenumber}")
        building_dir.mkdir(parents=True, exist_ok=True)

        thumbnail_building_dir = self.thumbnail_dir.joinpath(f"{street} {housenumber}")
        thumbnail_building_dir.mkdir(parents=True, exist_ok=True)

        yield (
            AllDimensionsSimulationCategoryConfiguration,
            ChartType.BUILDING_SUMMARY,
            building_dir.joinpath("Building Summary.pdf"),
            thumbnail_building_dir.joinpath("Building Summary.pdf"),
        )

    # --------- Cached Properties --------- #

    @cached_property
    def building_infos(self):
        return {
            building["id"]: building
            for building in BuildingDBHandler.find_in(
                id=[
                    int(x)
                    for x in self.data_handler.target_dataframe["building_id"].unique()
                ]
            )
        }

    @cached_property
    def apartment_ids(self):
        return {
            unit["client_id"]
            for unit in list(
                UnitDBHandler.find(
                    site_id=self.site_id, unit_usage=UNIT_USAGE.RESIDENTIAL
                )
            )
        }

    # --------- Chart Types --------- #

    @staticmethod
    def make_archilyse_chart(
        title: str, subtitle: str, bottom_left: str
    ) -> ArchilyseChart:
        # NOTE: This method is being used to use the clear() method of plt.figure() correctly
        #       which clears the figure after initialization and avoids a memory leak.
        #       If the title etc. are being added inside ArchilyseChart.__init__ they fall
        #       victim to this memory reset.
        figure = plt.figure(
            FigureClass=ArchilyseChart,
            figsize=(ArchilyseChart.FIG_WIDTH_INCHES, ArchilyseChart.FIG_HEIGHT_INCHES),
            dpi=ArchilyseChart.DPI,
            num=1,
            clear=True,
        )

        figure.add_title(text=title)
        figure.add_subtitle(text=subtitle)
        figure.add_bottom_texts(
            text_left=bottom_left,
            text_right="Copyright © Archilyse 2022. All rights reserved.",
        )

        return figure

    @archilyse_chart_style
    def unit_room_summary(
        self,
        apartment_id: str,
        configuration: Type[SimulationCategoryConfiguration],
    ) -> ArchilyseChart:
        # --------- Data --------- #

        percentile_dataframe = self.data_handler.percentile_dataframe(
            configuration=configuration  # type: ignore
        )
        area_type_quality_distribution_dataframe = self.data_handler.area_type_quality_distribution_dataframe(
            configuration=configuration  # type: ignore
        )
        area_type_score_dataframe = self.data_handler.apartment_area_type_scores(
            configuration=configuration  # type: ignore
        )
        apartment_area_type_quality_distribution_dataframe = self.data_handler.apartment_area_type_quality_frequencies_dataframe(
            configuration=configuration  # type: ignore
        )
        apartment_scores = self.data_handler.apartment_scores_adjusted(
            configuration=configuration  # type: ignore
        )

        # --------- Layout --------- #

        figure = self.make_archilyse_chart(
            title=f"Unit {configuration().category_name} Analysis",
            subtitle=self.get_metadata_string(apartment_id=apartment_id),
            bottom_left=self.get_clustersize_string(
                apartment_dataframe=percentile_dataframe[
                    percentile_dataframe.index.get_level_values("apartment_id")
                    == apartment_id
                ]
            ),
        )

        gs = figure.add_gridspec(
            ncols=4,
            nrows=2,
            left=figure.MAIN_AXIS[0] * figure.DX,
            bottom=figure.MAIN_AXIS[1] * figure.DY,
            right=(figure.MAIN_AXIS[0] + figure.MAIN_AXIS[2]) * figure.DX,
            top=(figure.MAIN_AXIS[1] + figure.MAIN_AXIS[3]) * figure.DY,
        )
        ax_parallel = figure.add_subplot(gs[:, :-1])
        ax_donut = figure.add_subplot(gs[0, -1])
        ax_bar = figure.add_subplot(gs[1, -1])

        # --------- Individual Charts --------- #

        # Parallel Coordinates
        parallel_coordinate_dataframe = (
            percentile_dataframe[
                percentile_dataframe.index.get_level_values("apartment_id")
                == apartment_id
            ]
            .dropna(axis=1, how="all")
            .drop(CLUSTER_COLUMNS, axis="columns")
            .reset_index("room_name")
        )
        ChartHandler.parallel_coordinates(
            dataframe=parallel_coordinate_dataframe,
            group_column="room_name",
            ax=ax_parallel,
            ylim=(0, 100),
            ytickcolors=ChartHandler.CMAP_5,
            yticklabels=tuple([label for label in ScoringHandler.SCORE_LABELS]),
        )

        # Bar Chart
        barchart_dataframe = (
            area_type_quality_distribution_dataframe[
                area_type_quality_distribution_dataframe.index.get_level_values(
                    "apartment_id"
                )
                == apartment_id
            ]
            .reset_index()
            .set_index("layout_area_type")
            .drop("apartment_id", axis=1)
            .dropna(axis=1, how="all")
        )

        scores = (
            area_type_score_dataframe[
                area_type_score_dataframe.index.get_level_values("apartment_id")
                == apartment_id
            ]
            .reset_index()
            .set_index("layout_area_type")
            .drop("apartment_id", axis=1)
            .sort_values("score", ascending=False)
        )
        scores_filtered = pd.concat([scores[:2], scores[-2:]])

        ChartHandler.bar_chart(
            dataframe=barchart_dataframe.loc[scores_filtered.index],
            scores=scores_filtered["score"] / 100.0,
            ax=ax_bar,
        )
        ax_bar.set_title("Strongest and Weakest Area Type", fontsize=28)

        # Donut Chart (Score)
        donut_dataframe = apartment_area_type_quality_distribution_dataframe[
            apartment_area_type_quality_distribution_dataframe.index.get_level_values(
                "apartment_id"
            )
            == apartment_id
        ].dropna(axis=1, how="all")

        ChartHandler.donut_chart(
            dataframe=donut_dataframe.T.reset_index().rename(
                columns={"value": "quality", apartment_id: "frequency"}
            ),
            group_column="quality",
            value_column="frequency",
            score=apartment_scores.loc[apartment_id].values[0] / 100,
            ax=ax_donut,
        )
        ax_donut.set_title("Holistic Performance Percentile", fontsize=28)

        return figure

    @archilyse_chart_style
    def unit_summary(
        self,
        apartment_id: str,
        configuration: Type[AllDimensionsSimulationCategoryConfiguration],
    ):
        # --------- Data --------- #

        percentile_dataframe = self.data_handler.percentile_dataframe(
            configuration=configuration  # type: ignore
        )
        area_quality_distribution_dataframe = self.data_handler.area_quality_distribution_dataframe(
            configuration=configuration  # type: ignore
        )

        area_scores = self.data_handler.area_scores(configuration=configuration)  # type: ignore

        apartment_area_type_quality_distribution_dataframe = self.data_handler.apartment_area_type_quality_frequencies_dataframe(
            configuration=configuration  # type: ignore
        )
        apartment_scores = self.data_handler.apartment_scores_adjusted(
            configuration=configuration  # type: ignore
        )

        # --------- Layout --------- #

        figure = self.make_archilyse_chart(
            title="Unit Analysis Summary",
            subtitle=self.get_metadata_string(apartment_id=apartment_id),
            bottom_left=self.get_clustersize_string(
                apartment_dataframe=percentile_dataframe[
                    percentile_dataframe.index.get_level_values("apartment_id")
                    == apartment_id
                ]
            ),
        )

        gs = figure.add_gridspec(
            ncols=60,
            nrows=17,
            left=figure.MAIN_AXIS[0] * figure.DX,
            bottom=figure.MAIN_AXIS[1] * figure.DY,
            right=(figure.MAIN_AXIS[0] + figure.MAIN_AXIS[2]) * figure.DX,
            top=(figure.MAIN_AXIS[1] + figure.MAIN_AXIS[3]) * figure.DY,
        )
        top_left = figure.add_subplot(gs[:9, :18])
        top_right = figure.add_subplot(gs[:17, 20:46])
        bottom_left_top_left = figure.add_subplot(gs[9:13, :6])
        bottom_left_top_center = figure.add_subplot(gs[9:13, 6:12])
        bottom_left_top_right = figure.add_subplot(gs[9:13, 12:18])
        bottom_left_bottom_left = figure.add_subplot(gs[13:17, 3:9])
        bottom_left_bottom_right = figure.add_subplot(gs[13:17, 9:15])

        # --------- Charts --------- #

        # Donut
        donut_dataframe = apartment_area_type_quality_distribution_dataframe[
            apartment_area_type_quality_distribution_dataframe.index.get_level_values(
                "apartment_id"
            )
            == apartment_id
        ]
        ChartHandler.donut_chart(
            dataframe=donut_dataframe.T.reset_index().rename(
                columns={"value": "quality", apartment_id: "frequency"}
            ),
            group_column="quality",
            value_column="frequency",
            score=apartment_scores.loc[apartment_id].values[0] / 100,
            ax=top_left,
        )
        top_left.set_title("Holistic Performance Percentile")

        # Bar Chart
        bar_dataframe = (
            area_quality_distribution_dataframe[
                area_quality_distribution_dataframe.index.get_level_values(
                    "apartment_id"
                )
                == apartment_id
            ]
            .reset_index()
            .set_index("room_name")
            .drop("apartment_id", axis=1)
        )
        ChartHandler.bar_chart(
            dataframe=bar_dataframe,
            scores=area_scores[
                area_scores.index.get_level_values("apartment_id") == apartment_id
            ]["score"]
            / 100.0,
            ax=top_right,
        )
        top_right.set_title("Individual Area Ranking")

        # Small Donuts
        axes = [
            bottom_left_top_left,
            bottom_left_top_center,
            bottom_left_top_right,
            bottom_left_bottom_left,
            bottom_left_bottom_right,
        ]
        sub_configurations = configuration()._CONFIGURATIONS

        for ax, sub_configuration in zip(axes, sub_configurations):
            config_apartment_area_type_quality_distribution_dataframe = (
                self.data_handler.apartment_area_type_quality_frequencies_dataframe(
                    configuration=sub_configuration
                )
            )
            config_apartment_scores = self.data_handler.apartment_scores_adjusted(
                configuration=sub_configuration
            )
            donut_dataframe = config_apartment_area_type_quality_distribution_dataframe[
                config_apartment_area_type_quality_distribution_dataframe.index.get_level_values(
                    "apartment_id"
                )
                == apartment_id
            ]
            ChartHandler.donut_chart(
                dataframe=donut_dataframe.T.reset_index().rename(
                    columns={"value": "quality", apartment_id: "frequency"}
                ),
                group_column="quality",
                value_column="frequency",
                score=config_apartment_scores.loc[apartment_id].values[0] / 100,
                ax=ax,
                compact=True,
            )
            ax.set_title(sub_configuration().category_name, y=0.9, fontsize=26)

        return figure

    @archilyse_chart_style
    def building_summary(
        self,
        building_id: int,
        configuration: Type[AllDimensionsSimulationCategoryConfiguration],
    ):
        # --------- Data --------- #

        percentile_dataframe = self.data_handler.percentile_dataframe(
            configuration=configuration  # type: ignore
        )

        building_scores = self.data_handler.building_scores(configuration=configuration)  # type: ignore
        building_area_type_quality_distribution_dataframe = self.data_handler.building_area_type_quality_distribution_dataframe(
            configuration=configuration  # type: ignore
        )

        floor_scores = self.data_handler.floor_scores(configuration=configuration)  # type: ignore
        floor_area_type_quality_distribution_dataframe = self.data_handler.floor_area_type_quality_distribution_dataframe(
            configuration=configuration  # type: ignore
        )

        floor_id_to_floor_number = (
            percentile_dataframe[
                percentile_dataframe.index.get_level_values("building_id")
                == building_id
            ]
            .reset_index()[["floor_id", "floor_number"]]
            .drop_duplicates()
            .groupby("floor_id")
            .max()
            .reset_index()
            .sort_values("floor_number", ascending=False)
            .set_index("floor_id")
            .drop_duplicates()
        )
        floor_num_apartments = (
            percentile_dataframe[
                percentile_dataframe.index.get_level_values("building_id")
                == building_id
            ]
            .reset_index()[["floor_id", "apartment_id"]]
            .drop_duplicates()
            .groupby("floor_id")
            .count()
            .loc[floor_id_to_floor_number.index]
        )

        room_count_scores = self.data_handler.room_count_scores(
            configuration=configuration  # type: ignore
        )
        room_count_area_type_quality_distribution_dataframe = self.data_handler.room_count_area_type_quality_distribution_dataframe(
            configuration=configuration  # type: ignore
        )
        room_counts = (
            percentile_dataframe[
                percentile_dataframe.index.get_level_values("building_id")
                == building_id
            ]
            .reset_index()[["apartment_aggregate_room_count"]]
            .drop_duplicates()
            .sort_values("apartment_aggregate_room_count", ascending=False)
            .set_index("apartment_aggregate_room_count")
            .drop_duplicates()
        )
        room_count_num_apartments = (
            percentile_dataframe[
                percentile_dataframe.index.get_level_values("building_id")
                == building_id
            ]
            .reset_index()[["apartment_aggregate_room_count", "apartment_id"]]
            .drop_duplicates()
            .groupby("apartment_aggregate_room_count")
            .count()
            .loc[room_counts.index]
        )

        # --------- Layout --------- #

        figure = self.make_archilyse_chart(
            title="Building Analysis Summary",
            subtitle=f"{self.building_infos[building_id]['city']} > {self.building_infos[building_id]['street']} {self.building_infos[building_id]['housenumber']}",
            bottom_left="",
        )

        gs = figure.add_gridspec(
            ncols=60,
            nrows=17,
            left=figure.MAIN_AXIS[0] * figure.DX,
            bottom=figure.MAIN_AXIS[1] * figure.DY,
            right=(figure.MAIN_AXIS[0] + figure.MAIN_AXIS[2]) * figure.DX,
            top=(figure.MAIN_AXIS[1] + figure.MAIN_AXIS[3]) * figure.DY,
        )
        top_left = figure.add_subplot(gs[:9, :18])
        bottom_left_top_left = figure.add_subplot(gs[9:13, :6])
        bottom_left_top_center = figure.add_subplot(gs[9:13, 6:12])
        bottom_left_top_right = figure.add_subplot(gs[9:13, 12:18])
        bottom_left_bottom_left = figure.add_subplot(gs[13:17, 3:9])
        bottom_left_bottom_right = figure.add_subplot(gs[13:17, 9:15])

        center = figure.add_subplot(
            gs[: min(floor_id_to_floor_number.shape[0] * 2, 17), 21:34]
        )
        right = figure.add_subplot(gs[: min(room_counts.shape[0] * 2, 17), 40:53])

        # --------- Charts --------- #

        # Donut
        donut_dataframe = building_area_type_quality_distribution_dataframe.loc[
            building_id
        ]
        ChartHandler.donut_chart(
            dataframe=donut_dataframe.T.reset_index().rename(
                columns={"value": "quality", building_id: "frequency"}
            ),
            group_column="quality",
            value_column="frequency",
            score=building_scores.loc[building_id]["score"] / 100.0,
            ax=top_left,
        )
        top_left.set_title("Holistic Performance Percentile")

        # Small Donuts
        axes = [
            bottom_left_top_left,
            bottom_left_top_center,
            bottom_left_top_right,
            bottom_left_bottom_left,
            bottom_left_bottom_right,
        ]
        sub_configurations = configuration()._CONFIGURATIONS

        for ax, sub_configuration in zip(axes, sub_configurations):
            config_building_scores = self.data_handler.building_scores(
                configuration=sub_configuration
            )
            config_building_area_type_quality_distribution_dataframe = (
                self.data_handler.building_area_type_quality_distribution_dataframe(
                    configuration=sub_configuration
                )
            )

            donut_dataframe = (
                config_building_area_type_quality_distribution_dataframe.loc[
                    building_id
                ]
                / 100.0
            )
            ChartHandler.donut_chart(
                dataframe=donut_dataframe.T.reset_index().rename(
                    columns={"value": "quality", building_id: "frequency"}
                ),
                group_column="quality",
                value_column="frequency",
                score=config_building_scores.loc[building_id]["score"] / 100.0,
                ax=ax,
                compact=True,
            )
            ax.set_title(sub_configuration().category_name, y=0.9, fontsize=26)

        # Floors
        bar_dataframe = floor_area_type_quality_distribution_dataframe.loc[
            floor_id_to_floor_number.index
        ].set_index(
            floor_id_to_floor_number["floor_number"].apply(lambda z: f"Floor {z:.0f}")
        )
        scores = floor_scores.loc[floor_id_to_floor_number.index].set_index(
            floor_id_to_floor_number["floor_number"].apply(lambda z: f"Floor {z:.0f}")
        )
        ChartHandler.bar_chart(
            dataframe=bar_dataframe * floor_num_apartments.values,
            scores=scores["score"] / 100,
            ax=center,
            vertical=True,
            multi_vertical=True,
            xticks=tuple(floor_num_apartments.values.flatten()),
        )
        center.set_title("Floor Overview", pad=-10)

        # Clusters
        bar_dataframe = room_count_area_type_quality_distribution_dataframe.loc[
            room_counts.index
        ].set_index(
            room_counts.reset_index()["apartment_aggregate_room_count"].apply(
                lambda z: f"{z} Rooms"
            )
        )
        scores = room_count_scores.loc[room_counts.index].set_index(
            room_counts.reset_index()["apartment_aggregate_room_count"].apply(
                lambda z: f"{z} Rooms"
            )
        )
        ChartHandler.bar_chart(
            dataframe=bar_dataframe * room_count_num_apartments.values,
            scores=scores["score"] / 100,
            ax=right,
            vertical=True,
            multi_vertical=True,
            xticks=tuple(room_count_num_apartments.values.flatten()),
        )
        right.set_title("Unit Type Overview", pad=-10)

        return figure

    # --------- Chart Utils --------- #

    def get_metadata_dict(self, apartment_id: str):
        apartment_dataframe = self.data_handler.target_dataframe[
            self.data_handler.target_dataframe["apartment_id"] == apartment_id
        ]
        building_id = apartment_dataframe["building_id"].values[0]

        return {
            "apartment_id": apartment_id,
            "room_count": apartment_dataframe["apartment_aggregate_room_count"].values[
                0
            ],
            "net_area": apartment_dataframe["apartment_aggregate_net_area"].values[0],
            "floor_number": apartment_dataframe[
                "apartment_aggregate_floor_number"
            ].values[0],
            "is_maisonette": apartment_dataframe[
                "apartment_aggregate_is_maisonette"
            ].values[0],
            "street": self.building_infos[building_id]["street"],
            "housenumber": self.building_infos[building_id]["housenumber"],
            "city": self.building_infos[building_id]["city"],
        }

    def get_metadata_string(self, apartment_id: str):
        metadata = self.get_metadata_dict(apartment_id=apartment_id)
        return (
            f"{metadata['city']}"
            f" > {metadata['street']} {metadata['housenumber']}"
            f" > Floor {metadata['floor_number']}"
            f" > Unit {metadata['apartment_id']}"
            f" ({metadata['room_count']} Rooms, {metadata['net_area']:.1f} m²"
            f"{', Maisonette' if metadata['is_maisonette'] else ''}"
            ")"
        )

    def get_clustersize_string(self, apartment_dataframe: pd.DataFrame) -> str:
        clusters = apartment_dataframe[CLUSTER_COLUMNS]
        bf = r"\bf"
        return f"${{{bf} Reference\\ Samples}}$\n" + ", ".join(
            f"{room_type}={count}"
            for i, (room_type, count) in enumerate(
                self.data_handler.reference_sizes.loc[map(tuple, clusters.values), :][
                    ["area_id"]
                ]
                .reset_index()[["layout_area_type", "area_id"]]
                .values
            )
        )
