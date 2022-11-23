from tasks.utils.utils import celery_retry_task


@celery_retry_task
def run_quavis_task(self, run_id: str):
    from handlers.quavis import QuavisGCPHandler
    from simulations.view import ViewWrapper

    quavis_input = QuavisGCPHandler.get_quavis_input(run_id=run_id)

    quavis_output = ViewWrapper.execute_quavis(quavis_input=quavis_input)

    QuavisGCPHandler.upload_quavis_output(run_id=run_id, quavis_output=quavis_output)
    return run_id
