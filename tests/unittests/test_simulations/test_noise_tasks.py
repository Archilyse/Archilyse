import pytest

from common_utils.constants import REGION
from handlers.db import ClientDBHandler, SiteDBHandler
from tasks.workflow_tasks import WorkflowGenerator


@pytest.mark.parametrize(
    "region, num_tasks_expected",
    [(REGION.CH.name, 6), (REGION.DE_HAMBURG.name, 6), (REGION.US_GEORGIA.name, 6)],
)
def test_noise_tasks_in_non_supported_region(
    mocker, celery_eager, region, num_tasks_expected
):
    mocker.patch.object(
        ClientDBHandler,
        "get_by_site_id",
        return_value={"option_analysis": True},
    )
    mocker.patch.object(
        SiteDBHandler,
        SiteDBHandler.get_by.__name__,
        return_value={"georef_region": region},
    )

    tasks = WorkflowGenerator(site_id=1).get_noise_chain()
    assert len(tasks) == num_tasks_expected
