from pathlib import Path
from unittest.mock import call
from zipfile import ZipFile

import pytest

from common_utils.constants import SUPPORTED_LANGUAGES, SUPPORTED_OUTPUT_FILES
from handlers import (
    DMSChartDeliverableHandler,
    DMSFloorDeliverableHandler,
    DMSUnitDeliverableHandler,
    DMSVectorFilesHandler,
)
from handlers.db import SiteDBHandler
from handlers.dms.dms_deliverable_handler import DMSEnergyReferenceAreaReportHandler
from tasks.deliverables_tasks import (
    generate_energy_reference_area_task,
    generate_unit_plots_task,
    generate_vector_files_task,
)
from tasks.utils.deliverable_utils import (
    download_floor_dxf_dwg,
    download_floor_pngs,
    download_unit_pngs,
)


@pytest.mark.parametrize("number_of_clusters", [None, 10])  # sth not None
def test_generate_vector_files_task(mocker, site, number_of_clusters):
    # Given
    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"sub_sampling_number_of_clusters": number_of_clusters},
    )
    mocked_clustering_enabled = mocker.spy(SiteDBHandler, SiteDBHandler.exists.__name__)
    mocked_vector_generation = mocker.patch.object(
        DMSVectorFilesHandler,
        DMSVectorFilesHandler.generate_and_upload_vector_files_to_dms.__name__,
    )

    # When
    generate_vector_files_task(site_id=site["id"])

    # Then
    mocked_clustering_enabled.assert_called_once_with(
        id=site["id"], sub_sampling_number_of_clusters=None
    )
    mocked_vector_generation.assert_called_once_with(
        site_id=site["id"], representative_units_only=number_of_clusters is not None
    )


def test_download_unit_pngs(mocker, client_db, site, floor, unit, fixtures_path):
    with fixtures_path.joinpath("images/unit_pngs/7641_unit.png").open("rb") as f:
        floorplan = f.read()

    mkdir_mock = mocker.patch("pathlib.Path.mkdir", mocker.mock_open())
    path_mock = mocker.patch("pathlib.Path.open", mocker.mock_open())
    download_file_mock = mocker.patch.object(
        DMSUnitDeliverableHandler, "download_unit_file", return_value=floorplan
    )

    download_unit_pngs(
        client_id=client_db["id"],
        units_in_floor=[unit],
        floor=floor,
        layouts_path=Path("layouts"),
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )
    assert path_mock.mock_calls[0].args[0] == "wb"
    mkdir_mock.assert_called_once_with(exist_ok=True, parents=True)
    download_file_mock.assert_has_calls(
        [
            call(
                client_id=client_db["id"],
                unit_id=unit["id"],
                language=language,
                file_format=SUPPORTED_OUTPUT_FILES.PNG,
            )
            for language in SUPPORTED_LANGUAGES
        ]
    )


def test_download_floor_pngs(mocker, floor, fixtures_path):
    with fixtures_path.joinpath("images/floor_pngs/7641-full_floorplan_DE.png").open(
        "rb"
    ) as f:
        floorplan = f.read()

    path_mock = mocker.patch("pathlib.Path.open", mocker.mock_open())
    download_file_mock = mocker.patch.object(
        DMSFloorDeliverableHandler, "download_floor_file", return_value=floorplan
    )
    download_floor_pngs(
        floor=floor,
        floor_prefix="foo",
        layouts_path=Path("layouts"),
        file_format=SUPPORTED_OUTPUT_FILES.PNG,
    )
    assert path_mock.mock_calls[0].args[0] == "wb"
    download_file_mock.assert_has_calls(
        [
            call(
                floor_id=floor["id"],
                language=language,
                file_format=SUPPORTED_OUTPUT_FILES.PNG,
            )
            for language in SUPPORTED_LANGUAGES
        ]
    )


def test_download_floor_dxf_dwg(mocker, floor, fixtures_path):
    with ZipFile(
        fixtures_path.joinpath("dxf/AL_Sample building_1OG_DXF.dwg.zip")
    ) as zip_file:
        with zip_file.open("AL_Sample building_1OG_DXF.dwg", "r") as fh:
            file_content = fh.read()

    path_mock = mocker.patch("pathlib.Path.open", mocker.mock_open())
    download_file_mock = mocker.patch.object(
        DMSFloorDeliverableHandler, "download_floor_file", return_value=file_content
    )
    download_floor_dxf_dwg(
        path=Path("noice"), floor=floor, file_format=SUPPORTED_OUTPUT_FILES.DWG
    )
    assert path_mock.mock_calls[0].args[0] == "wb"
    download_file_mock.assert_has_calls(
        [
            call(
                floor_id=floor["id"],
                language=language,
                file_format=SUPPORTED_OUTPUT_FILES.DWG,
            )
            for language in SUPPORTED_LANGUAGES
        ]
    )


def test_generate_unit_plots_task(mocker):
    dummy_site_id = 1
    mock = mocker.patch.object(
        DMSChartDeliverableHandler, "generate_and_upload_apartment_charts"
    )
    generate_unit_plots_task(site_id=dummy_site_id)
    mock.assert_called_once_with(site_id=dummy_site_id)


def test_generate_energt_report_task(mocker):
    dummy_site_id = 1
    mock = mocker.patch.object(
        DMSEnergyReferenceAreaReportHandler,
        "generate_and_upload_energy_reference_area_report",
    )
    generate_energy_reference_area_task(site_id=dummy_site_id)
    mock.assert_called_once_with(site_id=dummy_site_id)
