from pathlib import Path

from bin.digitization_partner_importer.import_files_from_folder import (
    DigitizationPartnerDwgFolderImport,
)
from handlers import PlanHandler
from handlers.db import ClientDBHandler, FloorDBHandler, PlanDBHandler


class TestDigitizationPartnerDwgFolderImport:
    @staticmethod
    def test_import_dwgs_plan_deduplication_works(
        mocker, site, building, plan, floor, fixtures_path
    ):
        mocker.patch.object(Path, "mkdir")
        unzip_folder_mock = mocker.patch.object(
            DigitizationPartnerDwgFolderImport, "_unzip_folder"
        )
        convert_dwg_to_dxf_mock = mocker.patch.object(
            DigitizationPartnerDwgFolderImport, "_convert_to_dxfs"
        )
        mocker.patch.object(ClientDBHandler, "get_by", return_value={"id": 1})
        mocker.patch.object(
            DigitizationPartnerDwgFolderImport,
            "create_file_floor_mapping",
            return_value=(
                [
                    {
                        "file_path": fixtures_path.joinpath(
                            "dxf/AL_Sample building_1OG_DXF.dxf.zip"
                        ),
                        "building_id": building["id"],
                        "floor_number": 2,
                    }
                ],
                None,
            ),
        )
        mocker.patch.object(PlanHandler, "add", return_value=plan)

        DigitizationPartnerDwgFolderImport.import_dwgs(
            client_name=None, zip_folderpath=None
        )

        assert unzip_folder_mock.called
        assert convert_dwg_to_dxf_mock.called

        assert len(PlanDBHandler.find()) == 1
        floors = FloorDBHandler.find()
        assert len(floors) == 2
        assert {floor["floor_number"] for floor in floors} == {1, 2}
