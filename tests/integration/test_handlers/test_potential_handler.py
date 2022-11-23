from pathvalidate import is_valid_filename


def test_get_view_surroundings(
    mocker,
    potential_db_simulation_ch_sun_empty,
):
    from handlers import PotentialSimulationHandler
    from surroundings.surrounding_handler import SurroundingStorageHandler

    mocked_download = mocker.patch.object(
        SurroundingStorageHandler,
        SurroundingStorageHandler._download_uncompress_surroundings_to_folder.__name__,
    )

    list(
        PotentialSimulationHandler.download_view_surroundings(
            simulation_info=potential_db_simulation_ch_sun_empty
        )
    )

    assert is_valid_filename(mocked_download.call_args.kwargs["remote_path"].name)
