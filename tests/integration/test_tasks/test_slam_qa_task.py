from tasks.surroundings_nightly_tasks import QA_SITE_IDS, run_slam_quality


def test_task_slam_qa_call(client_db, mocker, celery_eager):
    from tasks.workflow_tasks import run_digitize_analyze_client_tasks

    mocked_task = mocker.patch.object(
        run_digitize_analyze_client_tasks, "delay", return_value=True
    )

    run_slam_quality()
    assert mocked_task.call_count == len(QA_SITE_IDS)
