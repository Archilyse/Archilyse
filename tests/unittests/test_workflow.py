import pytest
from celery.canvas import Signature, _chain, chain, chord

from tasks.workflow_tasks import empty_task, fake_error_handler, fake_task, workflow

dummy_task = fake_task.si(message="task1")
dummy_workflow = workflow(
    fake_task.si(message="task1"),
    fake_task.si(message="task2"),
)
dummy_parallel_workflow = workflow(
    fake_task.si(message="task1"),
    fake_task.si(message="task2"),
    run_in_parallel=True,
)


def test_workflow_returns_chain():
    canvas = workflow(
        fake_task.si(message="task1"),
        fake_task.si(message="task2"),
    )
    assert isinstance(canvas, _chain)
    assert canvas.tasks == (
        fake_task.si(message="task1"),
        fake_task.si(message="task2"),
    )


def test_workflow_returns_signature():
    canvas = workflow(
        fake_task.si(message="task1"),
    )
    assert isinstance(canvas, Signature)
    assert canvas == fake_task.si(message="task1")


def test_parallel_workflow_returns_chord():
    canvas = workflow(
        fake_task.si(message="task1"),
        fake_task.si(message="task2"),
        run_in_parallel=True,
    )
    assert isinstance(canvas, chord)
    assert canvas.body == empty_task.s()
    assert canvas.tasks == (
        fake_task.si(message="task1"),
        fake_task.si(message="task2"),
    )


def test_parallel_workflow_on_error_is_added_to_the_chords_body():
    canvas = workflow(
        fake_task.si(message="task1"),
        fake_task.si(message="task2"),
        run_in_parallel=True,
        on_error=fake_error_handler.s(redis_key="some fake"),
    )
    assert canvas.body == empty_task.s().on_error(
        fake_error_handler.s(redis_key="some fake")
    )


def test_workflow_on_error_is_added_to_the_chain():
    canvas = workflow(
        fake_task.si(message="task1"),
        fake_task.si(message="task2"),
        on_error=fake_error_handler.s(redis_key="some fake"),
    )
    assert canvas == (
        fake_task.si(message="task1") | fake_task.si(message="task2")
    ).on_error(fake_error_handler.s(redis_key="some fake"))


def test_workflow_nested_on_error_callbacks():
    canvas = workflow(
        workflow(
            fake_task.si(message="task1"),
            on_error=fake_error_handler.s(redis_key="task1"),
        ),
        workflow(
            workflow(
                fake_task.si(message="task2"),
                fake_task.si(message="task3"),
                on_error=fake_error_handler.s(redis_key="nested_chain1"),
            ),
            workflow(
                fake_task.si(message="task4"),
                fake_task.si(message="task5"),
                on_error=fake_error_handler.s(redis_key="nested_chain2"),
            ),
            on_error=fake_error_handler.s(redis_key="nested_chain3"),
        ),
    )
    assert canvas == chain(
        fake_task.si(message="task1").on_error(fake_error_handler.s(redis_key="task1")),
        fake_task.si(message="task2")
        .on_error(fake_error_handler.s(redis_key="nested_chain1"))
        .on_error(fake_error_handler.s(redis_key="nested_chain3")),
        fake_task.si(message="task3")
        .on_error(fake_error_handler.s(redis_key="nested_chain1"))
        .on_error(fake_error_handler.s(redis_key="nested_chain3")),
        fake_task.si(message="task4")
        .on_error(fake_error_handler.s(redis_key="nested_chain2"))
        .on_error(fake_error_handler.s(redis_key="nested_chain3")),
        fake_task.si(message="task5")
        .on_error(fake_error_handler.s(redis_key="nested_chain2"))
        .on_error(fake_error_handler.s(redis_key="nested_chain3")),
    )


def test_parallel_workflow_on_error_is_added_to_the_signature():
    canvas = workflow(
        fake_task.si(message="task1"),
        on_error=fake_error_handler.s(redis_key="some fake"),
    )
    assert canvas == fake_task.si(message="task1").on_error(
        fake_error_handler.s(redis_key="some fake")
    )


@pytest.mark.parametrize(
    "canvas_to_append",
    [
        dummy_task,
        dummy_workflow,
        dummy_parallel_workflow,
    ],
)
def test_chaining_parallel_workflow_adds_connector_task(canvas_to_append):
    canvas = workflow(
        dummy_parallel_workflow,
        canvas_to_append,
    )
    assert canvas == (
        dummy_parallel_workflow
        # This is the "connector" task
        | chain(
            empty_task.s(),
        )
        | canvas_to_append
    )


@pytest.mark.parametrize(
    "canvas_to_append",
    [
        dummy_task,
        dummy_workflow,
        dummy_parallel_workflow,
    ],
)
def test_chaining_parallel_workflow_does_not_chain_to_the_chords_body(canvas_to_append):
    canvas = workflow(
        dummy_parallel_workflow,
        canvas_to_append,
    )
    # NOTE:
    # Without the connector task we would chain
    # the canvas to the chord's body.
    assert canvas.tasks[0].body == empty_task.s()


@pytest.mark.parametrize(
    "canvas_to_append, number_of_tasks_to_add",
    [
        (dummy_task, 1),
        (dummy_workflow, 2),
        (dummy_parallel_workflow, 1),
    ],
)
def test_chaining_parallel_workflow_expected_number_of_tasks(
    canvas_to_append, number_of_tasks_to_add
):
    canvas = workflow(
        dummy_parallel_workflow,
        canvas_to_append,
    )
    assert isinstance(canvas, _chain)
    assert len(canvas.tasks) == 1 + 1 + number_of_tasks_to_add


def test_workflow_raises_on_nested_parallelism():
    with pytest.raises(Exception, match="No nested parallelism please!"):
        workflow(dummy_parallel_workflow, dummy_task, run_in_parallel=True)
