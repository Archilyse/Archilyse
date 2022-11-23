import numpy as np
import pytest
from shapely.geometry import Polygon, box

from common_utils.constants import REGION, SurroundingType
from surroundings.constants import UNMountainClass
from surroundings.srtm.raster_window_provider import SRTMRasterWindowProvider
from surroundings.v2.grounds.un_mountains_handler import UNMountainsHandler
from tests.surroundings_utils import create_raster_window
from tests.utils import check_surr_triangles


class TestUNMountainsHandler:
    @pytest.mark.parametrize(
        "mountain_classes,  expected_surrounding_type",
        [
            ([8, 2, 1], SurroundingType.MOUNTAINS_CLASS_1),
            ([3, 4, 2], SurroundingType.MOUNTAINS_CLASS_2),
            ([3, 4, 3], SurroundingType.MOUNTAINS_CLASS_3),
            ([8, 8, 4], SurroundingType.MOUNTAINS_CLASS_4),
            ([8, 8, 5], SurroundingType.MOUNTAINS_CLASS_5),
            ([8, 8, 6], SurroundingType.MOUNTAINS_CLASS_6),
            ([8, 8, 8], SurroundingType.GROUNDS),
        ],
    )
    def test_get_surrounding_type(
        self, mountain_classes, expected_surrounding_type, mocker
    ):
        from surroundings.v2.grounds.un_mountains_handler import UNMountainsClassifier

        mocked_classify = mocker.patch.object(
            UNMountainsClassifier,
            UNMountainsClassifier.classify.__name__,
            side_effect=[UNMountainClass(cls) for cls in mountain_classes],
        )

        extended_grounds_handler = UNMountainsHandler(
            raster_window=mocker.MagicMock(),
            exclusion_bounds=mocker.ANY,
        )
        triangle_indexes = ((0, 0), (1, 0), (0, 1))
        assert (
            extended_grounds_handler._get_surrounding_type(
                row=0, col=0, triangle_offsets=triangle_indexes
            )
            == expected_surrounding_type
        )
        assert mocked_classify.call_args_list == [
            mocker.call(position=row_col) for row_col in triangle_indexes
        ]

    def test_get_triangles_from_mocked_srtm_tiles(self, mocked_srtm_tiles):
        with mocked_srtm_tiles("n46_e008_1arc_v3"):
            raster_window = SRTMRasterWindowProvider(
                region=REGION.CH,
                resolution=300,
                bounds=(
                    2651350.0 - 5000,
                    1165150.0 - 5000,
                    2651350.0 + 5000,
                    1165150.0 + 5000,
                ),
            ).get_raster_window()

        triangles = list(
            UNMountainsHandler(
                raster_window=raster_window,
                exclusion_bounds=(
                    2651350.0 - 500,
                    1165150.0 - 500,
                    2651350.0 + 500,
                    1165150.0 + 500,
                ),
            ).get_triangles()
        )

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=103040000.00000018,
            expected_num_triangles=2304,
            first_elem_height=2117.67349,
            surr_triangles=triangles,
            expected_surr_type={
                SurroundingType.GROUNDS,
                SurroundingType.MOUNTAINS_CLASS_2,
                SurroundingType.MOUNTAINS_CLASS_3,
                SurroundingType.MOUNTAINS_CLASS_4,
                SurroundingType.MOUNTAINS_CLASS_5,
            },
        )

    @pytest.mark.parametrize(
        "exclusion_footprint_bounds",
        [
            (0.75, 0.75, 1.25, 1.25),
            (1.0, 1.0, 2.0, 2.0),
            (1.0, 1.0, 3.0, 3.0),
            (0.0, 1.5, 1.5, 3.0),
        ],
    )
    def test_get_triangles_excludes_exclusion_area(self, exclusion_footprint_bounds):
        raster_window = create_raster_window(data=np.ones((1, 3, 3)))

        raster_triangulated_footprint = box(0.5, 0.5, 2.5, 2.5)
        exclusion_footprint = box(*exclusion_footprint_bounds)
        expected_footprint_after_exclusion = raster_triangulated_footprint.difference(
            exclusion_footprint
        )

        # When
        triangles = list(
            UNMountainsHandler(
                raster_window=raster_window, exclusion_bounds=exclusion_footprint_bounds
            ).get_triangles()
        )
        triangles_polygons = [Polygon(triangle) for _, triangle in triangles]

        # Then
        assert (
            sum(triangle.area for triangle in triangles_polygons)
            == expected_footprint_after_exclusion.area
        )
        # And
        assert (
            sum(
                triangle.intersection(expected_footprint_after_exclusion).area
                for triangle in triangles_polygons
            )
            == expected_footprint_after_exclusion.area
        )
        # And
        assert (
            sum(
                triangle.intersection(exclusion_footprint).area
                for triangle in triangles_polygons
            )
            == 0.0
        )
