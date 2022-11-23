from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.exceptions import BulkVolumeVolumeException
from handlers.db.bulk_volume_progress_handler import BulkVolumeProgressDBHandler
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def bulk_volume_volume_task(
    self, lk25_index: int, lk25_subindex_2: int, resolution: float, task_id: int
):
    from pathlib import Path
    from tempfile import TemporaryDirectory

    from common_utils.constants import VOLUME_BUCKET
    from handlers import GCloudStorageHandler
    from simulations.geometry.bulk_volume_volume import (
        BuildingVolumeHandler,
        GridHandler,
        store_as_tif,
    )
    from surroundings.utils import lk25_to_lv95_bounds

    errors = None
    state = ADMIN_SIM_STATUS.SUCCESS.value

    try:
        bounds = lk25_to_lv95_bounds(
            lk25_index=lk25_index, lk25_subindex=lk25_subindex_2
        )
        destination_folder = Path("bulk_volume_volumes_2021")

        grid_handler = GridHandler(bounds=bounds, resolution=resolution)
        building_volume_handler = BuildingVolumeHandler(grid_handler=grid_handler)
        gcloud_storage_handler = GCloudStorageHandler()

        with TemporaryDirectory() as tempdir:
            for subterranean, prefix in [(True, "sub"), (False, "super")]:
                output_filename = Path(tempdir).joinpath(
                    f"{prefix}_{lk25_index}_{lk25_subindex_2}.tif"
                )
                store_as_tif(
                    filename=output_filename,
                    transform=grid_handler.transform,
                    volumes_grid=building_volume_handler.get_volumes_grid(
                        subterranean=subterranean
                    ),
                )
                gcloud_storage_handler.upload_file_to_bucket(
                    bucket_name=VOLUME_BUCKET,
                    destination_folder=destination_folder,
                    local_file_path=output_filename,
                )
    except Exception as e:
        errors = {"msg": str(e), "code": type(e).__name__}
        state = ADMIN_SIM_STATUS.FAILURE.value
        raise BulkVolumeVolumeException from e

    finally:
        BulkVolumeProgressDBHandler.update(
            item_pks=dict(id=task_id),
            new_values=dict(
                lk25_index=lk25_index,
                lk25_subindex_2=lk25_subindex_2,
                state=state,
                errors=errors,
            ),
        )
