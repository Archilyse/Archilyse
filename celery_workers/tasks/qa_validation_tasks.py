from common_utils.constants import ADMIN_SIM_STATUS
from tasks.utils.utils import celery_retry_task, format_basic_feature_errors
from workers_config.celery_app import celery_app


@celery_retry_task
def qa_validation_task_processing(self, site_id: int):
    """Changes the status of the sites at the end of the chain"""
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(
            qa_validation=None,
            basic_features_error=None,
            basic_features_status=ADMIN_SIM_STATUS.PROCESSING.value,
        ),
    )


@celery_app.task
def qa_validation_task_failure(request, exc, traceback, site_id: int):
    """Changes the status of the sites at the end of the chain"""
    from handlers.db import SiteDBHandler

    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(
            basic_features_error=format_basic_feature_errors(exc=exc),
            basic_features_status=ADMIN_SIM_STATUS.FAILURE.value,
        ),
    )


@celery_retry_task
def run_qa_validation_task(self, site_id: int):
    from handlers import QAHandler
    from handlers.db import SiteDBHandler

    qa_validation = QAHandler(site_id=site_id).qa_validation()
    SiteDBHandler.update(
        item_pks=dict(id=site_id),
        new_values=dict(
            qa_validation=qa_validation,
            basic_features_status=ADMIN_SIM_STATUS.SUCCESS.name,
        ),
    )
