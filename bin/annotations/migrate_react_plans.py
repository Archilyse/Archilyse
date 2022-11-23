from typing import Dict

from common_utils.logger import logger
from handlers.db import ReactPlannerProjectsDBHandler
from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import ReactPlannerData

if __name__ == "__main__":

    def migration_callable(project: Dict):
        logger.info(f"migrating plan {project['plan_id']}")
        migrated_data = ReactPlannerHandler.migrate_data_if_old_version(project["data"])
        ReactPlannerData(**migrated_data)
        if project["data"]["version"] != migrated_data["version"]:
            ReactPlannerProjectsDBHandler.update(
                item_pks={"id": project["id"]}, new_values={"data": migrated_data}
            )

    all_projects = ReactPlannerProjectsDBHandler.find()
    from tqdm.contrib.concurrent import process_map

    process_map(migration_callable, all_projects, max_workers=8)
