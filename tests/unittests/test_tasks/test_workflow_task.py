from common_utils.constants import REGION
from handlers.db import ClientDBHandler, PlanDBHandler, SiteDBHandler, UnitDBHandler
from tasks import workflow_tasks


def test_workflow_get_unit_png_and_pdf_tasks(mocker):
    mocker.patch.object(
        ClientDBHandler,
        "get_by_site_id",
        return_value={"option_analysis": True},
    )
    mocker.patch.object(
        SiteDBHandler,
        "get_by",
        return_value={"georef_region": REGION.CH.name},
    )

    mocker.patch.object(
        PlanDBHandler,
        "find",
        return_value=[{"id": 1}, {"id": 2}],
    )
    mocker.patch.object(
        UnitDBHandler,
        "find_ids",
        return_value=[1, 2, 3, 4],
    )
    tasks = workflow_tasks.WorkflowGenerator(site_id=1).get_unit_png_and_pdf_tasks()
    assert len(tasks) == 4
    assert {task.kwargs["unit_id"] for task in tasks} == {1, 2, 3, 4}
