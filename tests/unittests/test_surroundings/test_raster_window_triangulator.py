import numpy as np

from surroundings.raster_window_triangulator import RasterWindowTriangulator


class TestRasterWindowTriangulator:
    def test_create_triangles(self, mocker):
        fake_raster_window = mocker.MagicMock()
        fake_raster_window.width.return_value = 2
        fake_raster_window.height.return_value = 2
        fake_raster_window.grid_values.return_value = np.ones((2, 2))
        fake_raster_window.get_xy_from_pixel.side_effect = lambda row, col: (
            row + 0.5,
            col + 0.5,
        )

        fake_raster_window_provider = mocker.MagicMock()
        fake_raster_window_provider.get_raster_window.return_value = fake_raster_window
        mocker.patch.object(
            RasterWindowTriangulator,
            "raster_window_provider",
            mocker.PropertyMock(return_value=fake_raster_window_provider),
        )

        triangulator = RasterWindowTriangulator(
            bounding_box=mocker.ANY, region=mocker.ANY
        )
        triangles = list(triangulator.create_triangles())

        assert triangles == [
            ((0.5, 0.5, 1.0), (0.5, 1.5, 1.0), (1.5, 0.5, 1.0)),
            ((0.5, 1.5, 1.0), (1.5, 0.5, 1.0), (1.5, 1.5, 1.0)),
        ]
