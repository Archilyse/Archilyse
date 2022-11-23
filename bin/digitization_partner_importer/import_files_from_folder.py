import mimetypes
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, List, Tuple

from tqdm.contrib.concurrent import process_map
from werkzeug.datastructures import FileStorage

from common_utils.logger import logger
from handlers import CloudConvertHandler, FloorHandler
from handlers.db import (
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    SiteDBHandler,
)
from handlers.dxf.dxf_constants import (
    CUSTOM_CLIENT_LETTER_SIGNATURE_FOR_IN_BETWEEN_FLOORS,
)


class DigitizationPartnerDwgFolderImport:
    @classmethod
    def import_dxfs(
        cls, client_name: str, dxf_folder: Path, client_site_ids: set[str] | None = None
    ):
        client = ClientDBHandler.get_by(name=client_name, output_columns=["id"])
        file_mapping, unmapped_files = cls.create_file_floor_mapping(
            client=client, folderpath=dxf_folder
        )
        if unmapped_files:
            logger.error(
                f"DXF files can not be mapped to a site, building or floor: \n {unmapped_files}"
            )

        if client_site_ids is not None:
            file_mapping = [
                x for x in file_mapping if x["client_site_id"] in client_site_ids
            ]

        results = process_map(
            cls.create_floor_from_file, file_mapping, chunksize=1, max_workers=8
        )
        failed_file_imports = {k: v for result in results for k, v in result.items()}

        if failed_file_imports:
            logger.error(failed_file_imports)

    @classmethod
    def create_floor_from_file(cls, input_info: dict) -> dict:
        floor_number = input_info["floor_number"]
        filename = input_info["file_path"].name
        if FloorDBHandler.exists(
            building_id=input_info["building_id"], floor_number=floor_number
        ):
            logger.info(
                f"Skipping creation of floor: {floor_number} using file: {filename}"
            )
        logger.info(f"Creating floor: {floor_number} using file: {filename}")
        try:
            with input_info["file_path"].open("rb") as f:
                FloorHandler.create_floors_from_plan_file(
                    floorplan=FileStorage(
                        stream=f, content_type=mimetypes.types_map[".dxf"]
                    ),
                    building_id=input_info["building_id"],
                    new_floor_numbers={floor_number},
                )
        except Exception as e:
            return {filename: str(e)}
        logger.info(f"Finished floor: {floor_number} using file: {filename}")
        return {}

    @classmethod
    def import_dwgs(cls, client_name: str, zip_folderpath: Path):
        """
        zip folder structure:
        zip folder
        -> 81712, 81713 (site folders)
        -> 84005_B11_O00.1.dwg, 84005_B11_O01.1.dwg (dwg files)
        """
        client = ClientDBHandler.get_by(name=client_name, output_columns=["id"])
        outputpath = (
            Path().home().joinpath(f"Downloads/dwg_import_client_{client['id']}")
        )
        outputpath.mkdir(parents=False, exist_ok=True)
        cls._unzip_folder(zip_folderpath=zip_folderpath, outputpath=outputpath)
        cls._convert_to_dxfs(folderpath=outputpath)
        cls.import_dxfs(client_name=client_name, dxf_folder=outputpath)

    @classmethod
    def create_file_floor_mapping(
        cls, client: Dict, folderpath: Path
    ) -> Tuple[List[Dict], DefaultDict]:
        unmapped_files = defaultdict(list)
        file_mapping = []
        client_site_id_to_id = {
            site["client_site_id"]: site["id"]
            for site in SiteDBHandler.find(
                client_id=client["id"], output_columns=["id", "client_site_id"]
            )
        }
        site_folders = cls._get_site_folders(folderpath=folderpath)
        for site_folder in site_folders:
            client_site_id = site_folder.name
            if client_site_id not in client_site_id_to_id:
                unmapped_files["Client site id not found in database"].append(
                    client_site_id
                )
                continue
            building_client_id_to_id = {
                building["client_building_id"]: building["id"]
                for building in BuildingDBHandler.find(
                    site_id=client_site_id_to_id[client_site_id],
                    output_columns=["id", "client_building_id"],
                )
            }

            file_mapping_current_site = []

            for dxf_file in cls._get_files_by_suffix(suffix=".dxf", folder=site_folder):
                try:
                    (
                        client_building_id,
                        floor_number,
                    ) = cls._get_building_id_floor_number_from_file_name(
                        filename=dxf_file.name
                    )
                except Exception:
                    unmapped_files[
                        "Could not create building id or floor number from file name"
                    ].append(dxf_file.name)
                    continue

                if client_building_id not in building_client_id_to_id:
                    unmapped_files["Client building id not found in database"].append(
                        client_building_id
                    )
                    continue

                file_mapping_current_site.append(
                    {
                        "file_path": dxf_file,
                        "client_site_id": client_site_id,
                        "building_id": building_client_id_to_id[client_building_id],
                        "floor_number": floor_number,
                    }
                )

            file_mapping_current_site = cls.ensure_unique_floor_numbers(
                file_mapping_current_site=file_mapping_current_site
            )
            file_mapping.extend(file_mapping_current_site)

        if missing_site_folders := {
            key for key in client_site_id_to_id.keys()
        }.difference({site_folder.name for site_folder in site_folders}):
            unmapped_files["missing_site_folders"] = list(missing_site_folders)

        return file_mapping, unmapped_files

    @staticmethod
    def _get_building_id_floor_number_from_file_name(filename: str) -> Tuple[str, int]:
        filename = filename.replace(".dxf", "")
        _, raw_building_id, raw_floor_number = filename.split("_")
        building_id = raw_building_id.replace("B", "")
        floor_number = int(
            raw_floor_number.replace(".1", "")
            .replace("O", "")
            .replace("U", "-")
            .replace("F", "")
        )
        return building_id, floor_number

    @staticmethod
    def ensure_unique_floor_numbers(
        file_mapping_current_site: List[Dict],
    ) -> List[Dict]:
        file_mapping_by_building = defaultdict(list)
        for file_mapping in file_mapping_current_site:
            file_mapping_by_building[file_mapping["building_id"]].append(file_mapping)

        for files_mapping in file_mapping_by_building.values():
            unique_floor_numbers = {
                file_mapping["floor_number"] for file_mapping in files_mapping
            }
            if len(unique_floor_numbers) != len(files_mapping):
                for i, file in enumerate(files_mapping):
                    if (
                        CUSTOM_CLIENT_LETTER_SIGNATURE_FOR_IN_BETWEEN_FLOORS
                        in file["file_path"].name
                    ):
                        for j, other_file in enumerate(files_mapping):
                            if i == j:
                                continue
                            if other_file["floor_number"] > file["floor_number"]:
                                other_file["floor_number"] += 1
                        file["floor_number"] += 1
        return file_mapping_current_site

    @classmethod
    def _convert_to_dxfs(cls, folderpath: Path):
        source_file_paths = [
            file
            for folder in cls._get_site_folders(folderpath=folderpath)
            for file in cls._get_files_by_suffix(suffix=".dwg", folder=folder)
            if not file.with_suffix(".dxf").exists()
        ]

        destination_file_paths = [
            file.with_suffix(".dxf") for file in source_file_paths
        ]
        input_format = ["dwg"] * len(source_file_paths)
        output_format = ["dxf"] * len(source_file_paths)
        process_map(
            CloudConvertHandler().transform,
            source_file_paths,
            destination_file_paths,
            input_format,
            output_format,
            max_workers=8,
        )

    @staticmethod
    def _unzip_folder(zip_folderpath: Path, outputpath: Path):
        with zipfile.ZipFile(zip_folderpath, "r") as file:
            file.extractall(path=outputpath)

    @staticmethod
    def _get_site_folders(folderpath: Path) -> List[Path]:
        return [f for f in folderpath.iterdir() if f.is_dir()]

    @classmethod
    def _get_files_by_suffix(cls, suffix: str, folder: Path) -> List[Path]:
        return [file for file in folder.iterdir() if file.suffix == suffix]


if __name__ == "__main__":
    DigitizationPartnerDwgFolderImport.import_dwgs(
        client_name="CustomClient2",
        zip_folderpath=Path().home().joinpath("Downloads/CustomClient2/16211.zip"),
    )
