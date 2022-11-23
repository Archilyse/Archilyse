import pytest
from shapely.geometry import Point

from common_utils.constants import GOOGLE_CLOUD_VIEW_SURROUNDINGS, SIMULATION_VERSION
from handlers.db import SiteDBHandler
from surroundings.surrounding_handler import (
    ManualSurroundingsHandler,
    SwissTopoSurroundingHandler,
)
from surroundings.swisstopo import (
    SwissTopoBuildingSurroundingHandler,
    SwissTopoExtraLakesSurroundingHandler,
    SwissTopoForestSurroundingHandler,
    SwissTopoGroundSurroundingHandler,
    SwissTopoLakeSurroundingHandler,
    SwissTopoMountainSurroundingHandler,
    SwissTopoParksSurroundingHandler,
    SwissTopoRailroadSurroundingHandler,
    SwissTopoRiverSurroundingHandler,
    SwissTopoStreetSurroundingHandler,
    SwissTopoTreeSurroundingHandler,
)


def test_generate_view_surrounding(
    site,
    building,
    plan_image_b,
    fixtures_path,
    mocker,
    mock_working_dir,
    mocked_gcp_upload_file_to_bucket,
    mocked_gcp_create_bucket,
):
    from handlers import SiteHandler

    SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={
            "lon": 8.485989015231816,
            "lat": 47.74946035003529,
        },
    )

    mocked_generate_surroundings_for_view_lv95_location = mocker.patch.object(
        SwissTopoSurroundingHandler,
        SwissTopoSurroundingHandler.generate_view_surroundings.__name__,
    )

    SiteHandler.upload_view_surroundings(site_id=site["id"])

    mocked_generate_surroundings_for_view_lv95_location.assert_called_once()
    assert (
        mocked_gcp_upload_file_to_bucket.call_args.kwargs["destination_folder"]
        == GOOGLE_CLOUD_VIEW_SURROUNDINGS
    )
    assert (
        mocked_gcp_upload_file_to_bucket.call_args.kwargs["destination_file_name"]
        == "2678544.000601088_1289289.0011523368.zip"
    )


@pytest.mark.parametrize(
    "simulation_version",
    [SIMULATION_VERSION.PH_01_2021],
)
@pytest.mark.parametrize("site_id", [999, None])
def test_generate_surroundings_for_view_lv95_location(
    mocker, site_id, simulation_version
):
    import fiona

    from surroundings.surrounding_handler import SwissTopoSurroundingHandler

    mocked_fiona = mocker.patch.object(fiona, "open")
    mocked_get_triangles = [
        mocker.patch.object(surrounding_handler, "get_triangles", return_value=[])
        for surrounding_handler in [
            SwissTopoBuildingSurroundingHandler,
            SwissTopoForestSurroundingHandler,
            SwissTopoParksSurroundingHandler,
            SwissTopoTreeSurroundingHandler,
            SwissTopoStreetSurroundingHandler,
            SwissTopoRailroadSurroundingHandler,
            SwissTopoRiverSurroundingHandler,
            SwissTopoLakeSurroundingHandler,
            SwissTopoExtraLakesSurroundingHandler,
            SwissTopoGroundSurroundingHandler,
        ]
    ]
    mocked_apply_manual_adjustments = mocker.patch.object(
        ManualSurroundingsHandler, "apply_manual_adjustments", return_value=[]
    )
    mocked_mountains_handler = mocker.patch.object(
        SwissTopoMountainSurroundingHandler, "get_triangles", return_value=[]
    )

    lv95_location = Point(2678544, 1289289)

    for _ in SwissTopoSurroundingHandler.generate_view_surroundings(
        location=lv95_location,
        building_footprints=[],
        simulation_version=simulation_version,
        site_id=site_id,
        bounding_box_extension=100,
    ):
        pass

    if site_id:
        assert mocked_apply_manual_adjustments.call_count == 1

    assert mocked_mountains_handler.call_count == 1
    assert all(mock.call_count == 1 for mock in mocked_get_triangles)

    # NOTE: fiona is only call when entities property is accessed
    assert mocked_fiona.call_count == 0
    for handler_mock in mocked_get_triangles:
        handler_mock.assert_called_once()
