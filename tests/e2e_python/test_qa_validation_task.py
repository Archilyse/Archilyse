from common_utils.constants import ADMIN_SIM_STATUS
from handlers.db import AreaDBHandler, SiteDBHandler, SlamSimulationDBHandler
from tasks.workflow_tasks import WorkflowGenerator
from tests.celery_utils import wait_for_celery_tasks


def test_qa_validation_task_chain_basic_features_failure(
    site_w_qa_data,
    plan,
    unit,
    annotations_box_data,
    basic_features_run_id,
    prepare_plans_for_basic_features_or_qa,
):
    prepare_plans_for_basic_features_or_qa(
        plan_id=plan["id"], annotations_data=annotations_box_data
    )
    area_ids = list(AreaDBHandler.find_ids(plan_id=plan["id"]))

    chain = WorkflowGenerator(site_id=site_w_qa_data["id"]).get_qa_validation_chain()
    chain.delay()

    wait_for_celery_tasks(wait_for_subtasks=True, num_tasks_expected=4)

    expected_validation_errors = {
        "errors": [
            {
                "type": "AREA_NOT_DEFINED",
                "position": {"type": "Point", "coordinates": [598.35, 544.39]},
                "object_id": area_ids[0],
                "text": "An area is NOT_DEFINED",
                "human_id": f'Plan id: {plan["id"]}, apartment_no: {unit["apartment_no"]}',
                "is_blocking": 1,
            }
        ]
    }

    site = SiteDBHandler.get_by(id=site_w_qa_data["id"])
    assert site["basic_features_status"] == ADMIN_SIM_STATUS.FAILURE.name
    assert site["basic_features_error"] == expected_validation_errors
    assert site["qa_validation"] is None

    simulation = SlamSimulationDBHandler.get_by(run_id=basic_features_run_id)
    assert simulation["errors"] == expected_validation_errors
    assert simulation["state"] == ADMIN_SIM_STATUS.FAILURE.value
