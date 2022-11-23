import zipfile
from glob import glob
from http import HTTPStatus
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import List, Optional

from cloudconvert.exceptions.exceptions import ClientError, ServerError

from common_utils.constants import (
    GOOGLE_CLOUD_DELIVERABLES,
    SIMULATION_VERSION,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
)
from common_utils.logger import logger
from handlers.utils import get_client_bucket_name
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def task_full_client_zip_delivery(
    self, client_id: int, excluded_site_ids: Optional[List[int]] = None
):
    from handlers import GCloudStorageHandler
    from handlers.db import BuildingDBHandler, ClientDBHandler, SiteDBHandler
    from tasks.utils.deliverable_utils import (
        _building_address,
        _create_path,
        _download_floors_content,
        client_site_id,
    )

    client = ClientDBHandler.get_by(id=client_id)
    with TemporaryDirectory() as fout, NamedTemporaryFile() as fzip:
        client_path = _create_path(base_path=Path(fout), postfix=client["name"])
        for site in SiteDBHandler.find(
            client_id=client_id,
            pipeline_and_qa_complete=True,
            output_columns=["id", "client_site_id"],
        ):
            if excluded_site_ids and site["id"] in excluded_site_ids:
                continue
            site_path = _create_path(
                base_path=client_path, postfix=client_site_id(site)
            )
            for building in BuildingDBHandler.find(site_id=site["id"]):
                building_path = _create_path(
                    base_path=site_path, postfix=_building_address(building)
                )
                _download_floors_content(
                    building=building,
                    site=site,
                    building_path=building_path,
                    client=client,
                )

        for path in client_path.rglob("*.checksum"):
            path.unlink()

        # Compress all files in directory
        with zipfile.ZipFile(fzip.name, "w", zipfile.ZIP_DEFLATED) as zipy:
            for fname in glob(f"{fout}/**/*.*", recursive=True):
                zipy.write(filename=fname, arcname=fname.replace(fout, ""))

        destination_gcs_path = Path(
            GOOGLE_CLOUD_DELIVERABLES.joinpath(
                f"{client['id']}/{client['name']}_delivery.zip"
            )
        )
        GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=get_client_bucket_name(client_id=client_id),
            destination_folder=destination_gcs_path.parent,
            local_file_path=Path(fzip.name),
            destination_file_name=destination_gcs_path.name,
        )


@celery_retry_task
def task_site_zip_deliverable(self, site_id: int):
    """Generates a zipfile from deliverable files and stores it in GOOGLE_CLOUD_BUCKET"""

    from handlers import GCloudStorageHandler, SiteHandler
    from handlers.db import SiteDBHandler
    from tasks.utils.deliverable_utils import generate_results_for_client_and_site

    logger.info(f"Start generation for {site_id} deliverable")
    site = SiteDBHandler.get_by(id=site_id)

    with TemporaryDirectory() as fout, NamedTemporaryFile() as fzip:
        _ = generate_results_for_client_and_site(site=site, output_dir=fout)

        # Compress all files in directory
        with zipfile.ZipFile(fzip.name, "w", zipfile.ZIP_DEFLATED) as zipy:
            for fname in glob(f"{fout}/**/*.*", recursive=True):
                if not fname.endswith(".lock"):
                    zipy.write(filename=fname, arcname=fname.replace(fout, ""))

        destination_gcs_path = SiteHandler.get_deliverable_zipfile_path(
            client_id=site["client_id"], site_id=site_id
        )
        # Upload zipfile into bucket
        GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=get_client_bucket_name(client_id=site["client_id"]),
            destination_folder=destination_gcs_path.parent,
            local_file_path=Path(fzip.name),
            destination_file_name=destination_gcs_path.name,
        )


@celery_retry_task
def generate_building_triangulation_task(self, building_id: int):
    from handlers import BuildingHandler
    from handlers.db import BuildingDBHandler, SiteDBHandler

    building_info = BuildingDBHandler.get_by(id=building_id)
    site_info = SiteDBHandler.get_by(id=building_info["site_id"])
    BuildingHandler(building_id=building_id).generate_and_upload_triangles_to_gcs(
        simulation_version=SIMULATION_VERSION(site_info["simulation_version"])
    )


