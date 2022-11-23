from pathlib import Path

import fiona
import pytest
from shapely.geometry import shape
from shapely.ops import unary_union

from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    SWISSTOPO_MISSING_TILES_BUILDINGS,
)
from simulations.geometry.bulk_volume_trigger_all_volume_tasks import (
    get_ch_borders,
    get_lk25_tiles,
    trigger_tasks,
)

NUMBER_OF_TILES = 3422


@pytest.fixture
def ch_borders(fixtures_swisstopo_path):
    with fiona.open(
        fixtures_swisstopo_path.joinpath("swissBOUNDARIES3D").joinpath(
            "swissBOUNDARIES3D_1_3_TLM_LANDESGEBIET.shp"
        )
    ) as file:
        return unary_union([shape(entity["geometry"]) for entity in file])


def test_get_ch_borders(
    mocked_gcp_download, mocker, fixtures_swisstopo_path, ch_borders
):
    from simulations.geometry.bulk_volume_trigger_all_volume_tasks import tempfile

    mocked_tempdir = mocker.patch.object(tempfile, "TemporaryDirectory")
    mocked_tempdir.return_value.__enter__.return_value = (
        fixtures_swisstopo_path.joinpath("swissBOUNDARIES3D")
    )
    local_file_name = fixtures_swisstopo_path.joinpath("swissBOUNDARIES3D").joinpath(
        "swissBOUNDARIES3D_1_3_TLM_LANDESGEBIET"
    )
    remote_file_path = Path(
        "swisstopo/swissBOUNDARIES3D/swissBOUNDARIES3D_1_3_TLM_LANDESGEBIET"
    )

    assert get_ch_borders() == ch_borders
    assert mocked_gcp_download.call_args_list == [
        mocker.call(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            remote_file_path=remote_file_path.with_suffix(suffix),
            local_file_name=local_file_name.with_suffix(suffix),
        )
        for suffix in (".shp", ".prj", ".shx", ".sbn", ".sbx")
    ]


def test_get_lk25_tiles(ch_borders):
    lk25_tiles = get_lk25_tiles(ch_borders=ch_borders)
    expected_length = NUMBER_OF_TILES
    assert len(lk25_tiles) == len(set(lk25_tiles)) == expected_length


def test_trigger_tasks(mocker, ch_borders):
    from handlers.db import BulkVolumeProgressDBHandler
    from simulations.geometry.bulk_volume_trigger_all_volume_tasks import (
        bulk_volume_volume_task,
    )

    mocked_db_add = mocker.patch.object(BulkVolumeProgressDBHandler, "add")
    mocked_tasks = mocker.patch.object(bulk_volume_volume_task, "delay")

    trigger_tasks(ch_borders=ch_borders, resolution=0.5)
    number_of_missing_tiles = sum(
        len(lk25_subindexes)
        for lk25_index, lk25_subindexes in SWISSTOPO_MISSING_TILES_BUILDINGS.items()
    )

    assert mocked_tasks.call_count == NUMBER_OF_TILES - number_of_missing_tiles
    assert mocked_db_add.call_count == NUMBER_OF_TILES - number_of_missing_tiles
