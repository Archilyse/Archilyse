from celery.schedules import crontab

from tasks.check_gcs_links_task import check_dead_gcs_links_task
from tasks.dms_tasks import cleanup_trash
from tasks.surroundings_nightly_tasks import (
    run_potential_surrounding_quality,
    run_slam_quality,
)
from workers_config.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "surroundings_nightly_execution": {
        "task": run_potential_surrounding_quality.name,
        "schedule": crontab(hour=3, minute=0),  # Nightly at 3 UTC
    },
    "slam_nightly_execution": {
        "task": run_slam_quality.name,
        "schedule": crontab(hour=0, minute=0),  # Nightly at 0 UTC
    },
    "cleanup_dms_trash": {
        "task": cleanup_trash.name,
        "schedule": crontab(hour=22, minute=0),
    },
    "check_for_dead_gcs_links": {
        "task": check_dead_gcs_links_task.name,
        "schedule": crontab(hour=22, minute=0, day_of_week="sat"),
    },
}
