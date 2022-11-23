from pathlib import Path

import pytest
from shapely.geometry import box

from common_utils.constants import GOOGLE_CLOUD_BUCKET, GOOGLE_CLOUD_SRTM, SRTM_DIR
from common_utils.exceptions import GCSLinkEmptyException
from handlers import GCloudStorageHandler
from surroundings.opentopo_handler import OpenTopoHandler
from surroundings.srtm.srtm_files_handler import Direction, SrtmFilesHandler


@pytest.mark.parametrize(
    "bounding_box,expected_tiles,expected_coords",
    [
        (
            box(minx=8.492015, maxx=9.492015, miny=47.349433, maxy=48.349433),
            (
                "n47_e008_1arc_v3.tif",
                "n47_e009_1arc_v3.tif",
                "n48_e008_1arc_v3.tif",
                "n48_e009_1arc_v3.tif",
            ),
            (
                (47, 8),
                (47, 9),
                (48, 8),
                (48, 9),
            ),
        ),
        (
            box(minx=-1, maxx=-1, miny=-10, maxy=-10),
            ("s10_w001_1arc_v3.tif",),
            ((-10, -1),),
        ),
        (
            box(minx=-1, maxx=0.5, miny=-10, maxy=-9),
            (
                "s10_w001_1arc_v3.tif",
                "s10_e000_1arc_v3.tif",
                "s09_w001_1arc_v3.tif",
                "s09_e000_1arc_v3.tif",
            ),
            ((-10, -1), (-10, 0), (-9, -1), (-9, 0)),
        ),
    ],
)
def test_get_srtm_filenames(bounding_box, expected_tiles, expected_coords):
    expected = [
        (SRTM_DIR.joinpath(f), GOOGLE_CLOUD_SRTM.joinpath(f), coords)
        for f, coords in zip(expected_tiles, expected_coords)
    ]
    actual = list(SrtmFilesHandler.get_srtm_filenames(bounding_box=bounding_box))
    assert actual == expected


def test_get_srtm_files_downloads_if_not_exists_locally(mocker, mocked_gcp_download):
    # given
    fake_source_file_name = Path("fake-gcs-link")
    nox_existent_destination_file = Path("n47_e008_1arc_v3.tif")
    coords = (47, 8)

    mocker.patch.object(
        SrtmFilesHandler,
        SrtmFilesHandler.get_srtm_filenames.__name__,
        return_value=iter(
            [
                (nox_existent_destination_file, fake_source_file_name, coords),
            ]
        ),
    )

    bounding_box = box(minx=8.492015, maxx=9.492015, miny=47.349433, maxy=48.349433)

    # when
    list(SrtmFilesHandler.get_srtm_files(bounding_box=bounding_box))

    # then
    mocked_gcp_download.assert_called_once_with(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        remote_file_path=fake_source_file_name,
        local_file_name=nox_existent_destination_file,
    )


def test_get_srtm_files_opentopo_call_if_not_exist_locally(
    mocker, mocked_gcp_upload_file_to_bucket
):
    data = b"random data"
    mocker.patch.object(
        GCloudStorageHandler,
        GCloudStorageHandler.get_blob_check_exists.__name__,
        side_effect=GCSLinkEmptyException(),
    )
    mocked_open_topo = mocker.patch.object(
        OpenTopoHandler,
        OpenTopoHandler.get_srtm_tile.__name__,
        return_value=data,
    )

    bounding_box = box(minx=8.2, maxx=8.5, miny=47.3, maxy=47.7)

    file = [f for f in SrtmFilesHandler.get_srtm_files(bounding_box=bounding_box)][0]

    assert file.is_file()
    mocked_gcp_upload_file_to_bucket.assert_called_once_with(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        destination_folder=GOOGLE_CLOUD_SRTM,
        destination_file_name=file.name.split("/")[-1],
        local_file_path=file,
        delete_local_after_upload=False,
    )
    mocked_open_topo.assert_called_once_with(bb_min_north=47, bb_min_east=8)


@pytest.mark.parametrize(
    "min_coord,max_coord,direction,expected",
    [
        (-84.2, -84.01, Direction.EAST, [("w085", -85)]),
        (84.01, 84.2, Direction.EAST, [("e084", 84)]),
        (-85.2, -84.01, Direction.EAST, [("w086", -86), ("w085", -85)]),
        (0, 0, Direction.EAST, [("e000", 0)]),
        (-0.1, 0.1, Direction.EAST, [("w001", -1), ("e000", 0)]),
        (-0.1, 0.1, Direction.NORTH, [("s01", -1), ("n00", 0)]),
        (10, 11, Direction.NORTH, [("n10", 10), ("n11", 11)]),
    ],
)
def test_get_direction_range_padded(min_coord, max_coord, direction, expected):
    assert (
        list(
            SrtmFilesHandler._get_direction_range_padded(
                min_coord, max_coord, direction
            )
        )
        == expected
    )


@pytest.mark.parametrize(
    "coord, direction, expected",
    [
        (0, Direction.NORTH, Direction.NORTH),
        (0, Direction.EAST, Direction.EAST),
        (10, Direction.NORTH, Direction.NORTH),
        (10, Direction.EAST, Direction.EAST),
        (-10, Direction.NORTH, Direction.SOUTH),
        (-10, Direction.EAST, Direction.WEST),
    ],
)
def test_get_direction_prefix(coord, direction, expected):
    assert SrtmFilesHandler._get_direction_prefix(coord, direction) == expected.value
