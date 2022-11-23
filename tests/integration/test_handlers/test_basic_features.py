from brooks.types import AreaType
from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from common_utils.exceptions import BasicFeaturesException
from handlers import SlamSimulationHandler
from handlers.db import AreaDBHandler
from tasks.basic_features import BasicFeatureTask
from tasks.workflow_tasks import WorkflowGenerator


def test_basic_features_errors(
    site_w_qa_data,
    plan,
    unit,
    annotations_box_data,
    celery_eager,
    basic_features_run_id,
    prepare_plans_for_basic_features_or_qa,
):
    prepare_plans_for_basic_features_or_qa(
        plan_id=plan["id"], annotations_data=annotations_box_data
    )
    area_ids = list(AreaDBHandler.find_ids(plan_id=plan["id"]))

    # HACK: as the error handler is not called
    # with celery eager we catch the error and call it ourself
    try:
        WorkflowGenerator(
            site_id=site_w_qa_data["id"]
        ).get_basic_features_task_chain().delay()
    except BasicFeaturesException as e:
        BasicFeatureTask().on_failure(
            exc=e,
            task_id="",
            args=None,
            kwargs={"run_id": basic_features_run_id},
            einfo=None,
        )

    simulation = SlamSimulationHandler.get_simulation(
        site_id=site_w_qa_data["id"], task_type=TASK_TYPE.BASIC_FEATURES
    )
    assert simulation["errors"] == {
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
    assert simulation["state"] == ADMIN_SIM_STATUS.FAILURE.value


def test_basic_features_all_ok(
    site,
    plan_georeferenced,
    annotations_box_data,
    celery_eager,
    prepare_plans_for_basic_features_or_qa,
):
    prepare_plans_for_basic_features_or_qa(
        plan_id=plan_georeferenced["id"],
        annotations_data=annotations_box_data,
        area_type=AreaType.ROOM,
    )

    WorkflowGenerator(site_id=site["id"]).get_basic_features_task_chain().delay()

    simulation = SlamSimulationHandler.get_simulation(
        site_id=site["id"], task_type=TASK_TYPE.BASIC_FEATURES
    )
    assert simulation["errors"] is None
    assert simulation["state"] == ADMIN_SIM_STATUS.SUCCESS.value
