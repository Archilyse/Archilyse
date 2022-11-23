import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import pytest

from common_utils.constants import DEFAULT_RESULT_VECTORS, SIMULATION_VERSION
from common_utils.exceptions import PHVectorSubgroupException
from handlers import (
    DMSChartDeliverableHandler,
    DMSEnergyReferenceAreaReportHandler,
    DMSVectorFilesHandler,
)
from handlers.charts import ApartmentChartGenerator
from handlers.db.site_handler import SiteDBHandler
from handlers.energy_reference_area.main_report import EnergyAreaReportForSite


@pytest.mark.parametrize(
    "subgroups", [None, {"groupname_1": {"1"}, "groupname_2": {"2"}}]
)
@pytest.mark.parametrize("match_client_id_exact", [True, False])
@pytest.mark.parametrize("allow_subset", [True, False])
def test_dms_generate_vector_files_no_units_ph2021(
    mocker, subgroups, match_client_id_exact, allow_subset
):
    from tasks.utils import deliverable_utils

    mocker.patch.object(
        deliverable_utils,
        "get_index_by_result_type",
        return_value={
            vector_type.value: [
                {"client_id": "1", "floor_number": 0, "apartment_no": 1},
                {"client_id": "2", "floor_number": 0, "apartment_no": 2},
                {"client_id": "13", "floor_number": 0, "apartment_no": 3},
            ]
            for vector_type in DEFAULT_RESULT_VECTORS
        },
    )

    write_vector_spy = mocker.spy(DMSVectorFilesHandler, "_create_vector_csv")

    mocked_write_header = mocker.patch.object(csv.DictWriter, "writeheader")

    with TemporaryDirectory() as fout:
        if subgroups and match_client_id_exact and not allow_subset:
            with pytest.raises(PHVectorSubgroupException):
                DMSVectorFilesHandler._generate_vector_files(
                    site={
                        "id": 1,
                        "client_site_id": "1",
                        "simulation_version": SIMULATION_VERSION.PH_01_2021.name,
                    },
                    representative_units_only=False,
                    folderpath=Path(fout),
                    subgroups=subgroups,
                    subgroups_match_client_ids_exact=match_client_id_exact,
                    subgroups_allow_subset=allow_subset,
                )
            return

        DMSVectorFilesHandler._generate_vector_files(
            site={
                "id": 1,
                "client_site_id": "1",
                "simulation_version": SIMULATION_VERSION.PH_01_2021.name,
            },
            representative_units_only=False,
            folderpath=Path(fout),
            subgroups=subgroups,
            subgroups_match_client_ids_exact=match_client_id_exact,
            subgroups_allow_subset=allow_subset,
        )
        if not subgroups:
            assert mocked_write_header.call_count == len(DEFAULT_RESULT_VECTORS)
            assert {
                len(call.kwargs["unit_vectors"])
                for call in write_vector_spy.call_args_list
            } == {3}
        elif match_client_id_exact:
            assert mocked_write_header.call_count == len(DEFAULT_RESULT_VECTORS) * 2
            assert {
                len(call.kwargs["unit_vectors"])
                for call in write_vector_spy.call_args_list
            } == {1}
        else:
            assert mocked_write_header.call_count == len(DEFAULT_RESULT_VECTORS) * 2
            assert {
                len(call.kwargs["unit_vectors"])
                for call in write_vector_spy.call_args_list
            } == {1, 2}


def test_dms_upload_vector_files_empty_files_ignored(mocker):
    mocked_upload_file = mocker.patch.object(
        DMSVectorFilesHandler, "create_or_replace_dms_file"
    )
    with TemporaryDirectory() as fout:
        Path(fout).joinpath("empty_file.csv").touch()
        DMSVectorFilesHandler._upload_files_to_dms(
            site={}, folder_id=1, folderpath=Path(fout)
        )
    assert mocked_upload_file.call_count == 0


def test_dms_upload_vector_files_valid_uploaded(mocker):
    mocked_upload_file = mocker.patch.object(
        DMSVectorFilesHandler, "create_or_replace_dms_file"
    )
    with TemporaryDirectory() as fout:
        with Path(fout).joinpath("file_w_content.csv").open("wb") as f:
            f.write(b"something")
            f.seek(0)
            DMSVectorFilesHandler._upload_files_to_dms(
                site={"client_id": 1, "id": 2}, folder_id=1, folderpath=Path(fout)
            )
    assert mocked_upload_file.call_count == 1


def test_generate_and_upload_apartment_charts(mocker, monkeypatch):
    site_id = 314
    dummy_site = {"client_id": "dummy_client", "client_site_id": "dummy_site"}
    mocker.patch.object(SiteDBHandler, "get_by", return_value=dummy_site)

    def _make_charts_fake(self):
        chart_path = self.output_dir.joinpath("dummy_apartment/dummy_chart.pdf")
        chart_path.parent.mkdir(parents=True, exist_ok=True)
        with chart_path.open("wb"):
            return

    monkeypatch.setattr(
        ApartmentChartGenerator, "generate_default_charts", _make_charts_fake
    )
    make_index_mock = mocker.patch.object(
        ApartmentChartGenerator, "generate_default_chart_index"
    )
    make_sheets_mock = mocker.patch.object(
        ApartmentChartGenerator, "generate_default_data_sheets"
    )
    upload_mock = mocker.patch.object(
        DMSChartDeliverableHandler, "create_or_replace_dms_file"
    )
    mocker.patch.object(DMSChartDeliverableHandler, "_download_reference_dataset")
    zip_spy = mocker.spy(ZipFile, "write")

    DMSChartDeliverableHandler.generate_and_upload_apartment_charts(site_id=site_id)

    make_index_mock.assert_called_once()
    make_sheets_mock.assert_called_once()
    assert upload_mock.call_args.kwargs["site_id"] == site_id
    assert upload_mock.call_args.kwargs["client_id"] == dummy_site["client_id"]
    assert upload_mock.call_args.kwargs["extension"] == ".zip"
    assert (
        upload_mock.call_args.kwargs["filename"] == "dummy_site - Apartment Charts.zip"
    )
    assert upload_mock.call_args.kwargs["labels"] == ["Benchmarks"]
    assert zip_spy.call_args.kwargs["arcname"] == "/dummy_apartment/dummy_chart.pdf"


@pytest.mark.parametrize(
    "client_site_id, name, expected_prefix",
    [
        ("", "", ""),
        ("foo", "bar", "foo"),
        ("", "foo", "foo"),
    ],
)
def test_generate_and_upload_energy_report(
    mocker, client_site_id, name, expected_prefix
):
    site_id = 314
    dummy_site = {
        "client_id": "dummy_client",
        "client_site_id": client_site_id,
        "name": name,
    }
    mocker.patch.object(SiteDBHandler, "get_by", return_value=dummy_site)

    mocker.patch.object(EnergyAreaReportForSite, "create_report")
    upload_mock = mocker.patch.object(
        DMSEnergyReferenceAreaReportHandler, "create_or_replace_dms_file"
    )

    DMSEnergyReferenceAreaReportHandler.generate_and_upload_energy_reference_area_report(
        site_id=site_id
    )

    assert upload_mock.call_args.kwargs["site_id"] == site_id
    assert upload_mock.call_args.kwargs["client_id"] == dummy_site["client_id"]
    assert upload_mock.call_args.kwargs["extension"] == ".xlsx"
    assert (
        upload_mock.call_args.kwargs["filename"]
        == f"{expected_prefix} - Energy Reference Area Report.xlsx"
    )
    assert upload_mock.call_args.kwargs["labels"] == ["EBF"]
