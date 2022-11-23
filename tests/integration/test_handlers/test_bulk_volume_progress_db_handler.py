import pytest
from deepdiff import DeepDiff

from common_utils.constants import ADMIN_SIM_STATUS
from handlers.db import BulkVolumeProgressDBHandler


class TestBulkVolumeProgressDBHandler:
    @pytest.mark.parametrize(
        "progress",
        [
            dict(
                lk25_index=1091,
                lk25_subindex_2=33,
                state=ADMIN_SIM_STATUS.FAILURE.value,
                errors={"code": "Exception", "msg": "Got a problem"},
            ),
            dict(
                lk25_index=1091,
                lk25_subindex_2=33,
                state=ADMIN_SIM_STATUS.SUCCESS.value,
                errors=None,
            ),
        ],
    )
    def test_add(self, progress):
        result = BulkVolumeProgressDBHandler.add(**progress)
        assert result == BulkVolumeProgressDBHandler.get_by(id=result["id"])
        assert not DeepDiff(
            result,
            progress,
            exclude_paths=["root['created']", "root['id']", "root['updated']"],
        )

    @pytest.mark.parametrize(
        "progress",
        [
            dict(
                lk25_index=1091,
                lk25_subindex_2=33,
                state=ADMIN_SIM_STATUS.FAILURE.value,
                errors={"code": "Exception", "msg": "Got a problem"},
            ),
            dict(
                lk25_index=1091,
                lk25_subindex_2=33,
                state=ADMIN_SIM_STATUS.SUCCESS.value,
                errors=None,
            ),
        ],
    )
    def test_update(self, progress):
        task_info = BulkVolumeProgressDBHandler.add(
            lk25_index=1091,
            lk25_subindex_2=33,
            state=ADMIN_SIM_STATUS.PENDING.value,
        )
        result = BulkVolumeProgressDBHandler.update(
            item_pks=dict(id=task_info["id"]), new_values=progress
        )
        assert result == BulkVolumeProgressDBHandler.get_by(id=result["id"])
        assert result == {**result, **progress}
