import os
from distutils.util import strtobool

rabbit_mq_user = os.environ.get("RABBITMQ_USER")
rabbit_mq_password = os.environ.get("RABBITMQ_PASSWORD")
rabbit_mq_host = os.environ.get("RABBITMQ_HOST")
rabbit_mq_vhost = os.environ.get("RABBITMQ_VIRTUAL_HOST")
rabbit_mq_port = os.environ.get("RABBITMQ_PORT")
rabbit_mq_management_port = os.environ.get("RABBITMQ_MANAGEMENT_PORT")

broker_url = (
    f"pyamqp://{rabbit_mq_user}:{rabbit_mq_password}@{rabbit_mq_host}:"
    f"{rabbit_mq_port}{rabbit_mq_vhost}"
)

if strtobool(os.environ.get("RABBITMQ_SSL_ACTIVE", "True")):
    broker_url += "?ssl=true"

event_queue_expires = 60
broker_heartbeat = None
broker_connection_timeout = 30
accept_content = ["json"]
enable_utc = True
timezone = "UTC"
database_short_lived_sessions = True


redis_max_connections = int(os.environ.get("REDIS_MAX_CONNECTIONS", 65000))
redis_backend_health_check_interval = int(
    os.environ.get("REDIS_BACKEND_HEALTH_CHECK_INTERVAL", 30)
)
redis_conn_config = {
    "host": os.environ["REDIS_HOST"],
    "port": int(os.environ["REDIS_PORT"]),
    "db": int(os.environ.get("REDIS_DB", 0)),
    "password": os.environ["REDIS_PASSWORD"],
}
result_backend = f"redis://:{redis_conn_config['password']}@{redis_conn_config['host']}:{redis_conn_config['port']}/{redis_conn_config['db']}"

result_serializer = "json"
result_expires = 86400 * 5  # 5 days in seconds

worker_prefetch_multiplier = 1
worker_concurrency = int(os.environ.get("WORKER_CONCURRENCY", 1))
worker_max_tasks_per_child = 1
worker_send_task_events = True
worker_redirect_stdouts = False
worker_cancel_long_running_tasks_on_connection_loss = True  # Important change in celery 5.x that is causing problems with duplicated tasks if False

task_send_sent_event = True
task_ignore_result = False
task_serializer = "json"
task_acks_late = strtobool(os.environ.get("CELERY_ACKS_LATE", "True"))
task_always_eager = strtobool(os.environ.get("CELERY_EAGER", "False"))
task_eager_propagates = True  # if eager == True then this applies
task_track_started = True
task_time_limit = 86400 * 2  # 48 hours in seconds
task_inherit_parent_priority = True
task_default_priority = 1  # RabbitMQ's priority works from 1 to 255, being 1 the lowest
task_queue_max_priority = 10  # Creates queues with priorities by default.
task_reject_on_worker_lost = True
# Too many priorities affects RabbitMQ performance.

result_chord_retry_interval = float(
    os.environ.get("CELERY_RETRY_INTERVAL", 60.0)
)  # production default, override for local tests

INCREASED_TASK_PRIORITY = task_default_priority + 1

include = [
    "tasks.basic_features",
    "tasks.connectivity_tasks",
    "tasks.noise_tasks",
    "tasks.check_gcs_links_task",
    "tasks.competition_features_tasks",
    "tasks.deliverables_tasks",
    "tasks.bulk_volume_volume_computation",
    "tasks.mail_tasks",
    "tasks.pipeline_tasks",
    "tasks.potential_view_tasks",
    "tasks.post_simulations_validations",
    "tasks.quavis_tasks",
    "tasks.simulations_tasks",
    "tasks.clustering_units_tasks",
    "tasks.site_ifc_tasks",
    "tasks.surroundings_tasks",
    "tasks.surroundings_nightly_tasks",
    "tasks.workflow_tasks",
    "tasks.annotations_migration_tasks",
    "tasks.rectangulator_tasks",
    "tasks.dev_helper_tasks",
    "tasks.qa_validation_tasks",
    "tasks.dms_tasks",
]

# At the moment, production is working with the following config:
# 2 workers dedicated to queues: basic_features_w_p,workflow_w_p,deliverables_w_p
# 7 workers dedicated to queues: potential_w_p,simulations_w_p,surroundings_w_p
# 1 worker dedicated to queues: potential_store,potential_w_p


#  https://docs.celeryproject.org/en/stable/userguide/routing.html#routers
task_routes = (
    [
        ("tasks.basic_features.*", dict(queue="basic_features_w_p")),
        ("tasks.pipeline_tasks.*", dict(queue="basic_features_w_p")),
        ("tasks.site_ifc_tasks.*", dict(queue="basic_features_w_p")),
        ("tasks.qa_validation_tasks.*", dict(queue="basic_features_w_p")),
        ("tasks.deliverables_tasks.*", dict(queue="deliverables_w_p")),
        ("tasks.check_gcs_links_task.*", dict(queue="workflow_w_p")),
        (
            "tasks.potential_view_tasks.store_quavis_results_potential_task",
            dict(queue="potential_store", priority=INCREASED_TASK_PRIORITY),
        ),
        ("tasks.potential_view_tasks.*", dict(queue="potential_w_p")),
        ("tasks.quavis_tasks.*", dict(queue="quavis_w_p")),
        ("tasks.connectivity_tasks.*", dict(queue="simulations_w_p")),
        ("tasks.noise_tasks.*", dict(queue="simulations_w_p")),
        ("tasks.dms_tasks.*", dict(queue="simulations_w_p")),
        ("tasks.competition_features_tasks.*", dict(queue="basic_features_w_p")),
        (
            "tasks.simulations_tasks.*",
            dict(queue="simulations_w_p", priority=INCREASED_TASK_PRIORITY),
        ),
        ("tasks.bulk_volume_volume_computation.*", dict(queue="potential_w_p")),
        ("tasks.clustering_units_tasks.*", dict(queue="simulations_w_p")),
        ("tasks.surroundings_tasks.*", dict(queue="surroundings_w_p")),
        ("tasks.surroundings_nightly_tasks.*", dict(queue="surroundings_w_p")),
        ("tasks.post_simulations_validations.*", dict(queue="simulations_w_p")),
        ("tasks.workflow_tasks.*", dict(queue="workflow_w_p")),
        ("tasks.mail_tasks.*", dict(queue="workflow_w_p")),
        ("tasks.annotations_migration_tasks.*", dict(queue="simulations_w_p")),
        ("tasks.rectangulator_tasks.*", dict(queue="simulations_w_p")),
        (
            "celery.*",
            dict(queue="workflow_w_p"),
        ),  # Tasks executed by celery, like chords checks, etc
        ("tasks.dev_helper_tasks.*", dict(queue="workflow_w_p")),
    ],
)
