from tasks.utils.utils import celery_retry_task


@celery_retry_task
def copy_site_task(
    self,
    target_client_id: int,
    site_id_to_copy: int,
    copy_area_types: bool,
    target_existing_site_id: int | None = None,
):
    from handlers.copy_site import CopySite

    new_site_id = CopySite().copy_site(
        target_client_id=target_client_id,
        site_id_to_copy=site_id_to_copy,
        copy_area_types=copy_area_types,
        target_existing_site_id=target_existing_site_id,
    )
    return new_site_id
