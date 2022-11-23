import contextlib
import csv
import io
import mimetypes
import zipfile
from glob import glob
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import IO, TYPE_CHECKING, Dict, List, Optional, Set, Union

from google.cloud.exceptions import NotFound
from werkzeug.datastructures import FileStorage

from common_utils.constants import (
    BENCHMARK_DATASET_CLUSTER_SIZES_PATH,
    BENCHMARK_DATASET_DIR,
    BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH,
    BENCHMARK_PERCENTILES_DIMENSIONS_PATH,
    DEFAULT_RESULT_VECTORS,
    GOOGLE_CLOUD_BENCHMARK_APARTMENT_SCORES,
    GOOGLE_CLOUD_BENCHMARK_CLUSTER_SIZES,
    GOOGLE_CLOUD_BENCHMARK_PERCENTILES,
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_CLOUD_CONVERT_FILES,
    RESULT_VECTORS,
    SIMULATION_VERSION,
    SUN_V2_VECTOR_PREFIX,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
)
from common_utils.exceptions import PHVectorSubgroupException
from common_utils.logger import logger
from handlers.cloud_convert import CloudConvertHandler
from handlers.db import FileDBHandler, FloorDBHandler, FolderDBHandler, SiteDBHandler
from handlers.energy_reference_area.main_report import EnergyAreaReportForSite
from handlers.plan_layout_handler import PlanLayoutHandlerIDCacheMixin
from handlers.utils import get_client_bucket_name

if TYPE_CHECKING:
    from handlers import PlanLayoutHandler


class DMSDeliverableMixin:
    @staticmethod
    def suffix_normalization(extension: str):
        return extension.lower()

    @classmethod
    def create_or_replace_dms_file(
        cls,
        buff: IO,
        filename: str,
        client_id: int,
        site_id: int,
        extension: str,
        labels: Optional[List[str]] = None,
        building_id: Optional[int] = None,
        floor_id: Optional[int] = None,
        unit_id: Optional[int] = None,
        area_id: Optional[int] = None,
        folder_id: Optional[int] = None,
    ):
        from handlers import FileHandler

        if not extension.startswith("."):
            extension = f".{cls.suffix_normalization(extension=extension)}"

        file_obj = FileStorage(
            stream=buff, filename=filename, content_type=mimetypes.types_map[extension]
        )

        existing_files = FileDBHandler.find(
            client_id=client_id,
            site_id=site_id,
            building_id=building_id,
            floor_id=floor_id,
            unit_id=unit_id,
            area_id=area_id,
            name=filename,
            output_columns=["id"],
        )
        for file in existing_files:
            FileHandler.remove(file_id=file["id"])

        FileHandler.create(
            user_id=None,
            client_id=client_id,
            filename=filename,
            site_id=site_id,
            file_obj=file_obj,
            labels=labels,
            building_id=building_id,
            floor_id=floor_id,
            unit_id=unit_id,
            area_id=area_id,
            folder_id=folder_id,
        )
        file_obj.close()

    @classmethod
    def download_file(cls, client_id: int, name: str, **kwargs) -> bytes:
        from handlers import FileHandler

        file = FileDBHandler.get_by(client_id=client_id, name=name, **kwargs)
        return FileHandler.download(client_id=client_id, checksum=file["checksum"])


class DMSIFCDeliverableHandler(DMSDeliverableMixin):
    default_ifc_tags = ["3D", "BIM", "IFC"]

    @staticmethod
    def _get_exported_ifc_file_name(site: dict) -> str:
        prefix = site["client_site_id"] or site["name"]
        return f"{prefix} - Exported IFC {SUPPORTED_LANGUAGES.EN.name.lower()}.zip"

    @staticmethod
    def _get_ifc_file_name_inside_zip(site_name: str):
        return f"{''.join(e for e in site_name if e.isalnum())}.ifc"

    @classmethod
    def generate_ifc_and_upload_to_dms(cls, site_id: int):
        from handlers.ifc import IfcExportHandler

        site_data = SiteDBHandler.get_by(id=site_id)
        with NamedTemporaryFile() as temp_file:
            local_file_path = Path(temp_file.name)
            IfcExportHandler(site_id=site_id).export_site(
                output_filename=local_file_path.as_posix()
            )

            zip_extension = ".zip"
            compressed_file = local_file_path.with_suffix(zip_extension)

            with zipfile.ZipFile(
                file=compressed_file,
                mode="w",
                compression=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            ) as zipy:
                zipy.write(
                    filename=local_file_path.as_posix(),
                    arcname=cls._get_ifc_file_name_inside_zip(
                        site_name=site_data["name"]
                    ),
                )
            with compressed_file.open("rb") as f:
                cls.create_or_replace_dms_file(
                    buff=f,
                    filename=cls._get_exported_ifc_file_name(site=site_data),
                    client_id=site_data["client_id"],
                    site_id=site_id,
                    labels=cls.default_ifc_tags,
                    extension=zip_extension,
                )

    @classmethod
    def download_ifc_file(cls, site_id: int) -> bytes:
        site = SiteDBHandler.get_by(
            id=site_id, output_columns=["client_id", "name", "client_site_id"]
        )
        return cls.download_file(
            site_id=site_id,
            client_id=site["client_id"],
            name=cls._get_exported_ifc_file_name(site=site),
        )


