from collections import defaultdict
from concurrent import futures
from typing import List

from common_utils.constants import GOOGLE_CLOUD_BUCKET
from common_utils.exceptions import GCSLinkEmptyException
from common_utils.logger import logger
from tasks.utils.utils import celery_retry_task

COLUMN_NAME_TO_BUCKET_MAPPING = {"gcs_buildings_link": GOOGLE_CLOUD_BUCKET}


@celery_retry_task()
def check_dead_gcs_links_task(self):
    from handlers import GCloudStorageHandler
    from handlers.db import (
        BuildingDBHandler,
        ClientDBHandler,
        FloorDBHandler,
        PlanDBHandler,
        SiteDBHandler,
        UnitDBHandler,
    )

    errors_by_handler_and_id = defaultdict(default_dict_wrapper)
    gcloud_handler = GCloudStorageHandler()
    with futures.ThreadPoolExecutor(max_workers=50) as executor:
        executors = []
        for client in ClientDBHandler.find(output_columns=["id"]):
            common_args = {
                "client_id": client["id"],
                "gcloud_handler": gcloud_handler,
                "errors_by_handler_and_id": errors_by_handler_and_id,
                "executors": executors,
                "executor": executor,
            }
            for site in SiteDBHandler.find(
                client_id=client["id"], output_columns=["id"]
            ):
                add_executors(
                    handler=SiteDBHandler, entity_id=site["id"], **common_args
                )
                for building in BuildingDBHandler.find(
                    site_id=site["id"], output_columns=["id"]
                ):
                    add_executors(
                        handler=BuildingDBHandler,
                        entity_id=building["id"],
                        **common_args,
                    )
                    for plan in PlanDBHandler.find(
                        building_id=building["id"], output_columns=["id"]
                    ):
                        add_executors(
                            handler=PlanDBHandler, entity_id=plan["id"], **common_args
                        )
                    for floor in FloorDBHandler.find(
                        building_id=building["id"], output_columns=["id"]
                    ):
                        add_executors(
                            handler=FloorDBHandler, entity_id=floor["id"], **common_args
                        )
                        for unit in UnitDBHandler.find(
                            floor_id=floor["id"], output_columns=["id"]
                        ):
                            add_executors(
                                handler=UnitDBHandler,
                                entity_id=unit["id"],
                                **common_args,
                            )

    for executor in executors:
        # It has no effect but raises exception from the threads if any
        executor.result()

    logger.debug(f"Summary of GCS link errors: {errors_by_handler_and_id}")
    return errors_by_handler_and_id


def get_gcs_columns_from_handler(handler) -> List[str]:
    return [
        column for column in handler.model.__table__.columns.keys() if "gcs" in column
    ]


def add_executors(
    handler,
    entity_id: int,
    client_id: int,
    gcloud_handler,
    errors_by_handler_and_id,
    executors,
    executor,
):
    for column in get_gcs_columns_from_handler(handler=handler):
        executors.append(
            executor.submit(
                check_handler_column,
                handler_class=handler,
                column_name=column,
                gcloud_handler=gcloud_handler,
                client_id=client_id,
                entity_id=entity_id,
                errors_by_handler_and_id=errors_by_handler_and_id,
            )
        )


def check_handler_column(
    handler_class,
    column_name: str,
    gcloud_handler,
    errors_by_handler_and_id,
    client_id: int,
    entity_id: int,
):
    from handlers.utils import get_client_bucket_name

    entity = handler_class.get_by(id=entity_id, output_columns=["id", column_name])
    if entity[column_name] is None:
        columns = []
    else:
        if isinstance(entity[column_name], dict):
            # Ifc files are a dictionary
            columns = list(entity[column_name].values())
        else:
            columns = [entity[column_name]]

    bucket_name = COLUMN_NAME_TO_BUCKET_MAPPING.get(
        column_name, get_client_bucket_name(client_id=client_id)
    )
    for column_value in columns:
        try:
            gcloud_handler.get_blob_check_exists(
                bucket_name=bucket_name,
                file_path=gcloud_handler._convert_media_link_to_file_in_gcp(
                    column_value
                ),
            )
        except GCSLinkEmptyException:
            logger.error(
                f"Broken gcs link in the DB for entity: {handler_class.__name__},"
                f" column: {column_name} and id: {entity_id} of client: {client_id}"
            )
            errors_by_handler_and_id[handler_class.__name__][column_name].append(
                entity_id
            )


def default_dict_wrapper():
    """
    function to avoid lambda expresion like errors_by_handler_and_id = defaultdict(lambda: defaultdict(list))
    lambda expressions are not pickle serializable
    """
    return defaultdict(list)
