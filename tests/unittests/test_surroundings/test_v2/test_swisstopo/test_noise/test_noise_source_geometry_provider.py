import pytest
from shapely.geometry import LineString, Point

from common_utils.constants import NOISE_SOURCE_TYPE, REGION
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo import SwissTopoNoiseSourceGeometryProvider
from surroundings.v2.swisstopo.railways.railway_geometry_provider import (
    SwissTopoNoisyRailwayGeometryProvider,
)
from surroundings.v2.swisstopo.streets.street_geometry_provider import (
    SwissTopoNoisyStreetsGeometryProvider,
)


class TestSwissTopoNoiseSourceGeometryProvider:
    @pytest.mark.parametrize(
        "noise_source_type, surrounding_handler",
        [
            (NOISE_SOURCE_TYPE.TRAFFIC, SwissTopoNoisyStreetsGeometryProvider),
            (NOISE_SOURCE_TYPE.TRAIN, SwissTopoNoisyRailwayGeometryProvider),
        ],
    )
    def test_correct_surrounding_handler_is_called(
        self, noise_source_type, surrounding_handler, mocker
    ):
        location = Point(0, 0)
        bounding_box_extension = 500
        geometries = iter(
            [
                Geometry(LineString([(0, 0), (1, 1)]), {}),
                Geometry(LineString([(0, 0), (1000, 1000)]), {}),
                Geometry(LineString([(1000, 1000), (2000, 2000)]), {}),
            ]
        )

        mocked_surr_handler = mocker.patch.object(
            surrounding_handler, "get_geometries", return_value=geometries
        )

        noise_source_geometries = list(
            SwissTopoNoiseSourceGeometryProvider(
                location=location,
                region=REGION.CH,
                bounding_box_extension=bounding_box_extension,
            ).get_source_geometries(noise_source_type)
        )

        assert noise_source_geometries == [
            LineString([(0, 0), (1, 1)]),
            LineString([(0, 0), (500, 500)]),
        ]
        assert mocked_surr_handler.call_count == 1
