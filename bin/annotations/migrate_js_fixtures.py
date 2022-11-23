import json
from pathlib import Path

from common_utils.logger import logger
from handlers.editor_v2 import ReactPlannerHandler
from handlers.editor_v2.schema import ReactPlannerSchema


def main():
    file_path = Path("ui/react-planner/src/tests/utils/mockAnnotationsResponse.json")
    with file_path.open() as f:
        source_data = json.load(f)
        migrated_data = ReactPlannerHandler.migrate_data_if_old_version(
            plan_data=source_data["data"]
        )
        source_data["data"] = migrated_data
        ReactPlannerSchema().load(migrated_data).validate()

    with file_path.open("wt") as f:
        json.dump(source_data, f)

    for scene_file in (
        "ui/react-planner/src/tests/utils/mockScene.json",
        "ui/react-planner/src/tests/utils/mockSimpleScene.json",
        "ui/react-planner/src/tests/utils/mockSceneWithPotentialOrphanOpenings.json",
    ):
        file_path = Path(scene_file)
        with file_path.open() as f:
            source_data = json.load(f)
            logger.info(f"Migrating {scene_file}")
            migrated_data = ReactPlannerHandler.migrate_data_if_old_version(
                plan_data=source_data
            )
            ReactPlannerSchema().load(migrated_data)

        with file_path.open("wt") as f:
            json.dump(migrated_data, f)


if __name__ == "__main__":
    main()
