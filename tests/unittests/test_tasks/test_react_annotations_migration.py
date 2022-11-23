from common_utils.exceptions import DBNotFoundException
from handlers.db import ReactPlannerProjectsDBHandler
from handlers.editor_v2.schema import (
    CURRENT_REACT_ANNOTATION_VERSION,
    ReactPlannerData,
    ReactPlannerSchema,
)
from tasks import annotations_migration_tasks
from tasks.annotations_migration_tasks import migrate_react_annotations


def test_migrate_all_react_annotations(mocker, celery_eager):
    from handlers.db import react_planner_projects_handler
    from handlers.editor_v2 import react_planner_handler

    previous_version = f'V{int(CURRENT_REACT_ANNOTATION_VERSION.replace("V", "")) - 1}'
    mocker.patch.object(
        react_planner_projects_handler.ReactPlannerProjectsDBHandler,
        "find_iter",
        return_value=[
            {"id": 1, "data": {"version": previous_version}},
            {"id": 2, "data": {"version": CURRENT_REACT_ANNOTATION_VERSION}},
        ],
    )
    mocker.patch.object(
        react_planner_projects_handler.ReactPlannerProjectsDBHandler,
        "get_by",
        side_effect=[
            {
                "id": 1,
                "plan_id": 1,
                "data": ReactPlannerSchema().dump(
                    ReactPlannerData(version=previous_version)
                ),
            },
            {
                "id": 2,
                "plan_id": 2,
                "data": ReactPlannerSchema().dump(
                    ReactPlannerData(version=CURRENT_REACT_ANNOTATION_VERSION)
                ),
            },
        ],
    )
    mocked_updated = mocker.patch.object(
        react_planner_projects_handler.ReactPlannerProjectsDBHandler, "update"
    )
    mocked_migration_call = mocker.patch.object(
        react_planner_handler.ReactPlannerHandler,
        "migrate_data_if_old_version",
        return_value=ReactPlannerSchema().dump(ReactPlannerData()),
    )
    annotations_migration_tasks.migrate_all_react_annotations.delay()
    assert mocked_migration_call.call_count == 1
    assert isinstance(mocked_updated.call_args.kwargs["new_values"]["data"], dict)


def test_migrate_react_annotation(mocker):
    mocker.patch.object(
        ReactPlannerProjectsDBHandler, "get_by", side_effect=DBNotFoundException()
    )
    assert migrate_react_annotations(project_id=1) is None
