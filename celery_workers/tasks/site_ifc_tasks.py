from pathlib import Path
from tempfile import NamedTemporaryFile

from shapely.geometry import MultiPoint, Point

from common_utils.constants import ADMIN_SIM_STATUS
from handlers.db import PlanDBHandler, SiteDBHandler
from handlers.utils import get_client_bucket_name
from tasks.utils.utils import celery_retry_task
from workers_config.celery_app import celery_app


@celery_retry_task
def create_ifc_entities_from_site_task(self, site_id: int):
    from handlers import GCloudStorageHandler, SiteHandler
    from handlers.ifc import IfcToSiteHandler
    from ifc_reader.reader import IfcReader

    site = SiteDBHandler.update(
        item_pks={"id": site_id},
        new_values={"ifc_import_status": ADMIN_SIM_STATUS.PROCESSING.value},
    )
    ifc_site_coordinates = []
    for ifc_filename, ifc_file_gcs_link in site["gcs_ifc_file_links"].items():
        with NamedTemporaryFile() as temp_file:
            path_file = Path(temp_file.name)
            GCloudStorageHandler().download_file_from_media_link(
                source_media_link=ifc_file_gcs_link,
                destination_file=path_file,
                bucket_name=get_client_bucket_name(client_id=site["client_id"]),
            )

            ifc_reader = IfcReader(filepath=path_file)
            handler = IfcToSiteHandler(ifc_reader=ifc_reader)
            handler.create_and_save_site_entities(
                site_id=site_id, ifc_filename=ifc_filename
            )

            site_coordinates: Point = ifc_reader.reference_point
            ifc_site_coordinates.append(site_coordinates)

    site_center = MultiPoint([p for p in ifc_site_coordinates]).centroid
    SiteHandler.update(
        site_id=site_id,
        lon=site_center.x,
        lat=site_center.y,
    )


@celery_retry_task
def ifc_create_plan_areas_task(self, site_id: int):
    from handlers.plan_utils import create_areas_for_plan

    for plan_id in PlanDBHandler.find_ids(site_id=site_id):
        create_areas_for_plan(plan_id=plan_id, preclassify=True)


@celery_app.task(bind=True)
def ifc_import_success(self, site_id: int):
    SiteDBHandler.update(
        item_pks={"id": site_id},
        new_values={"ifc_import_status": ADMIN_SIM_STATUS.SUCCESS.value},
    )


@celery_app.task
def ifc_import_errors(request, exc, traceback, site_id: int):
    SiteDBHandler.update(
        item_pks={"id": site_id},
        new_values={
            "ifc_import_status": ADMIN_SIM_STATUS.FAILURE.value,
            "ifc_import_exceptions": {"msg": str(exc), "code": type(exc).__name__},
        },
    )


def get_ifc_import_task_chain(site_id: int):
    task_chain = (
        create_ifc_entities_from_site_task.si(site_id=site_id)
        | ifc_create_plan_areas_task.si(site_id=site_id)
        | ifc_import_success.si(site_id=site_id)
    )
    task_chain.on_error(ifc_import_errors.s(site_id=site_id))
    return task_chain
