import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest
from deepdiff import DeepDiff
from PIL import Image

from common_utils.constants import (
    BENCHMARK_DATASET_SIMULATIONS_PATH,
    BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH,
    BENCHMARK_PERCENTILES_DIMENSIONS_PATH,
)
from handlers.charts import ApartmentChartGenerator
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
from tests.utils import (
    assert_image_phash,
    load_dataframe_from_zip_file,
    load_json_from_zip_file,
    save_dataframe_to_zip_file,
    save_json_to_zip_file,
)


@pytest.fixture
def make_mocked_chart_data(mocker, fixtures_path, update_fixtures: bool = False):
    def _regenerate_fixtures(
        apartment_id: str = "f3f08476fea8c931b6fcbd4cadc35e7d",
        apartment_aggregate_cluster="TOP_LEVEL_4.X",
    ):
        df_simulations = pd.read_csv(BENCHMARK_DATASET_SIMULATIONS_PATH)
        df_simulations = df_simulations[df_simulations["apartment_id"] == apartment_id]
        save_dataframe_to_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="simulations",
            data=df_simulations,
        )

        df_percentiles_apartment_scores = pd.read_csv(
            BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH
        )
        df_percentiles_apartment_scores = df_percentiles_apartment_scores[
            df_percentiles_apartment_scores["apartment_aggregate_cluster"]
            == apartment_aggregate_cluster
        ]
        save_dataframe_to_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="simulations_apartment_scores",
            data=df_percentiles_apartment_scores,
        )

        with BENCHMARK_PERCENTILES_DIMENSIONS_PATH.open() as fh:
            percentiles_dimensions = json.load(fh)
            percentiles_dimensions = {
                apartment_aggregate_cluster: percentiles_dimensions[
                    apartment_aggregate_cluster
                ]
            }
        save_json_to_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="dimension_percentiles_per_cluster",
            data=percentiles_dimensions,
        )

    if update_fixtures:
        _regenerate_fixtures()

    def _make_mocked_chart_data(
        apartment_id: str, add_nan_values: bool = False
    ) -> tuple[int, int]:

        target_dataframe = load_dataframe_from_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="simulations",
        )
        if add_nan_values:
            target_dataframe["connectivity_eigen_centrality_p80"] = None

        apartment_score_bins_dataframe = load_dataframe_from_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="simulations_apartment_scores",
        )
        reference_dataframe_cluster_sizes = load_dataframe_from_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="reference_sizes",
        ).set_index(CLUSTER_COLUMNS)
        reference_dataframe_percentiles_per_cluster = load_json_from_zip_file(
            fixtures_path=fixtures_path.joinpath("vectors/charts"),
            file_name="dimension_percentiles_per_cluster",
        )
        for (
            apartment_type,
            area_type_percentiles,
        ) in reference_dataframe_percentiles_per_cluster.items():
            for area_type, percentiles in area_type_percentiles.items():
                reference_dataframe_percentiles_per_cluster[apartment_type][
                    area_type
                ] = pd.DataFrame(percentiles)

        mocker.patch.object(
            ChartDataHandler,
            "_unprocessed_target_dataframe",
            mocker.PropertyMock(return_value=target_dataframe),
        )
        mocker.patch.object(
            ChartDataHandler,
            "apartment_score_bins_dataframe",
            mocker.PropertyMock(return_value=apartment_score_bins_dataframe),
        )
        mocker.patch.object(
            ChartDataHandler,
            "reference_dataframe_percentiles_per_cluster",
            mocker.PropertyMock(
                return_value=reference_dataframe_percentiles_per_cluster
            ),
        )
        mocker.patch.object(
            ChartDataHandler,
            "reference_sizes",
            mocker.PropertyMock(return_value=reference_dataframe_cluster_sizes),
        )
        mocker.patch.object(
            ApartmentChartGenerator,
            "building_infos",
            mocker.PropertyMock(
                return_value={
                    target_dataframe["building_id"].unique()[0]: {
                        "street": "Musterstr.",
                        "housenumber": "1a",
                        "city": "Musterstadt",
                    }
                }
            ),
        )

        return (
            target_dataframe["site_id"].unique()[0],
            target_dataframe["building_id"].unique()[0],
        )

    return _make_mocked_chart_data


