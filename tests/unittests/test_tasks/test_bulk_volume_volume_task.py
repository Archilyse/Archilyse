from pathlib import Path

import numpy as np
import pytest
import rasterio

from common_utils.constants import ADMIN_SIM_STATUS, VOLUME_BUCKET
from common_utils.exceptions import BulkVolumeVolumeException
from tasks.bulk_volume_volume_computation import bulk_volume_volume_task


def test_bulk_volume_volume_task_reports_errors(
    mocker, mocked_gcp_upload_file_to_bucket
):
    import surroundings.utils
    from handlers.db import BulkVolumeProgressDBHandler

    mocked_progress_report = mocker.patch.object(BulkVolumeProgressDBHandler, "update")
    mocker.patch.object(
        surroundings.utils,
        "lk25_to_lv95_bounds",
        side_effect=Exception("Got a problem"),
    )

    fake_task_id = -999
    lk25_index = 1091
    lk25_subindex_2 = 41

    with pytest.raises(BulkVolumeVolumeException):
        bulk_volume_volume_task(
            lk25_index=lk25_index,
            lk25_subindex_2=lk25_subindex_2,
            resolution=0.5,
            task_id=fake_task_id,
        )

    mocked_progress_report.assert_called_once_with(
        item_pks=dict(id=fake_task_id),
        new_values=dict(
            lk25_index=lk25_index,
            lk25_subindex_2=lk25_subindex_2,
            state=ADMIN_SIM_STATUS.FAILURE.value,
            errors={"code": "Exception", "msg": "Got a problem"},
        ),
    )


def test_bulk_volume_volume_task(mocker, mocked_gcp_upload_file_to_bucket):
    import tempfile

    import simulations.geometry.bulk_volume_volume
    import surroundings.utils
    from handlers.db import BulkVolumeProgressDBHandler

    fake_task_id = -999
    lk25_index = 1091
    lk25_subindex_2 = 41
    bounds = (0.0, 0.0, 1.0, 1.0)
    resolution = 0.5

    mocked_progress_report = mocker.patch.object(BulkVolumeProgressDBHandler, "update")
    mocked_get_volumes_grid = mocker.patch.object(
        simulations.geometry.bulk_volume_volume.BuildingVolumeHandler,
        "get_volumes_grid",
        return_value=np.array([[0.0, 0.125], [0.125, 0.125]]),
    )
    mocked_lk25_to_lv95_bounds = mocker.patch.object(
        surroundings.utils, "lk25_to_lv95_bounds", return_value=bounds
    )
    spy_grid_handler = mocker.spy(
        simulations.geometry.bulk_volume_volume, "GridHandler"
    )

    with tempfile.TemporaryDirectory() as tempdir:
        mocker.patch.object(
            tempfile, "TemporaryDirectory"
        ).return_value.__enter__.return_value = tempdir

        bulk_volume_volume_task(
            lk25_index=lk25_index,
            lk25_subindex_2=lk25_subindex_2,
            resolution=resolution,
            task_id=fake_task_id,
        )
        output_filenames = [
            Path(tempdir).joinpath("sub_1091_41.tif"),
            Path(tempdir).joinpath("super_1091_41.tif"),
        ]

        for output_filename in output_filenames:
            with rasterio.open(output_filename) as dataset:
                grid_values = dataset.read(1)

            assert dataset.transform == spy_grid_handler.spy_return.transform
            assert grid_values.tolist() == [[0.0, 0.125], [0.125, 0.125]]
            assert grid_values.shape == (
                spy_grid_handler.spy_return.height,
                spy_grid_handler.spy_return.width,
            )

    spy_grid_handler.assert_called_once_with(bounds=bounds, resolution=resolution)
    assert mocked_get_volumes_grid.call_args_list == [
        mocker.call(subterranean=True),
        mocker.call(subterranean=False),
    ]
    mocked_lk25_to_lv95_bounds.assert_called_once_with(
        lk25_index=lk25_index, lk25_subindex=lk25_subindex_2
    )
    assert mocked_gcp_upload_file_to_bucket.call_args_list == [
        mocker.call(
            bucket_name=VOLUME_BUCKET,
            destination_folder=Path("bulk_volume_volumes_2021"),
            local_file_path=output_filename,
        )
        for output_filename in output_filenames
    ]
    mocked_progress_report.assert_called_once_with(
        item_pks=dict(id=fake_task_id),
        new_values=dict(
            lk25_index=lk25_index,
            lk25_subindex_2=lk25_subindex_2,
            state=ADMIN_SIM_STATUS.SUCCESS.value,
            errors=None,
        ),
    )
