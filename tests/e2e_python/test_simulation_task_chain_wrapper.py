import pytest

from common_utils.constants import ADMIN_SIM_STATUS, TASK_TYPE
from common_utils.exceptions import DBNotFoundException
from handlers.db import SlamSimulationDBHandler
from tasks.simulations_tasks import simulation_success
from tasks.workflow_tasks import WorkflowGenerator
from tests.celery_utils import wait_for_celery_tasks


def test_simulation_task_chain_wrapper_on_error(site):
    run_id = "my-run-id"

    result = (
        WorkflowGenerator(site_id=site["id"])
        .get_simulation_task_chain_wrapper(
            # HACK: this is just a random task which is already registered at runtime
            # and can throw an exception ...
            simulation_success.si(run_id="this run_id does not exist"),
            run_id=run_id,
            task_type=TASK_TYPE.VIEW_SUN,
        )
        .delay()
    )
    wait_for_celery_tasks()
    with pytest.raises(DBNotFoundException):
        result.wait()

    simulation = SlamSimulationDBHandler.get_by(run_id=run_id)
    assert simulation["state"] == ADMIN_SIM_STATUS.FAILURE.name
    assert simulation["errors"] == {
        "code": "DBNotFoundException",
        "msg": "Item for table SlamSimulationDBModel does not exist for pk: "
        "{'run_id': 'this run_id does not exist'}",
    }