@celery_retry_task
def generate_unit_pngs_and_pdfs(self, unit_id: int):
    from handlers import DMSUnitDeliverableHandler

    dms_handler = DMSUnitDeliverableHandler()
    for language in SUPPORTED_LANGUAGES:
        for file_format in (SUPPORTED_OUTPUT_FILES.PNG, SUPPORTED_OUTPUT_FILES.PDF):
            logger.info(
                f"generating {file_format.name} file for unit {unit_id} and language {language.name}"
            )
            dms_handler.generate_upload_floorplan(
                unit_id=unit_id,
                language=language,
                file_format=file_format,
            )
            logger.info(
                f"generated {file_format.name} file for unit {unit_id} and language {language.name}"
            )


@celery_retry_task
def generate_pngs_and_pdfs_for_floor_task(self, floor_id: int):
    from handlers import DMSFloorDeliverableHandler

    dms_handler = DMSFloorDeliverableHandler()
    for language in SUPPORTED_LANGUAGES:
        for file_format in (SUPPORTED_OUTPUT_FILES.PNG, SUPPORTED_OUTPUT_FILES.PDF):
            logger.info(
                f"generating {file_format.name} file for floor {floor_id} and language {language.name}"
            )
            dms_handler.generate_upload_floorplan(
                floor_id=floor_id,
                language=language,
                file_format=file_format,
            )
            logger.info(
                f"generated {file_format.name} file for floor {floor_id} and language {language.name}"
            )


@celery_retry_task
def generate_dxf_floor_task(self, floor_id: int):
    """Task that generates all the DXF files of a floor"""
    from handlers import DMSFloorDeliverableHandler

    dms_handler = DMSFloorDeliverableHandler()
    for language in SUPPORTED_LANGUAGES:
        logger.info(
            f"generating dxf file for floor {floor_id} and language {language.name}"
        )
        dms_handler.generate_upload_floorplan(
            floor_id=floor_id,
            language=language,
            file_format=SUPPORTED_OUTPUT_FILES.DXF,
        )
        logger.info(
            f"generated dxf file for floor {floor_id} and language {language.name}"
        )


@celery_retry_task
def generate_dwg_floor_task(self, floor_id: int):
    from handlers import DMSFloorDeliverableHandler

    for language in SUPPORTED_LANGUAGES:
        logger.info(
            f"generating dwg file for floor {floor_id} and language {language.name}"
        )
        try:
            DMSFloorDeliverableHandler.convert_and_upload_dwg(
                floor_id=floor_id, language=language
            )
        except ClientError as exc:
            if exc.response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
                self.retry(exc=exc, countdown=60)
            raise exc
        except ServerError as exc:
            self.retry(exc=exc)

        logger.info(
            f"generated dwg file for floor {floor_id} and language {language.name}"
        )


@celery_retry_task
def generate_ifc_file_task(self, site_id: int):
    from handlers import DMSIFCDeliverableHandler

    DMSIFCDeliverableHandler.generate_ifc_and_upload_to_dms(site_id=site_id)


@celery_retry_task
def generate_vector_files_task(self, site_id: int):
    from handlers import DMSVectorFilesHandler
    from handlers.db import SiteDBHandler

    representative_units_only = not SiteDBHandler.exists(
        id=site_id, sub_sampling_number_of_clusters=None
    )
    DMSVectorFilesHandler.generate_and_upload_vector_files_to_dms(
        site_id=site_id, representative_units_only=representative_units_only
    )


@celery_retry_task
def generate_unit_plots_task(self, site_id: int):
    from handlers import DMSChartDeliverableHandler

    DMSChartDeliverableHandler.generate_and_upload_apartment_charts(site_id=site_id)


@celery_retry_task
def generate_energy_reference_area_task(self, site_id: int):
    from handlers.dms.dms_deliverable_handler import DMSEnergyReferenceAreaReportHandler

    DMSEnergyReferenceAreaReportHandler.generate_and_upload_energy_reference_area_report(
        site_id=site_id
    )
