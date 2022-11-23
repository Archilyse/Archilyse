import itertools

import numpy as np
import pytest
from shapely.affinity import rotate
from shapely.geometry import Point, Polygon, box

from common_utils.exceptions import BaseElevationException
from surroundings.v2.grounds import ElevationHandler, MultiRasterElevationHandler
from tests.surroundings_utils import create_raster_window


class TestElevationHandler:
    def test_project_onto_surface_should_not_yield_polygon(self):
        # Given a polygon not intersecting with the raster grid
        polygon = box(1000, 1000, 2000, 2000)

        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                data=np.full((1, 2, 2), 0.0),
                bounds=(-0.5, -0.5, 1.5, 1.5),
            )
        )

        # When the segment method is called
        sub_polygons = list(elevation_handler.project_onto_surface(polygon=polygon))
        # Then the polygon is silently ignored
        assert not sub_polygons

    @pytest.mark.parametrize("ground_offset", [0.0, 0.2])
    def test_project_onto_surface_transform_geometry_simple_case(self, ground_offset):
        """
        Tests, that the input polygon is split into 2 smaller ones when segmented against the raster grid.

        Input:
                          raster grid
                          _________
                 |--------|-----/-|--|
        polygon  |        |   /   |  |
                 |--------|-/-----|--|
                          ---------

        Output:
                          |-----/-|
        sub polygons      |   /   |
                          |-/-----|

        """
        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                data=np.full((1, 2, 2), 0.0),
                bounds=(-0.5, -0.5, 1.5, 1.5),
            )
        )
        sub_polygons = list(
            elevation_handler.project_onto_surface(
                polygon=box(-0.75, 0.25, 1.5, 0.75), ground_offset=ground_offset
            )
        )
        expected_polygons = map(
            Polygon,
            [
                [
                    (0.0, 0.75, ground_offset),
                    (0.75, 0.75, ground_offset),
                    (0.25, 0.25, ground_offset),
                    (0.0, 0.25, ground_offset),
                ],
                [
                    (1.0, 0.25, ground_offset),
                    (0.25, 0.25, ground_offset),
                    (0.75, 0.75, ground_offset),
                    (1.0, 0.75, ground_offset),
                ],
            ],
        )
        assert len(sub_polygons) == 2
        assert all(
            actual.equals(expected)
            for actual, expected in zip(sub_polygons, expected_polygons)
        )

    def test_project_onto_surface_transform_geometry_complex_case(self):
        """
        Tests, that the input polygon is split into 6 smaller ones if intermediate sub-polygons are intersected by a second
        triangle from a 2x2 triangle grid.
        """
        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                data=np.full((1, 3, 3), 0.0),
                bounds=(-0.5, -0.5, 2.5, 2.5),
            )
        )

        polygon = rotate(box(0.5, 0.5, 1.5, 1.5), angle=45)
        sub_polygons = list(elevation_handler.project_onto_surface(polygon=polygon))

        assert len(sub_polygons) == 6
        assert all(isinstance(s, Polygon) for s in sub_polygons)
        assert (
            len([s for s in sub_polygons if s.area == pytest.approx(0.125, abs=1e-9)])
            == 4
        )
        assert (
            len([s for s in sub_polygons if s.area == pytest.approx(0.25, abs=1e-9)])
            == 2
        )
        assert sum(sub_polygon.area for sub_polygon in sub_polygons) == pytest.approx(
            polygon.area, rel=1e-6
        )
        assert all(p1.touches(p2) for p1, p2 in itertools.combinations(sub_polygons, 2))

    @pytest.mark.parametrize(
        "x, y, z",
        [
            # from bottom left to top right
            (0.5, 0.5, 0.0),
            (0.75, 0.75, 0.25),
            (1.0, 1.0, 0.5),
            (1.25, 1.25, 0.75),
            (1.5, 1.5, 1.0),
            # from top left to bottom right
            (0.5, 1.5, 0.0),
            (0.75, 1.25, 0.25),
            (1.25, 0.75, 0.25),
            (1.5, 0.5, 0.0),
            # touching the borders
            (1.0, 0.5, 0.0),
            (1.5, 1.0, 0.5),
            (1.0, 1.5, 0.5),
            (0.5, 1.0, 0.0),
        ],
    )
    def test_get_elevation(self, x, y, z):
        raster_window = create_raster_window(data=np.array([[[0.0, 1.0], [0.0, 0.0]]]))
        assert (
            ElevationHandler(raster_window=raster_window).get_elevation(
                point=Point(x, y)
            )
            == z
        )

    def test_get_elevation_raises_elevation_exception(self):
        point_out_of_raster = Point(20, 20)
        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                data=np.array([[[0.0, 1.0], [0.0, 0.0]]])
            )
        )
        with pytest.raises(BaseElevationException, match="No triangle found."):
            elevation_handler.get_elevation(point=point_out_of_raster)


