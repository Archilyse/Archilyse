import pytest

from brooks.types import AreaType
from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from handlers.db import SiteDBHandler, SlamSimulationDBHandler
from tasks.workflow_tasks import WorkflowGenerator


@pytest.mark.parametrize(
    "given_site_status",
    [
        dict(
            basic_features_status=ADMIN_SIM_STATUS.SUCCESS.value,
            basic_features_error=dict(all="good"),
            qa_validation=dict(all="good"),
            pipeline_and_qa_complete=True,
        ),
        dict(
            basic_features_status=ADMIN_SIM_STATUS.UNPROCESSED.value,
            basic_features_error=None,
            qa_validation=None,
            pipeline_and_qa_complete=False,
        ),
    ],
)
def test_qa_validation_task(
    site,
    plan_georeferenced,
    unit,
    annotations_box_data,
    celery_eager,
    qa_db,
    prepare_plans_for_basic_features_or_qa,
    given_site_status,
    basic_features_run_id,
):
    prepare_plans_for_basic_features_or_qa(
        plan_id=plan_georeferenced["id"],
        annotations_data=annotations_box_data,
        area_type=AreaType.ROOM,
    )

    SiteDBHandler.update(item_pks=dict(id=site["id"]), new_values=given_site_status)

    WorkflowGenerator(site_id=site["id"]).get_qa_validation_chain().delay()

    site = SiteDBHandler.get_by(id=site["id"])
    assert site["basic_features_status"] == ADMIN_SIM_STATUS.SUCCESS.name
    assert site["basic_features_error"] is None
    assert site["qa_validation"] == {
        unit["client_id"]: [
            "Kitchen missing",
            "Bathrooms missing",
            "Rooms mismatch. Should have 4.5 rooms and it has 1.0 rooms",
            "Net area mismatch. Should have 94.0 m2 and it has 0.1 m2. Scale deviation factor: 871.81. ",
        ],
        "site_warnings": [
            "plan 1: Space with not enough windows that has been classified as ['ROOM']"
        ],
    }

    assert SlamSimulationDBHandler.exists(
        run_id=basic_features_run_id,
        state=ADMIN_SIM_STATUS.SUCCESS.name,
        type=TASK_TYPE.BASIC_FEATURES.name,
    )