def test_generate_default_charts(mocker):
    dummy_site_id = 1
    dummy_apartment_ids = {"11", "12"}
    dummy_building_ids = [123, 124]
    dummy_metadata_dict = {
        "apartment_id": "11",
        "room_count": 2,
        "net_area": 3,
        "floor_number": 4,
        "is_maisonette": False,
        "street": "Musterstr",
        "housenumber": "1",
        "city": "Musterstadt",
    }
    mocker.patch.object(
        ApartmentChartGenerator, "get_metadata_dict", return_value=dummy_metadata_dict
    )

    mocker.patch.object(
        ApartmentChartGenerator,
        "apartment_ids",
        mocker.PropertyMock(return_value=dummy_apartment_ids),
    )
    mocker.patch.object(
        ApartmentChartGenerator,
        "building_infos",
        mocker.PropertyMock(
            return_value={
                dummy_building_id: {
                    "street": "Musterstr",
                    "housenumber": "1",
                    "city": "Musterstadt",
                }
                for dummy_building_id in dummy_building_ids
            }
        ),
    )
    mock_chart = mocker.MagicMock()
    mock_unit_room_summary = mocker.patch.object(
        ApartmentChartGenerator, "unit_room_summary", return_value=mock_chart
    )
    mock_unit_summary = mocker.patch.object(
        ApartmentChartGenerator, "unit_summary", return_value=mock_chart
    )
    mock_building_summary = mocker.patch.object(
        ApartmentChartGenerator, "building_summary", return_value=mock_chart
    )

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = ApartmentChartGenerator(
            site_id=dummy_site_id, output_dir=output_dir
        )
        generator.generate_default_charts()

    for apartment_id in dummy_apartment_ids:
        for configuration in [
            ViewSimulationCategoryConfiguration,
            SunSimulationCategoryConfiguration,
            NoiseSimulationCategoryConfiguration,
            CentralitySimulationCategoryConfiguration,
            RoomLayoutSimulationCategoryConfiguration,
        ]:
            mock_unit_room_summary.assert_any_call(
                apartment_id=apartment_id, configuration=configuration
            )

        mock_unit_summary.assert_any_call(
            apartment_id=apartment_id,
            configuration=AllDimensionsSimulationCategoryConfiguration,
        )
        for expected_file in [
            "Daylight.pdf",
            "Accessibility.pdf",
            "Layout.pdf",
            "View.pdf",
            "Noise.pdf",
            "Summary.pdf",
        ]:
            mock_chart.savefig.assert_any_call(
                output_dir.joinpath(
                    f"Musterstr 1/2 Rooms/{apartment_id}/{expected_file}"
                ).as_posix(),
            )
            mock_chart.savefig.assert_any_call(
                output_dir.joinpath("Preview")
                .joinpath(f"Musterstr 1/2 Rooms/{apartment_id}/{expected_file}.png")
                .as_posix(),
                dpi=10,
            )

    for dummy_building_id in dummy_building_ids:
        mock_building_summary.assert_any_call(
            building_id=dummy_building_id,
            configuration=AllDimensionsSimulationCategoryConfiguration,
        )

        mock_chart.savefig.assert_any_call(
            output_dir.joinpath("Musterstr 1/Building Summary.pdf").as_posix()
        )


