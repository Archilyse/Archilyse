from handlers.quavis import QuavisGCPHandler


def test_upload_download_quavis_input_format(recreate_test_gcp_bucket, tmp_path):
    run_id = "lo_que_tal"
    to_upload = {"salpica": "carota"}
    QuavisGCPHandler.upload_quavis_input(run_id=run_id, quavis_input=to_upload)
    result = QuavisGCPHandler.get_quavis_input(run_id=run_id)
    assert result == to_upload


def test_upload_download_quavis_ouput_format(recreate_test_gcp_bucket, tmp_path):
    run_id = "lo_que_tal"
    to_upload = {"salpica": "carota"}
    QuavisGCPHandler.upload_quavis_output(run_id=run_id, quavis_output=to_upload)
    result = QuavisGCPHandler.get_quavis_output(run_id=run_id)
    assert result == to_upload
