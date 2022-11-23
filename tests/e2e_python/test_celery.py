import json
import uuid
from datetime import datetime

import pytest
from shapely.geometry import box

from common_utils.constants import ADMIN_SIM_STATUS
from handlers.db import PotentialSimulationDBHandler
from tasks.potential_view_tasks import (
    get_potential_quavis_simulation_chain,
    store_quavis_results_potential_task,
)
from tasks.workflow_tasks import fake_error_handler, fake_task, workflow
from tests.celery_utils import (
    get_celery_metadata_from_flower_api,
    get_flower_all_tasks_metadata,
    wait_for_celery_tasks,
)
from tests.utils import get_redis


def test_potential_chain_failure(potential_db_simulation_ch_sun_empty):
    PotentialSimulationDBHandler.update(
        item_pks={"id": potential_db_simulation_ch_sun_empty["id"]},
        new_values={"building_footprint": box(0, 0, 0, 0)},
    )

    chain = get_potential_quavis_simulation_chain(
        simulation_id=potential_db_simulation_ch_sun_empty["id"]
    )

    chain.delay()
    wait_for_celery_tasks()

    potential_sim = PotentialSimulationDBHandler.get_by(
        id=potential_db_simulation_ch_sun_empty["id"]
    )
    assert potential_sim["status"] == ADMIN_SIM_STATUS.FAILURE.value
    assert potential_sim["result"] == {
        "msg": "Couldn't find any raster file intersecting with bounding box: "
        "(1397713.841086102, -4617343.61385932, 1398713.841086102, -4616343.61385932)",
        "code": "SurroundingException",
    }


def test_potential_tasks_routing(potential_db_simulation_ch_sun_empty):
    PotentialSimulationDBHandler.update(
        item_pks={"id": potential_db_simulation_ch_sun_empty["id"]},
        new_values={"building_footprint": box(0, 0, 0, 0)},
    )

    sim_start_time = datetime.now()
    store_quavis_results_potential_task.si(
        simulation_id=potential_db_simulation_ch_sun_empty["id"]
    ).delay()

    wait_for_celery_tasks(num_tasks_expected=1)
    #
    tasks = get_flower_all_tasks_metadata(after_time=int(sim_start_time.strftime("%s")))
    assert len(tasks) == 1
    assert (
        tasks[0]["name"]
        == "tasks.potential_view_tasks.store_quavis_results_potential_task"
    )
    assert tasks[0]["routing_key"] == "potential_store"