def test_generate_default_chart_index(mocker, monkeypatch):
    import pandas as pd

    dummy_site_id = 1
    dummy_apartment_ids = {"11", "12"}
    dummy_metadata_dicts = {
        "11": {
            "apartment_id": "11",
            "room_count": 2,
            "net_area": 3,
            "floor_number": 4,
            "is_maisonette": False,
            "street": "Musterstr",
            "housenumber": "1",
            "city": "Musterstadt",
        },
        "12": {
            "apartment_id": "12",
            "room_count": 3,
            "net_area": 4,
            "floor_number": 5,
            "is_maisonette": True,
            "street": "Andere Musterstr",
            "housenumber": "2",
            "city": "Andere Musterstadt",
        },
    }

    def _get_dummy_metadata_dict(self, apartment_id: str):
        return dummy_metadata_dicts[apartment_id]

    monkeypatch.setattr(
        ApartmentChartGenerator, "get_metadata_dict", _get_dummy_metadata_dict
    )
    mocker.patch.object(
        ApartmentChartGenerator,
        "apartment_ids",
        mocker.PropertyMock(return_value=dummy_apartment_ids),
    )
    to_html_mock = mocker.patch.object(pd.DataFrame, "to_html", autospec=True)
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = ApartmentChartGenerator(
            site_id=dummy_site_id, output_dir=output_dir
        )
        generator.generate_default_chart_index()

    expected_index = {
        "apartment_id": {1: "12", 0: "11"},
        "city": {1: "Andere Musterstadt", 0: "Musterstadt"},
        "street": {1: "Andere Musterstr", 0: "Musterstr"},
        "housenumber": {1: "2", 0: "1"},
        "floor_number": {1: 5, 0: 4},
        "is_maisonette": {1: True, 0: False},
        "room_count": {1: 3, 0: 2},
        "net_area": {1: 4, 0: 3},
        "All": {
            1: "<a href='Andere Musterstr 2/3 Rooms/12/Summary.pdf'><img src='Preview/Andere Musterstr 2/3 Rooms/12/Summary.pdf.png' /><a/>",
            0: "<a href='Musterstr 1/2 Rooms/11/Summary.pdf'><img src='Preview/Musterstr 1/2 Rooms/11/Summary.pdf.png' /><a/>",
        },
        "View": {
            1: "<a href='Andere Musterstr 2/3 Rooms/12/View.pdf'><img src='Preview/Andere Musterstr 2/3 Rooms/12/View.pdf.png' /><a/>",
            0: "<a href='Musterstr 1/2 Rooms/11/View.pdf'><img src='Preview/Musterstr 1/2 Rooms/11/View.pdf.png' /><a/>",
        },
        "Daylight": {
            1: "<a href='Andere Musterstr 2/3 Rooms/12/Daylight.pdf'><img src='Preview/Andere Musterstr 2/3 Rooms/12/Daylight.pdf.png' /><a/>",
            0: "<a href='Musterstr 1/2 Rooms/11/Daylight.pdf'><img src='Preview/Musterstr 1/2 Rooms/11/Daylight.pdf.png' /><a/>",
        },
        "Noise": {
            1: "<a href='Andere Musterstr 2/3 Rooms/12/Noise.pdf'><img src='Preview/Andere Musterstr 2/3 Rooms/12/Noise.pdf.png' /><a/>",
            0: "<a href='Musterstr 1/2 Rooms/11/Noise.pdf'><img src='Preview/Musterstr 1/2 Rooms/11/Noise.pdf.png' /><a/>",
        },
        "Accessibility": {
            1: "<a href='Andere Musterstr 2/3 Rooms/12/Accessibility.pdf'><img src='Preview/Andere Musterstr 2/3 Rooms/12/Accessibility.pdf.png' /><a/>",
            0: "<a href='Musterstr 1/2 Rooms/11/Accessibility.pdf'><img src='Preview/Musterstr 1/2 Rooms/11/Accessibility.pdf.png' /><a/>",
        },
        "Layout": {
            1: "<a href='Andere Musterstr 2/3 Rooms/12/Layout.pdf'><img src='Preview/Andere Musterstr 2/3 Rooms/12/Layout.pdf.png' /><a/>",
            0: "<a href='Musterstr 1/2 Rooms/11/Layout.pdf'><img src='Preview/Musterstr 1/2 Rooms/11/Layout.pdf.png' /><a/>",
        },
    }
    assert not DeepDiff(
        to_html_mock.call_args[0][0].to_dict(), expected_index, ignore_order=True
    )


@pytest.mark.parametrize(
    "configuration",
    [
        CentralitySimulationCategoryConfiguration,
        NoiseSimulationCategoryConfiguration,
        RoomLayoutSimulationCategoryConfiguration,
        SunSimulationCategoryConfiguration,
        ViewSimulationCategoryConfiguration,
    ],
)
def test_unit_room_summary(fixtures_path, configuration, make_mocked_chart_data):
    apartment_id = "f3f08476fea8c931b6fcbd4cadc35e7d"
    site_id, _ = make_mocked_chart_data(apartment_id=apartment_id)

    expected_image_file_path = fixtures_path.joinpath(
        f"images/charts/unit_room_summary_{apartment_id}_{configuration.__name__}.png"
    )
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = ApartmentChartGenerator(site_id=site_id, output_dir=output_dir)
        figure = generator.unit_room_summary(
            apartment_id=apartment_id, configuration=configuration
        )

        new_file_path = output_dir.joinpath("new.png")
        figure.savefig(new_file_path, format="png")
        with Image.open(new_file_path) as new_image_content:
            assert_image_phash(
                expected_image_file=expected_image_file_path,
                new_image_content=new_image_content,
            )


def test_unit_summary(fixtures_path, make_mocked_chart_data):
    apartment_id = "f3f08476fea8c931b6fcbd4cadc35e7d"
    configuration = AllDimensionsSimulationCategoryConfiguration
    site_id, _ = make_mocked_chart_data(apartment_id=apartment_id)

    expected_image_file_path = fixtures_path.joinpath(
        f"images/charts/unit_summary_{apartment_id}_{configuration.__name__}.png"
    )
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = ApartmentChartGenerator(site_id=site_id, output_dir=output_dir)
        figure = generator.unit_summary(
            apartment_id=apartment_id, configuration=configuration
        )

        new_file_path = output_dir.joinpath("new.png")
        figure.savefig(new_file_path, format="png")
        with Image.open(new_file_path) as new_image_content:
            assert_image_phash(
                expected_image_file=expected_image_file_path,
                new_image_content=new_image_content,
            )


