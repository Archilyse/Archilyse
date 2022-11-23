class TestFileHandler:
    def test_cleanup_trash(self, mocker):
        from handlers.dms.file_handler import FileDBHandler, FileHandler

        fake_deleted_files = [
            (file_checksum, client_id)
            for file_checksum, client_id in [
                ("some", 1),
                ("some_other", 1),
                ("else", 2),
            ]
        ]

        mocker.patch.object(
            FileDBHandler, "remove_deleted_files", return_value=fake_deleted_files
        )
        mocked_gcs_delete = mocker.patch.object(FileHandler, "delete_file_from_gcs")

        FileHandler.cleanup_trash()

        mocked_gcs_delete.assert_has_calls(
            [
                mocker.call(checksum=checksum, client_id=client_id)
                for checksum, client_id in fake_deleted_files
            ]
        )
