from common_utils.exceptions import DBNotFoundException
from common_utils.logger import logger
from handlers.editor_v2.schema import CURRENT_REACT_ANNOTATION_VERSION
from tasks.utils.utils import celery_retry_task


@celery_retry_task()
def migrate_all_react_annotations(self):
    from handlers.db import ReactPlannerProjectsDBHandler

    for project in ReactPlannerProjectsDBHandler.find_iter(
        output_columns=["id", "data"]
    ):
        if project["data"]["version"] != CURRENT_REACT_ANNOTATION_VERSION:
            migrate_react_annotations.delay(project_id=project["id"])


@celery_retry_task()
def migrate_react_annotations(self, project_id: int):
    from handlers.db import ReactPlannerProjectsDBHandler
    from handlers.editor_v2 import ReactPlannerHandler
    from handlers.editor_v2.schema import ReactPlannerSchema

    try:
        project = ReactPlannerProjectsDBHandler.get_by(id=project_id)
    except DBNotFoundException:
        # if the plan has been removed since the task was launched this raises an exception
        return None
    if project["data"]["version"] != CURRENT_REACT_ANNOTATION_VERSION:
        logger.info(f"migrating plan {project['plan_id']}")
        migrated_data = ReactPlannerHandler.migrate_data_if_old_version(project["data"])
        ReactPlannerSchema().load(migrated_data)
        ReactPlannerProjectsDBHandler.update(
            item_pks={"id": project["id"]}, new_values={"data": migrated_data}
        )
        logger.info(f"migrated plan {project['plan_id']}")
    else:
        logger.info(
            f"plan {project['plan_id']} is already on the last react annotation version"
        )