def test_unit_summary_with_none_values_in_target_df(
    fixtures_path, make_mocked_chart_data
):
    apartment_id = "f3f08476fea8c931b6fcbd4cadc35e7d"
    configuration = AllDimensionsSimulationCategoryConfiguration
    site_id, _ = make_mocked_chart_data(apartment_id=apartment_id, add_nan_values=True)
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        ApartmentChartGenerator(site_id=site_id, output_dir=output_dir).unit_summary(
            apartment_id=apartment_id, configuration=configuration
        )


def test_building_summary(fixtures_path, make_mocked_chart_data):
    apartment_id = "f3f08476fea8c931b6fcbd4cadc35e7d"
    configuration = AllDimensionsSimulationCategoryConfiguration
    site_id, _ = make_mocked_chart_data(apartment_id=apartment_id)
    building_id = 6267

    expected_image_file_path = fixtures_path.joinpath(
        f"images/charts/building_summary_{building_id}_{configuration.__name__}.png"
    )
    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = ApartmentChartGenerator(site_id=site_id, output_dir=output_dir)
        figure = generator.building_summary(
            building_id=6267, configuration=configuration
        )

        new_file_path = output_dir.joinpath("new.png")
        figure.savefig(new_file_path, format="png")
        with Image.open(new_file_path) as new_image_content:
            assert_image_phash(
                expected_image_file=expected_image_file_path,
                new_image_content=new_image_content,
            )


def test_generate_default_data_sheet(
    mocker,
    monkeypatch,
    fixtures_path,
    make_mocked_chart_data,
    update_fixture: bool = False,
):
    import pandas as pd

    apartment_id = "f3f08476fea8c931b6fcbd4cadc35e7d"
    site_id, _ = make_mocked_chart_data(apartment_id=apartment_id)

    dummy_site_id = 1
    dummy_apartment_ids = {apartment_id}
    dummy_metadata_dicts = {
        apartment_id: {
            "apartment_id": apartment_id,
            "room_count": 2,
            "net_area": 3,
            "floor_number": 4,
            "is_maisonette": False,
            "street": "Musterstr",
            "housenumber": "1",
            "city": "Musterstadt",
        },
    }

    def _get_dummy_metadata_dict(self, apartment_id: str):
        return dummy_metadata_dicts[apartment_id]

    monkeypatch.setattr(
        ApartmentChartGenerator, "get_metadata_dict", _get_dummy_metadata_dict
    )
    mocker.patch.object(
        ApartmentChartGenerator,
        "apartment_ids",
        mocker.PropertyMock(return_value=dummy_apartment_ids),
    )

    expected_apartment_scores = {
        "apartment_id": {0: "f3f08476fea8c931b6fcbd4cadc35e7d"},
        "room_count": {0: 2},
        "net_area": {0: 3},
        "floor_number": {0: 4},
        "is_maisonette": {0: False},
        "street": {0: "Musterstr"},
        "housenumber": {0: 1},
        "city": {0: "Musterstadt"},
        "All Score": {0: 35.0},
        "Noise Score": {0: 60.0},
        "Daylight Score": {0: 16.0},
        "Layout Score": {0: 46.0},
        "Accessibility Score": {0: 53.0},
        "View Score": {0: 28.000000000000004},
    }

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir)
        generator = ApartmentChartGenerator(
            site_id=dummy_site_id, output_dir=output_dir
        )
        generator.generate_default_data_sheets()

        actual_apartment_scores = pd.read_csv(
            output_dir.joinpath("apartment_scores.csv")
        ).to_dict()
        assert actual_apartment_scores == expected_apartment_scores

        actual_area_percentiles = json.loads(
            json.dumps(
                pd.read_csv(output_dir.joinpath("area_percentiles.csv")).to_dict()
            )
        )
        if update_fixture:
            with fixtures_path.joinpath("vectors/data_sheet_charts.json").open(
                "w"
            ) as fh:
                json.dump(actual_area_percentiles, fh)

        with fixtures_path.joinpath("vectors/data_sheet_charts.json").open() as fh:
            expected_area_percentiles = json.load(fh)

        assert not DeepDiff(
            actual_area_percentiles,
            expected_area_percentiles,
            ignore_order=True,
        )