class TestWorkflow:
    def test_parallel_workflow_on_error_is_called_late(self):
        error_key = str(uuid.uuid4())
        long_running_chain = workflow(
            fake_task.si(message="chain1.task1", wait_for=1),
            fake_task.si(message="chain1.task2", wait_for=1),
            fake_task.si(message="chain1.task3", wait_for=1),
        )
        failing_task = fake_task.si(message="task4", raise_exception=True)
        dummy_workflow = workflow(
            long_running_chain,
            failing_task,
            run_in_parallel=True,
            on_error=fake_error_handler.s(redis_key=error_key),
        )

        result = dummy_workflow.delay()
        wait_for_celery_tasks(num_tasks_expected=5)

        long_running_chain_result, failing_task_result = result.parent
        long_running_chain_flower_metadata = get_celery_metadata_from_flower_api(
            task_id=long_running_chain_result.id
        )
        on_error_metadata = [
            json.loads(err) for err in get_redis().lrange(error_key, 0, -1)
        ]

        # Then
        # the on error callback is called once the long-running chain finished
        assert on_error_metadata == [
            {
                "message": f"Dependency {failing_task_result.id} raised Exception('task4')",
                "time": pytest.approx(
                    long_running_chain_flower_metadata["succeeded"], abs=0.01
                ),
            }
        ]

    def test_workflow_nested_on_error_callbacks(self):
        (
            task_error_key,
            chain_error_key,
            chord_error_key,
            outer_chain_error_key,
        ) = error_keys = list(map(str, [uuid.uuid4() for _ in range(4)]))
        dummy_workflow = workflow(
            workflow(
                workflow(
                    fake_task.si(message="chain1.task1", wait_for=2),
                    fake_task.si(message="chain1.task2", wait_for=1),
                ),
                workflow(
                    fake_task.si(message="group.chain.task1"),
                    fake_task.si(
                        message="group.chain.task2", wait_for=1, raise_exception=True
                    ).on_error(fake_error_handler.s(redis_key=task_error_key)),
                    on_error=fake_error_handler.s(redis_key=chain_error_key),
                ),
                on_error=fake_error_handler.s(redis_key=chord_error_key),
                run_in_parallel=True,
            ),
            fake_task.si(message="won't run"),
            on_error=fake_error_handler.s(redis_key=outer_chain_error_key),
        )

        result = dummy_workflow.delay()
        wait_for_celery_tasks(num_tasks_expected=5)

        redis_client = get_redis()

        # Then
        # all error callbacks were hit
        assert redis_client.exists(*error_keys) == len(error_keys)

        (
            long_running_chain_result,
            failed_task_result,
        ) = result.parent.parent.parent
        failed_task_flower_metadata, long_running_chain_flower_metadata = map(
            get_celery_metadata_from_flower_api,
            [failed_task_result.id, long_running_chain_result.id],
        )
        (
            task_error_metadata,
            chain_error_metadata,
            chord_error_metadata,
            outer_chain_error_metadata,
        ) = [
            [json.loads(err) for err in redis_client.lrange(name, 0, -1)]
            for name in error_keys
        ]

        # And
        # the task's and task's chain's error callbacks are called instantly following the exception
        for on_error_metadata in [task_error_metadata, chain_error_metadata]:
            assert on_error_metadata == [
                {
                    "message": "group.chain.task2",
                    "time": pytest.approx(
                        failed_task_flower_metadata["failed"], abs=0.1
                    ),
                }
            ]

        # And
        # the chord's and outer chain's error callbacks are called once the long-running chain finished
        for on_error_metadata in [chord_error_metadata, outer_chain_error_metadata]:
            assert on_error_metadata == [
                {
                    "message": f"Dependency {failed_task_result.id} raised Exception('group.chain.task2')",
                    "time": pytest.approx(
                        long_running_chain_flower_metadata["succeeded"], abs=0.1
                    ),
                },
            ]

    def test_chaining_parallel_workflows_success(self):
        error_key = str(uuid.uuid4())
        dummy_workflow = workflow(
            workflow(
                fake_task.si(message="group1.task1"),
                fake_task.si(message="group1.task2"),
                run_in_parallel=True,
            ),
            workflow(
                fake_task.si(message="group2.task1"),
                fake_task.si(message="group2.task2"),
                run_in_parallel=True,
            ),
            fake_task.si(message="some task"),
            on_error=fake_error_handler.s(redis_key=error_key),
        )

        result = dummy_workflow.delay()
        result.get()

        assert result.state == "SUCCESS"

    def test_chaining_parallel_workflows_on_error_first_chord_fails(self):
        error_key = str(uuid.uuid4())
        long_running_chain = workflow(
            fake_task.si(message="chain1.task1", wait_for=1),
            fake_task.si(message="chain1.task2", wait_for=1),
            fake_task.si(message="chain1.task3", wait_for=1),
        )
        dummy_workflow = workflow(
            workflow(
                long_running_chain,
                fake_task.si(message="group1.task2", raise_exception=True),
                run_in_parallel=True,
            ),
            workflow(
                fake_task.si(message="won't run"),
                fake_task.si(message="won't run"),
                run_in_parallel=True,
            ),
            on_error=fake_error_handler.s(redis_key=error_key),
        )

        result = dummy_workflow.delay()
        wait_for_celery_tasks(num_tasks_expected=5)

        (
            long_running_chain_result,
            failing_task_result,
        ) = result.parent.parent.parent.parent
        long_running_chain_flower_metadata = get_celery_metadata_from_flower_api(
            task_id=long_running_chain_result.id
        )
        on_error_metadata = [
            json.loads(err) for err in get_redis().lrange(error_key, 0, -1)
        ]

        # Then
        # the on error callback is called once the long-running chain finished
        assert on_error_metadata == [
            {
                "message": f"Dependency {failing_task_result.id} raised Exception('group1.task2')",
                "time": pytest.approx(
                    long_running_chain_flower_metadata["succeeded"], abs=0.01
                ),
            }
        ]

    def test_chaining_parallel_workflows_on_error_second_chord_fails(self):
        error_key = str(uuid.uuid4())
        long_running_chain = workflow(
            fake_task.si(message="chain1.task1", wait_for=1),
            fake_task.si(message="chain1.task2", wait_for=1),
            fake_task.si(message="chain1.task3", wait_for=1),
        )
        dummy_workflow = workflow(
            workflow(
                fake_task.si(message="group1.task1"),
                fake_task.si(message="group1.task2"),
                run_in_parallel=True,
            ),
            workflow(
                long_running_chain,
                fake_task.si(message="group2.task2", raise_exception=True),
                run_in_parallel=True,
            ),
            on_error=fake_error_handler.s(redis_key=error_key),
        )

        result = dummy_workflow.delay()
        wait_for_celery_tasks(num_tasks_expected=9)

        long_running_chain_result, failing_task_result = result.parent
        long_running_chain_flower_metadata = get_celery_metadata_from_flower_api(
            task_id=long_running_chain_result.id
        )
        on_error_metadata = [
            json.loads(err) for err in get_redis().lrange(error_key, 0, -1)
        ]

        # Then
        # the on error callback is called once the long-running chain finished
        assert on_error_metadata == [
            {
                "message": f"Dependency {failing_task_result.id} raised Exception('group2.task2')",
                "time": pytest.approx(
                    long_running_chain_flower_metadata["succeeded"], abs=0.01
                ),
            }
        ]
