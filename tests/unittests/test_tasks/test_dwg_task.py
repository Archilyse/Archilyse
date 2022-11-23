import pytest
from celery import Task
from cloudconvert.exceptions.exceptions import ClientError, ServerError
from requests import Response

from handlers import DMSFloorDeliverableHandler
from tasks.deliverables_tasks import generate_dwg_floor_task


@pytest.mark.parametrize(
    "exception_class, status_code, should_retry",
    [
        (ClientError, 429, True),
        (ClientError, 428, False),
        (ServerError, None, True),
        (Exception, None, False),
    ],
)
def test_generate_dwg_floor_task_retry_too_many_requests(
    mocker, exception_class, status_code, should_retry
):
    response = Response()
    response.status_code = status_code
    if exception_class == Exception:
        side_effect = [Exception("random exception")]
    else:
        side_effect = [exception_class(response=response)]

    mocker.patch.object(
        DMSFloorDeliverableHandler,
        "convert_and_upload_dwg",
        side_effect=side_effect,
    )
    spy = mocker.spy(Task, "retry")
    with pytest.raises(exception_class):
        generate_dwg_floor_task(floor_id=1)

    if should_retry:
        spy.assert_called_once()
