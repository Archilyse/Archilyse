from pathlib import Path, PosixPath

import pytest

from bin.digitization_partner_importer.import_files_from_folder import (
    DigitizationPartnerDwgFolderImport,
)
from handlers.db import BuildingDBHandler, SiteDBHandler


class TestDigitizationPartnerDwgFolderImport:
    @staticmethod
    @pytest.mark.parametrize(
        "filename,expected_building_id,expected_floor_number",
        [
            ("84178_B04_O00.1.dxf", "04", 0),
            ("84178_B05_U01.1.dxf", "05", -1),
            ("84178_B04_F00.1.dxf", "04", 0),
        ],
    )
    def test_get_building_id_floor_number_from_file_name(
        filename, expected_building_id, expected_floor_number
    ):
        (
            building_id,
            floor_number,
        ) = DigitizationPartnerDwgFolderImport._get_building_id_floor_number_from_file_name(
            filename=filename
        )
        assert building_id == expected_building_id
        assert floor_number == expected_floor_number

    @staticmethod
    def test_get_mapped_and_unmapped_files(mocker):
        mocker.patch.object(
            SiteDBHandler,
            "find",
            return_value=[
                {"id": 1, "client_site_id": "80420"},
                {"id": 2, "client_site_id": "80421"},
            ],
        )
        mocker.patch.object(
            BuildingDBHandler,
            "find",
            return_value=[{"id": 1, "client_building_id": "01"}],
        )
        mocker.patch.object(
            DigitizationPartnerDwgFolderImport,
            "_get_site_folders",
            return_value=[
                Path("80420"),
                Path("Not existing 1"),
                Path("Not existing 2"),
            ],
        )
        mocker.patch.object(
            DigitizationPartnerDwgFolderImport,
            "_get_files_by_suffix",
            return_value=[
                Path("invalid filename 1"),
                Path("invalid filename 2"),
                Path("80420_B05_U01.1.dxf"),
                Path("80420_B01_O03.1.dxf"),
            ],
        )

        (
            mapped_files,
            unmapped_files,
        ) = DigitizationPartnerDwgFolderImport.create_file_floor_mapping(
            client={"id": None}, folderpath=None
        )

        assert mapped_files == [
            {
                "file_path": PosixPath("80420_B01_O03.1.dxf"),
                "building_id": 1,
                "floor_number": 3,
                "client_site_id": "80420",
            }
        ]

        assert unmapped_files == {
            "Could not create building id or floor number from file name": [
                "invalid filename 1",
                "invalid filename 2",
            ],
            "Client building id not found in database": ["05"],
            "Client site id not found in database": [
                "Not existing 1",
                "Not existing 2",
            ],
            "missing_site_folders": ["80421"],
        }

    @staticmethod
    def test_get_file_mapping_with_in_between_floors(mocker):
        mocker.patch.object(
            SiteDBHandler,
            "find",
            return_value=[
                {"id": 1, "client_site_id": "80420"},
            ],
        )
        mocker.patch.object(
            BuildingDBHandler,
            "find",
            return_value=[{"id": 1, "client_building_id": "01"}],
        )
        mocker.patch.object(
            DigitizationPartnerDwgFolderImport,
            "_get_site_folders",
            return_value=[
                Path("80420"),
            ],
        )
        mocker.patch.object(
            DigitizationPartnerDwgFolderImport,
            "_get_files_by_suffix",
            return_value=[
                Path("80420_B01_O00.1.dxf"),
                Path("80420_B01_O01.1.dxf"),
                Path("80420_B01_F00.1.dxf"),
            ],
        )

        mapped_files, _ = DigitizationPartnerDwgFolderImport.create_file_floor_mapping(
            client={"id": None}, folderpath=None
        )
        assert len(mapped_files) == 3
        assert (
            mapped_files[0]["file_path"].name == "80420_B01_O00.1.dxf"
            and mapped_files[0]["floor_number"] == 0
        )
        assert (
            mapped_files[1]["file_path"].name == "80420_B01_O01.1.dxf"
            and mapped_files[1]["floor_number"] == 2
        )
        assert (
            mapped_files[2]["file_path"].name == "80420_B01_F00.1.dxf"
            and mapped_files[2]["floor_number"] == 1
        )

    @staticmethod
    def test_ensure_unique_floor_numbers():
        file_mapping = [
            {"building_id": "02", "floor_number": 6, "file_path": Path("")},
            {
                "building_id": "01",
                "floor_number": -1,
                "file_path": Path("80420_B01_U01.1.dxf"),
            },
            {
                "building_id": "01",
                "floor_number": 0,
                "file_path": Path("80420_B01_O00.1.dxf"),
            },
            {
                "building_id": "01",
                "floor_number": 0,
                "file_path": Path("80420_B01_F00.1.dxf"),
            },
            {
                "building_id": "01",
                "floor_number": 1,
                "file_path": Path("80420_B01_O01.1.dxf"),
            },
            {
                "building_id": "01",
                "floor_number": 1,
                "file_path": Path("80420_B01_F01.1.dxf"),
            },
            {
                "building_id": "01",
                "floor_number": 2,
                "file_path": Path("80420_B01_O02.1.dxf"),
            },
        ]
        new_file_mapping = (
            DigitizationPartnerDwgFolderImport.ensure_unique_floor_numbers(
                file_mapping_current_site=file_mapping
            )
        )
        assert [mapping["floor_number"] for mapping in new_file_mapping] == [
            6,
            -1,
            0,
            1,
            2,
            3,
            4,
        ]