class TestMultiRasterElevationHandler:
    def test_get_elevation_raises_elevation_exception(self):
        point_out_of_raster = Point(20, 20)
        elevation_handler = MultiRasterElevationHandler(
            primary_window=create_raster_window(
                data=np.zeros((1, 2, 2)), bounds=(-1.0, -1.0, 1.0, 1.0)
            ),
            secondary_window=create_raster_window(
                data=np.zeros((1, 2, 2)), bounds=(-10.0, -10.0, 10.0, 10.0)
            ),
        )
        with pytest.raises(BaseElevationException, match="No triangle found."):
            elevation_handler.get_elevation(point=point_out_of_raster)

    @pytest.mark.parametrize("x, y, z", [(0.0, 0.0, 0.0), (5.0, 5.0, 1.0)])
    def test_get_elevation(self, x, y, z):
        elevation_handler = MultiRasterElevationHandler(
            primary_window=create_raster_window(
                data=np.zeros((1, 2, 2)), bounds=(-1.0, -1.0, 1.0, 1.0)
            ),
            secondary_window=create_raster_window(
                data=np.ones((1, 2, 2)), bounds=(-10.0, -10.0, 10.0, 10.0)
            ),
        )
        assert elevation_handler.get_elevation(point=Point(x, y)) == z

    def test_project_onto_surface(self, mocker):
        import surroundings.v2.grounds.elevation_handler

        fake_primary_elevation_handler = mocker.MagicMock()
        fake_primary_projected = mocker.MagicMock()
        fake_primary_elevation_handler.project_onto_surface.return_value = iter(
            [fake_primary_projected]
        )

        fake_secondary_elevation_handler = mocker.MagicMock()
        fake_secondary_projected = mocker.MagicMock()
        fake_secondary_elevation_handler.project_onto_surface.return_value = iter(
            [fake_secondary_projected]
        )

        mocker.patch.object(
            surroundings.v2.grounds.elevation_handler,
            "ElevationHandler",
            side_effect=[
                fake_primary_elevation_handler,
                fake_secondary_elevation_handler,
            ],
        )

        elevation_handler = MultiRasterElevationHandler(
            primary_window=create_raster_window(
                data=np.zeros((1, 2, 2)), bounds=(-1.0, -1.0, 1.0, 1.0)
            ),
            secondary_window=create_raster_window(
                data=np.ones((1, 2, 2)), bounds=(-10.0, -10.0, 10.0, 10.0)
            ),
        )

        primary_triangles_bbox = box(-0.5, -0.5, 0.5, 0.5)
        secondary_triangles_bbox = box(-5.0, -5.0, 5.0, 5.0).difference(
            primary_triangles_bbox
        )
        polygon = box(0.0, 0.0, 1.0, 1.0)

        result = list(elevation_handler.project_onto_surface(polygon=polygon))

        fake_primary_elevation_handler.project_onto_surface.assert_called_once_with(
            polygon=primary_triangles_bbox.intersection(polygon), ground_offset=0.0
        )
        fake_secondary_elevation_handler.project_onto_surface.assert_called_once_with(
            polygon=secondary_triangles_bbox.intersection(polygon),
            ground_offset=0.0,
        )

        assert result == [fake_primary_projected, fake_secondary_projected]
