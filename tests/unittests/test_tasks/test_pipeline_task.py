import pytest

from handlers import AreaHandler
from handlers.db import ReactPlannerProjectsDBHandler
from handlers.plan_utils import create_areas_for_plan


@pytest.mark.parametrize(
    "exists",
    [False, True],
)
def test_create_areas_for_plan(mocker, exists):
    mocker.patch.object(ReactPlannerProjectsDBHandler, "exists", return_value=exists)
    mocked_area_upsert = mocker.patch.object(AreaHandler, "recover_and_upsert_areas")
    create_areas_for_plan(plan_id=1)
    assert mocked_area_upsert.called is exists
