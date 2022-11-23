import json

import pytest
from deepdiff import DeepDiff

from common_utils.constants import REGION
from handlers import BuildingHandler
from handlers.db import BuildingDBHandler, SiteDBHandler
from tests.constants import CLIENT_ID_1

TRIANGLE_CH_YX = [
    (1246810.24, 2683422.09, 0.0),
    (1246810.24, 2683432.09, 0.0),
    (1246820.24, 2683432.09, 0.0),
]
TRIANGLE_LAT_LON = [
    (47.366853958193545, 8.543057050180613, 0.0),
    (47.36685269227952, 8.543189423492752, 0.0),
    (47.366942626132776, 8.54319128690173, 0.0),
]


class TestBuildingHandler:
    @pytest.fixture
    def mock_db_dependencies(self, mocker):
        mocker.patch.object(
            BuildingDBHandler, "get_by", return_value={"site_id": mocker.ANY}
        )
        mocker.patch.object(
            SiteDBHandler, "get_by", return_value={"georef_region": REGION.CH.name}
        )

    @pytest.mark.parametrize(
        "file_crs_region, triangle_in, triangle_out_expected",
        [
            (
                REGION.CH,
                TRIANGLE_CH_YX,
                TRIANGLE_LAT_LON,
            ),
            (
                REGION.LAT_LON,
                TRIANGLE_LAT_LON,
                TRIANGLE_LAT_LON,
            ),
        ],
    )
    def test_get_triangles_lat_lon_new_file_format(
        self,
        file_crs_region,
        triangle_in,
        triangle_out_expected,
        mocker,
        mock_db_dependencies,
    ):
        triangles = [[CLIENT_ID_1, [triangle_in]]]
        expected_triangles_lat_lon = [[CLIENT_ID_1, [triangle_out_expected]]]

        mocker.patch.object(
            BuildingHandler,
            BuildingHandler._get_triangles_from_gcs.__name__,
            return_value=json.dumps(
                {"triangles": triangles, "georef_region": file_crs_region.name}
            ),
        )

        building_handler = BuildingHandler(building_id=mocker.ANY)
        triangles_lat_lon = building_handler.get_triangles_from_gcs_lat_lon()

        assert not DeepDiff(
            expected_triangles_lat_lon,
            triangles_lat_lon,
            ignore_type_in_groups=[(list, tuple)],
        )

    def test_get_triangles_lat_lon_old_file_format(self, mocker, mock_db_dependencies):
        triangles_local_yx = [[CLIENT_ID_1, [TRIANGLE_CH_YX]]]
        expected_triangles_lat_lon = [
            [
                CLIENT_ID_1,
                [TRIANGLE_LAT_LON],
            ]
        ]

        mocker.patch.object(
            BuildingHandler,
            BuildingHandler._get_triangles_from_gcs.__name__,
            return_value=json.dumps(triangles_local_yx),
        )

        building_handler = BuildingHandler(building_id=mocker.ANY)

        assert not DeepDiff(
            expected_triangles_lat_lon,
            building_handler.get_triangles_from_gcs_lat_lon(),
            ignore_type_in_groups=[(list, tuple)],
        )

    def test_generate_and_upload_triangles_to_gcs_projects_to_lat_lon(
        self, mocker, mock_db_dependencies
    ):
        # given
        mocker.patch.object(
            BuildingHandler,
            "generate_layout_triangles",
            return_value=[[CLIENT_ID_1, [TRIANGLE_CH_YX]]],
        )
        mocked_upload_to_gcs = mocker.patch.object(
            BuildingHandler, "_upload_triangles_to_gcs"
        )
        # when
        BuildingHandler(building_id=mocker.ANY).generate_and_upload_triangles_to_gcs(
            simulation_version=mocker.ANY
        )
        # then
        expected_triangles_lat_lon = [
            [
                CLIENT_ID_1,
                [TRIANGLE_LAT_LON],
            ]
        ]
        assert (
            mocked_upload_to_gcs.call_args[1]["triangles"]["georef_region"]
            == REGION.LAT_LON.name
        )
        assert not DeepDiff(
            expected_triangles_lat_lon,
            list(mocked_upload_to_gcs.call_args[1]["triangles"]["triangles"]),
            ignore_type_in_groups=[(list, tuple)],
        )