class DMSFloorDeliverableHandler(DMSDeliverableMixin, PlanLayoutHandlerIDCacheMixin):
    def generate_upload_floorplan(
        self,
        floor_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ):
        from handlers import FloorHandler

        io_image, filename, site_info = FloorHandler(
            layout_handler_by_id=self._layout_handler_by_id
        ).generate_floorplan_image(
            floor_id=floor_id, file_format=file_format, language=language
        )
        self.create_or_replace_dms_file(
            client_id=site_info["client_id"],
            site_id=site_info["id"],
            floor_id=floor_id,
            filename=filename,
            extension=file_format.name,
            labels=[file_format.name],
            buff=io_image,
        )

    @classmethod
    def get_file_info(
        cls,
        floor_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ):
        from handlers import FloorHandler

        site = SiteDBHandler.get_by_floor_id(floor_id=floor_id)
        floor = FloorDBHandler.get_by(
            id=floor_id, output_columns=["building_id", "floor_number"]
        )
        # This is exceptionally retuning file names with capital letters .PNG, .PDF, etc.
        image_filename = FloorHandler.get_gcs_floorplan_image_filename(
            site_id=site["id"],
            building_id=floor["building_id"],
            floor_number=floor["floor_number"],
            language=language,
            file_format=file_format,
        )
        return FileDBHandler.get_by(
            client_id=site["client_id"],
            name=image_filename,
            floor_id=floor_id,
        )

    @classmethod
    def download_floor_file(
        cls,
        floor_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> bytes:
        from handlers import FileHandler

        file_info = cls.get_file_info(
            floor_id=floor_id, language=language, file_format=file_format
        )
        return FileHandler.download(
            client_id=file_info["client_id"], checksum=file_info["checksum"]
        )

    @classmethod
    def convert_and_upload_dwg(cls, floor_id: int, language: SUPPORTED_LANGUAGES):
        from handlers import FileHandler, GCloudStorageHandler

        dxf_file_info = DMSFloorDeliverableHandler.get_file_info(
            floor_id=floor_id, language=language, file_format=SUPPORTED_OUTPUT_FILES.DXF
        )
        client_bucket = get_client_bucket_name(client_id=dxf_file_info["client_id"])
        source_medialink = FileHandler.get_media_link(
            bucket=client_bucket, file_checksum=dxf_file_info["checksum"]
        )
        dwg_filepath = Path(dxf_file_info["name"]).with_suffix(
            f".{cls.suffix_normalization(extension=SUPPORTED_OUTPUT_FILES.DWG.name)}"
        )
        file_content = CloudConvertHandler().transform_gcloud_file(
            source_bucket=client_bucket,
            source_medialink=source_medialink,
            destination_bucket=client_bucket,
            destination_folder=GOOGLE_CLOUD_CLOUD_CONVERT_FILES,
            destination_filename=dwg_filepath.as_posix(),
            input_format=cls.suffix_normalization(
                extension=SUPPORTED_OUTPUT_FILES.DXF.name
            ),
            output_format=cls.suffix_normalization(
                extension=SUPPORTED_OUTPUT_FILES.DWG.name
            ),
        )
        with io.BytesIO(file_content) as file_obj:
            cls.create_or_replace_dms_file(
                client_id=dxf_file_info["client_id"],
                site_id=dxf_file_info["site_id"],
                floor_id=floor_id,
                filename=dwg_filepath.as_posix(),
                extension=SUPPORTED_OUTPUT_FILES.DWG.name,
                labels=[SUPPORTED_OUTPUT_FILES.DWG.name],
                buff=file_obj,
            )

            # Deletes the temporary file after conversion
            GCloudStorageHandler().delete_resource(
                bucket_name=client_bucket,
                source_folder=GOOGLE_CLOUD_CLOUD_CONVERT_FILES,
                filename=dwg_filepath,
            )


class DMSUnitDeliverableHandler(DMSDeliverableMixin, PlanLayoutHandlerIDCacheMixin):
    def __init__(
        self, layout_handler_by_id: Optional[Dict[int, "PlanLayoutHandler"]] = None
    ):
        super().__init__(layout_handler_by_id=layout_handler_by_id)
        from handlers import UnitHandler

        self.unit_handler = UnitHandler(layout_handler_by_id=layout_handler_by_id)

    def generate_upload_floorplan(
        self,
        unit_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ):

        io_image, filename, site_info = self.unit_handler.generate_floorplan_image(
            unit_id=unit_id, file_format=file_format, language=language
        )
        self.create_or_replace_dms_file(
            client_id=site_info["client_id"],
            site_id=site_info["id"],
            unit_id=unit_id,
            filename=filename,
            extension=file_format.name,
            labels=[file_format.name],
            buff=io_image,
        )

    @classmethod
    def download_unit_file(
        cls,
        client_id: int,
        unit_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ):
        from handlers import FileHandler, UnitHandler

        filename = UnitHandler().get_floorplan_image_filename(
            unit_id=unit_id, language=language, file_format=file_format
        )
        file_info = FileDBHandler.get_by(
            client_id=client_id,
            name=filename,
            unit_id=unit_id,
        )
        return FileHandler.download(client_id=client_id, checksum=file_info["checksum"])


class DMSVectorFilesHandler(DMSDeliverableMixin):
    FOLDERNAME = "Vectors"

    @classmethod
    def generate_and_upload_vector_files_to_dms(
        cls,
        site_id: int,
        representative_units_only: bool,
    ):
        with TemporaryDirectory() as tempfolder:
            site = SiteDBHandler.get_by(
                id=site_id,
                output_columns=[
                    "id",
                    "client_id",
                    "client_site_id",
                    "simulation_version",
                ],
            )
            cls._generate_vector_files(
                site=site,
                folderpath=Path(tempfolder),
                representative_units_only=representative_units_only,
            )
            folder = cls._create_or_replace_dms_folder(
                foldername=cls.FOLDERNAME,
                client_id=site["client_id"],
                site_id=site["id"],
            )
            cls._upload_files_to_dms(
                site=site, folder_id=folder["id"], folderpath=Path(tempfolder)
            )

    @classmethod
    def download_vector_files(cls, site_id: int, download_path: Path):
        from handlers import FileHandler, FolderHandler

        site = SiteDBHandler.get_by(
            id=site_id,
            output_columns=["id", "client_id", "client_site_id", "simulation_version"],
        )
        if folder := cls._get_existing_dms_folder(
            foldername=cls.FOLDERNAME, client_id=site["client_id"], site_id=site["id"]
        ):
            for file in FolderHandler.get_files_of_folder(
                folder_id=folder["id"], deleted=False
            ):
                with download_path.joinpath(file["name"]).open("wb") as f:
                    f.write(
                        FileHandler.download(
                            client_id=site["client_id"], checksum=file["checksum"]
                        )
                    )
        else:
            cls._generate_vector_files(
                site=site,
                folderpath=download_path,
                representative_units_only=False,
            )

    @classmethod
    def _upload_files_to_dms(cls, site: Dict, folder_id: int, folderpath: Path):
        for file_path in folderpath.iterdir():
            with file_path.open(mode="rb") as csv_file:
                # in cases where we only have commercial units, we won't have any information in the csvs
                if file_path.stat().st_size > 0:
                    cls.create_or_replace_dms_file(
                        buff=csv_file,
                        filename=file_path.name,
                        client_id=site["client_id"],
                        site_id=site["id"],
                        extension=".csv",
                        folder_id=folder_id,
                    )

    @classmethod
    def _create_or_replace_dms_folder(
        cls,
        foldername: str,
        client_id: int,
        site_id: int,
    ) -> Dict:
        from handlers import FolderHandler

        if existing_folder := cls._get_existing_dms_folder(
            foldername=foldername,
            client_id=client_id,
            site_id=site_id,
        ):
            with contextlib.suppress(NotFound):
                FolderHandler.remove(folder_id=existing_folder["id"])

        return FolderDBHandler.add(
            creator_id=None, name=foldername, client_id=client_id, site_id=site_id
        )

    @classmethod
    def _get_existing_dms_folder(
        cls, foldername: str, client_id: int, site_id: int
    ) -> Union[None, Dict]:
        from handlers import FolderHandler

        existing_folders = list(
            FolderHandler.get(
                name=foldername,
                client_id=client_id,
                site_id=site_id,
                building_id=None,
                floor_id=None,
                unit_id=None,
                area_id=None,
                output_columns=["id"],
                return_subdocuments=False,
            )
        )
        if existing_folders:
            return existing_folders[0]

        return None

    @classmethod
    def _generate_vector_files(
        cls,
        site: Dict,
        folderpath: Path,
        representative_units_only: bool,
        subgroups: Optional[Dict[str, Set[str]]] = None,
        subgroups_match_client_ids_exact: bool = False,
        subgroups_allow_subset: bool = False,
    ):
        if site["simulation_version"] in {
            SIMULATION_VERSION.EXPERIMENTAL.name,
            SIMULATION_VERSION.PH_2022_H1.name,
        }:
            from handlers.ph_vector.ph2022 import (
                PH2022ResultVectorHandler,
                PHResultVectorCSVWriter,
            )

            vectors = PH2022ResultVectorHandler.generate_vectors(
                site_id=site["id"], representative_units_only=representative_units_only
            )
            PHResultVectorCSVWriter.write_to_csv(vectors=vectors, directory=folderpath)
        else:

            from tasks.utils.deliverable_utils import (
                client_site_id,
                get_index_by_result_type,
            )

            index: Dict[str, List[Dict]] = get_index_by_result_type(
                site_id=site["id"],
                representative_units_only=representative_units_only,
            )
            client_site_id = client_site_id(site=site)

            for vector in DEFAULT_RESULT_VECTORS:
                unit_vectors = cls._get_unit_vectors(index=index, vector=vector)
                if not subgroups:
                    cls._create_vector_csv(
                        filepath=folderpath.joinpath(
                            f"{client_site_id}-{vector.value}.csv"
                        ),
                        unit_vectors=unit_vectors,
                    )
                else:
                    cls._create_vector_csv_by_subgroups(
                        unit_vectors=unit_vectors,
                        subgroups=subgroups,
                        folderpath=folderpath,
                        client_site_id=client_site_id,
                        vector=vector,
                        match_client_ids_exact=subgroups_match_client_ids_exact,
                        allow_subset=subgroups_allow_subset,
                    )

    @classmethod
    def _create_vector_csv_by_subgroups(
        cls,
        unit_vectors: List[dict],
        subgroups: Dict[str, Set[str]],
        folderpath: Path,
        client_site_id: str,
        vector: RESULT_VECTORS,
        match_client_ids_exact: bool,
        allow_subset: bool,
    ):
        covered_units = set()
        expected_units = {unit_vector["client_id"] for unit_vector in unit_vectors}

        for subgroup_name, subgroup_tags in subgroups.items():
            logger.info(
                f"Downloading vectors for site {client_site_id} and subgroup {subgroup_name}."
            )
            filepath = folderpath.joinpath(
                f"{subgroup_name}--{client_site_id}-{vector.value}.csv"
            )
            subgroup_unit_vectors = []
            for unit_vector in unit_vectors:
                if match_client_ids_exact:
                    matched = any(
                        [tag == unit_vector["client_id"] for tag in subgroup_tags]
                    )
                else:
                    matched = any(
                        [tag in unit_vector["client_id"] for tag in subgroup_tags]
                    )

                if matched:
                    subgroup_unit_vectors.append(unit_vector)
                    covered_units.add(unit_vector["client_id"])

            cls._create_vector_csv(
                filepath=filepath,
                unit_vectors=subgroup_unit_vectors,
            )
            logger.info(
                f"Created vector for subgroup {subgroup_name} with units {', '.join(sorted(covered_units))}."
            )
        if not allow_subset and expected_units.difference(covered_units):
            raise PHVectorSubgroupException(
                "The tags provided to subgroup units by their unit client id is insufficient "
                "and leads to loss of units in the result"
            )

    @staticmethod
    def _create_vector_csv(filepath: Path, unit_vectors: List[dict]):
        with filepath.open(mode="w") as csv_file:

            writer: csv.DictWriter = csv.DictWriter(
                f=csv_file,
                fieldnames=list(
                    {key for unit_vector in unit_vectors for key in unit_vector.keys()}
                ),
            )
            writer.writeheader()
            writer.writerows(unit_vectors)

    @staticmethod
    def _get_unit_vectors(
        index: Dict[str, List[Dict]], vector: RESULT_VECTORS
    ) -> List[Dict]:
        from tasks.utils.deliverable_utils import BLACKLISTED_FIELDS

        unit_vectors = sorted(
            index[vector.value],
            key=lambda x: (x["floor_number"], x["apartment_no"]),
        )

        for unit_vector in unit_vectors:
            for field in list(unit_vector.keys()):
                if SUN_V2_VECTOR_PREFIX not in field and "Sun." in field:
                    del unit_vector[field]

            for blacklisted_field in BLACKLISTED_FIELDS:
                if blacklisted_field in unit_vector:
                    del unit_vector[blacklisted_field]
        return unit_vectors


class DMSChartDeliverableHandler(DMSDeliverableMixin):
    REQUIRED_FILES: dict[Path, Path] = {
        BENCHMARK_PERCENTILES_APARTMENT_SCORES_PATH: GOOGLE_CLOUD_BENCHMARK_APARTMENT_SCORES,
        BENCHMARK_PERCENTILES_DIMENSIONS_PATH: GOOGLE_CLOUD_BENCHMARK_PERCENTILES,
        BENCHMARK_DATASET_CLUSTER_SIZES_PATH: GOOGLE_CLOUD_BENCHMARK_CLUSTER_SIZES,
    }

    @classmethod
    def generate_and_upload_apartment_charts(cls, site_id: int):
        from handlers.charts.chart_generator import ApartmentChartGenerator

        cls._download_reference_dataset()

        with TemporaryDirectory() as temporary_directory:
            output_main_folder = Path(temporary_directory)
            output_main_folder.mkdir(exist_ok=True, parents=True)

            exporter = ApartmentChartGenerator(
                site_id=site_id, output_dir=output_main_folder
            )
            exporter.generate_default_charts()
            exporter.generate_default_chart_index()
            exporter.generate_default_data_sheets()

            with NamedTemporaryFile(suffix=".zip") as temp_file:
                with zipfile.ZipFile(temp_file.name, "w", zipfile.ZIP_DEFLATED) as zipy:
                    for fname in glob(f"{output_main_folder}/**/*.*", recursive=True):
                        zipy.write(
                            filename=fname,
                            arcname=fname.replace(output_main_folder.as_posix(), ""),
                        )

                site = SiteDBHandler.get_by(
                    id=site_id, output_columns=["client_id", "client_site_id", "name"]
                )
                prefix = site["client_site_id"] or site["name"]
                filename = f"{prefix} - Apartment Charts.zip"

                with Path(temp_file.name).open("rb") as f:
                    cls.create_or_replace_dms_file(
                        client_id=site["client_id"],
                        site_id=site_id,
                        filename=filename,
                        labels=["Benchmarks"],
                        extension=".zip",
                        buff=f,
                    )

    @classmethod
    def _download_reference_dataset(cls):
        from handlers import GCloudStorageHandler

        BENCHMARK_DATASET_DIR.mkdir(parents=True, exist_ok=True)
        for local_file_path, google_cloud_path in cls.REQUIRED_FILES.items():
            if not local_file_path.exists():
                with NamedTemporaryFile(suffix=".zip") as temp_file:
                    path = Path(temp_file.name)
                    GCloudStorageHandler().download_file(
                        bucket_name=GOOGLE_CLOUD_BUCKET,
                        remote_file_path=google_cloud_path,
                        local_file_name=path,
                    )
                    with zipfile.ZipFile(path, "r") as file:
                        file.extractall(path=BENCHMARK_DATASET_DIR)

            if not local_file_path.exists():
                raise FileNotFoundError(
                    f"There was a problem extracting the correct file {local_file_path.as_posix()} from gcloud://{google_cloud_path.as_posix()}. The directory looks like this: {','.join(map(str, BENCHMARK_DATASET_DIR.glob('**')))}"
                )


class DMSEnergyReferenceAreaReportHandler(DMSDeliverableMixin):
    @classmethod
    def generate_and_upload_energy_reference_area_report(cls, site_id: int):
        with NamedTemporaryFile(suffix=".xlsx") as file:
            EnergyAreaReportForSite.create_report(
                site_id=site_id, outputpath=Path(file.name)
            )
            site = SiteDBHandler.get_by(
                id=site_id, output_columns=["client_id", "client_site_id", "name"]
            )
            prefix = site["client_site_id"] or site["name"]
            filename = f"{prefix} - Energy Reference Area Report.xlsx"
            with Path(file.name).open(mode="rb") as f:
                cls.create_or_replace_dms_file(
                    client_id=site["client_id"],
                    site_id=site_id,
                    filename=filename,
                    labels=["EBF"],
                    extension=".xlsx",
                    buff=f,
                )
