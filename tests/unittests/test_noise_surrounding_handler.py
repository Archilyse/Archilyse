import pytest
from shapely.geometry import Point, box

from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE
from common_utils.exceptions import RasterNotIntersectingException
from surroundings.swisstopo.noise_surrounding_handler import SwissTopoNoiseLevelHandler


class TestNoiseSurroundingHandler:
    @staticmethod
    def noise_handler_create(mock_open_raster_file):
        dataset, mocked_call = mock_open_raster_file(
            filename="Bahnlaerm_Tag_LV95_cropped"
        )
        # given
        # a handler initialized with a bounding box bigger than the bounds of the dataset
        minx, miny, maxx, maxy = dataset.bounds
        handler = SwissTopoNoiseLevelHandler(
            location=box(*dataset.bounds).centroid,
            bounding_box_extension=(maxx - minx) / 2 + 1000,
            noise_source_type=NOISE_SOURCE_TYPE.TRAIN,
            noise_time_type=NOISE_TIME_TYPE.DAY,
        )
        return handler, dataset, maxy, minx

    @pytest.mark.parametrize(
        "point",
        [
            Point(2679538.7, 1249432.5),
            Point(2679541.7, 1249432.5333),
            Point(2679545.0, 1249436.5333),
            Point(2679550.0, 1249440.0),
        ],
    )
    def test_get_at_reads_window_correctly(
        self, point, mocked_gcp_download, mock_open_raster_file
    ):
        """
        Since get_at() is using windowed read which wasn't super straight forward to me
        this test makes sure that get_at() really returns the same values as if we'd read directly from the file
        without using windowed read.
        """
        dataset, mocked_call = mock_open_raster_file(
            filename="Bahnlaerm_Nacht_LV95_cropped"
        )
        handler = SwissTopoNoiseLevelHandler(
            location=point,
            bounding_box_extension=10,
            noise_source_type=NOISE_SOURCE_TYPE.TRAIN,
            noise_time_type=NOISE_TIME_TYPE.NIGHT,
        )
        band = dataset.read(1)
        row, col = dataset.index(point.x, point.y)
        assert handler.get_at(location=point) == band[row, col]

    @pytest.mark.parametrize(
        "noise_type, noise_time, filename,expected_noise_value",
        [
            (
                NOISE_SOURCE_TYPE.TRAIN,
                NOISE_TIME_TYPE.DAY,
                "Bahnlaerm_Tag_LV95_cropped",
                67,
            ),
            (
                NOISE_SOURCE_TYPE.TRAIN,
                NOISE_TIME_TYPE.NIGHT,
                "Bahnlaerm_Nacht_LV95_cropped",
                63,
            ),
            (
                NOISE_SOURCE_TYPE.TRAFFIC,
                NOISE_TIME_TYPE.DAY,
                "StrassenLaerm_Tag_LV95_cropped",
                56,
            ),
            (
                NOISE_SOURCE_TYPE.TRAFFIC,
                NOISE_TIME_TYPE.NIGHT,
                "StrassenLaerm_Nacht_LV95_cropped",
                49,
            ),
        ],
    )
    def test_get_at_zurich_hardbruecke(
        self,
        noise_type,
        noise_time,
        filename,
        expected_noise_value,
        mocked_gcp_download,
        mock_open_raster_file,
    ):
        """
        This test assures that the values get_at returns are matching what we see on https://map.geo.admin.ch
        """
        point = Point(2679538.7, 1249432.5)  # Zurich Hardbruecke
        mock_open_raster_file(filename=filename)

        handler = SwissTopoNoiseLevelHandler(
            location=point,
            bounding_box_extension=10,
            noise_source_type=noise_type,
            noise_time_type=noise_time,
        )

        assert handler.get_at(location=point) == expected_noise_value
        assert mocked_gcp_download.call_count == 1

    def test_get_data_window_with_bounding_box_overlapping_raster_borders(
        self, mocked_gcp_download, mock_open_raster_file
    ):
        handler, dataset, maxy, minx = self.noise_handler_create(mock_open_raster_file)
        # the window shape is similar to the datasets shape,
        #  aka we load as much data as possible
        assert handler._data_window.grid_values.shape == dataset.shape

    def test_get_data_window_with_bounding_box_outside_of_raster_borders(
        self, mocked_gcp_download, mock_open_raster_file
    ):
        dataset, mocked_call = mock_open_raster_file(
            filename="Bahnlaerm_Tag_LV95_cropped"
        )

        # given
        # a handler initialized with a bounding box not overlapping with the bounds of the dataset
        minx, miny, maxx, maxy = dataset.bounds
        handler = SwissTopoNoiseLevelHandler(
            location=Point(minx - 1000, miny - 1000),
            bounding_box_extension=500,
            noise_source_type=NOISE_SOURCE_TYPE.TRAIN,
            noise_time_type=NOISE_TIME_TYPE.DAY,
        )

        # then
        with pytest.raises(RasterNotIntersectingException):
            # when
            handler._data_window

    def test_get_at_outside_of_raster_borders(
        self, mocked_gcp_download, mock_open_raster_file
    ):
        handler, dataset, maxy, minx = self.noise_handler_create(mock_open_raster_file)
        # a point within the bounding box but outside of the borders of the dataset
        x, y = minx - 500, maxy + 500

        # then
        with pytest.raises(RasterNotIntersectingException):
            # when
            handler.get_at(Point(x, y))
