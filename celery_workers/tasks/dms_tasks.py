from handlers import FileHandler
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def cleanup_trash(self):
    FileHandler.cleanup_trash()
