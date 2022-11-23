from typing import Collection

import numpy as np
import pytest
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box

from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.v2.base import BaseElevationHandler
from surroundings.v2.constants import DEFAULT_RIVER_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import (
    BuildingFootprintTransformer,
    ForestGeometryTransformer,
    GroundCoveringLineStringTransformer,
    GroundCoveringPolygonTransformer,
    NoTransformer,
    RiverLinesGeometryTransformer,
    TreeGeometryTransformer,
)
from surroundings.v2.grounds import ElevationHandler
from tests.surroundings_utils import create_raster_window, flat_elevation_handler


class TestGroundCoveringPolygonTransformer:
    instance_cls = GroundCoveringPolygonTransformer

    def get_instance(
        self, elevation_handler: BaseElevationHandler, ground_offset: float
    ):
        return self.instance_cls(
            elevation_handler=elevation_handler, ground_offset=ground_offset
        )

    @pytest.mark.parametrize("ground_offset", [0.0, 0.2])
    def test_transform_geometry_calls_project_onto_surface(self, mocker, ground_offset):
        fake_elevation_handler = mocker.MagicMock()
        fake_projected = mocker.MagicMock()
        fake_elevation_handler.project_onto_surface.return_value = iter(
            [fake_projected]
        )

        geometry = Geometry(geom=box(0, 0, 1, 1), properties=mocker.ANY)

        (transformed,) = list(
            GroundCoveringPolygonTransformer(
                elevation_handler=fake_elevation_handler, ground_offset=ground_offset
            ).transform_geometry(geometry=geometry)
        )

        fake_elevation_handler.project_onto_surface.assert_called_once_with(
            polygon=geometry.geom, ground_offset=ground_offset
        )
        assert transformed == fake_projected


class _TestGroundCoveringLineStringTransformer:
    instance_cls = GroundCoveringLineStringTransformer

    def get_instance(self, elevation_handler=None, ground_offset=None):
        return self.instance_cls(
            elevation_handler=elevation_handler, ground_offset=ground_offset
        )

    def test_transform_geometry(self, mocker):
        mocker.patch.object(self.instance_cls, "get_width", return_value=1.0)
        mocker.patch.object(
            self.instance_cls,
            "get_extension_type",
            return_value=LINESTRING_EXTENSION.SYMMETRIC,
        )

        elevation_handler = flat_elevation_handler(
            bounds=(-2, -2, 2, 2), elevation=-1.0
        )

        transformer = self.get_instance(
            elevation_handler=elevation_handler, ground_offset=0.15
        )
        transformed = list(
            transformer.transform_geometry(
                Geometry(geom=LineString([(0, 0, 1), (0, 1, 1)]), properties=mocker.ANY)
            )
        )

        expected_transformed = map(
            Polygon,
            [
                [
                    (0.0, 0.0, -0.85),
                    (-0.5, 0.0, -0.85),
                    (-0.5, 1.0, -0.85),
                    (0.5, 1.0, -0.85),
                    (0.5, 0.5, -0.85),
                    (0.0, 0.0, -0.85),
                ],
                [
                    (0.5, 0.5, -0.85),
                    (0.5, 0.0, -0.85),
                    (0.0, 0.0, -0.85),
                    (0.5, 0.5, -0.85),
                ],
            ],
        )
        assert len(transformed) == 2
        assert all(
            actual.equals(expected)
            for actual, expected in zip(transformed, expected_transformed)
        )


class TestRiverLinesGeometryTransformer(_TestGroundCoveringLineStringTransformer):
    instance_cls = RiverLinesGeometryTransformer

    def test_get_width(self, mocker):
        assert self.get_instance().get_width(geometry=mocker.ANY) == DEFAULT_RIVER_WIDTH


class TestNoTransformer:
    @pytest.mark.parametrize(
        "geom, expected_transformed",
        [
            (box(0, 0, 1, 1), [box(0, 0, 1, 1)]),
            (
                MultiPolygon([box(0, 0, 1, 1), box(1, 1, 2, 2)]),
                [box(0, 0, 1, 1), box(1, 1, 2, 2)],
            ),
        ],
    )
    def test_transform_geometry(self, geom, expected_transformed, mocker):
        assert (
            list(
                NoTransformer().transform_geometry(
                    geometry=Geometry(geom=geom, properties=mocker.ANY)
                )
            )
            == expected_transformed
        )


class _TestForestGeometryTransformer:
    instance_cls = ForestGeometryTransformer

    def get_instance(
        self,
        elevation_handler=None,
        ground_offset=None,
    ):
        return self.instance_cls(
            elevation_handler=elevation_handler, ground_offset=ground_offset
        )

    def test_transform_geometry_calls_forest_generator(self, mocker):
        fake_elevation_handler = mocker.MagicMock()

        fake_triangle = mocker.MagicMock()
        fake_forest_generator = mocker.MagicMock()
        fake_forest_generator.get_forest_triangles.return_value = iter([fake_triangle])

        mocker.patch.object(
            self.instance_cls,
            "get_forest_generator",
            return_value=fake_forest_generator,
        )

        geometry = Geometry(geom=box(0, 0, 1, 1), properties=mocker.ANY)

        (tree_triangle,) = list(
            self.get_instance(
                elevation_handler=fake_elevation_handler
            ).transform_geometry(geometry=geometry)
        )

        fake_forest_generator.get_forest_triangles.assert_called_once_with(
            elevation_handler=fake_elevation_handler,
            building_footprints=[],
            tree_shape=geometry.geom,
        )
        assert tree_triangle == Polygon(fake_triangle)

    def test_transform_geometry_projects_onto_ground_if_no_forest_generator(
        self, mocker
    ):
        fake_polygon = mocker.MagicMock()
        mocked_ground_covering_polygon_transformer = mocker.patch.object(
            GroundCoveringPolygonTransformer,
            "transform_geometry",
            return_value=iter([fake_polygon]),
        )
        mocker.patch.object(
            self.instance_cls, "get_forest_generator", return_value=False
        )
        geometry = Geometry(geom=box(0, 0, 1, 1), properties=mocker.ANY)

        (polygon_z,) = list(self.get_instance().transform_geometry(geometry=geometry))

        mocked_ground_covering_polygon_transformer.assert_called_once_with(
            geometry=geometry
        )
        assert polygon_z == fake_polygon


class _TestTreeGeometryTransformer:
    instance_cls = TreeGeometryTransformer

    def get_instance(self, elevation_handler=None):
        return self.instance_cls(elevation_handler=elevation_handler)

    def test_transform_geometry_calls_tree_generator(self, mocker):
        from surroundings.v2.geometry_transformer import StandardTreeGenerator

        fake_triangle = mocker.MagicMock()
        dummy_tree_height = 10.0
        mocker.patch.object(
            self.instance_cls, "get_height", return_value=dummy_tree_height
        )
        mocked_tree_generator = mocker.patch.object(
            StandardTreeGenerator, "get_triangles", return_value=iter([fake_triangle])
        )

        elevation_handler = flat_elevation_handler(bounds=(-1, -1, 1, 1), elevation=0.0)
        geometry = Geometry(geom=Point(0, 0, 0), properties=mocker.ANY)

        (tree_triangle,) = list(
            self.get_instance(elevation_handler=elevation_handler).transform_geometry(
                geometry=geometry
            )
        )

        mocked_tree_generator.assert_called_once_with(
            ground_level=0.0,
            building_footprints=[],
            tree_height=dummy_tree_height,
            tree_location=geometry.geom,
        )
        assert tree_triangle == Polygon(fake_triangle)


def create_expected_building_triangles(
    bottom_level: float, top_level: float
) -> Collection[Polygon]:
    return list(
        map(
            Polygon,
            [
                [
                    (1.0, 0.0, bottom_level),
                    (1.0, 1.0, bottom_level),
                    (1.0, 1.0, top_level),
                ],
                [
                    (1.0, 1.0, top_level),
                    (1.0, 0.0, top_level),
                    (1.0, 0.0, bottom_level),
                ],
                [
                    (1.0, 1.0, bottom_level),
                    (0.0, 1.0, bottom_level),
                    (0.0, 1.0, top_level),
                ],
                [
                    (0.0, 1.0, top_level),
                    (1.0, 1.0, top_level),
                    (1.0, 1.0, bottom_level),
                ],
                [
                    (0.0, 1.0, bottom_level),
                    (0.0, 0.0, bottom_level),
                    (0.0, 0.0, top_level),
                ],
                [
                    (0.0, 0.0, top_level),
                    (0.0, 1.0, top_level),
                    (0.0, 1.0, bottom_level),
                ],
                [
                    (0.0, 0.0, bottom_level),
                    (1.0, 0.0, bottom_level),
                    (1.0, 0.0, top_level),
                ],
                [
                    (1.0, 0.0, top_level),
                    (0.0, 0.0, top_level),
                    (0.0, 0.0, bottom_level),
                ],
                [
                    (0.0, 1.0, bottom_level),
                    (0.0, 0.0, bottom_level),
                    (1.0, 0.0, bottom_level),
                ],
                [
                    (1.0, 0.0, bottom_level),
                    (1.0, 1.0, bottom_level),
                    (0.0, 1.0, bottom_level),
                ],
                [
                    (0.0, 1.0, top_level),
                    (0.0, 0.0, top_level),
                    (1.0, 0.0, top_level),
                ],
                [
                    (1.0, 0.0, top_level),
                    (1.0, 1.0, top_level),
                    (0.0, 1.0, top_level),
                ],
            ],
        )
    )


class _TestBuildingFootprintTransformer:
    instance_cls = BuildingFootprintTransformer

    def get_instance(self, elevation_handler=None):
        return self.instance_cls(
            elevation_handler=elevation_handler,
        )

    @pytest.mark.parametrize("min_ground_level, max_ground_level", [(0.0, 3.0)])
    def test_get_min_max_ground_levels(self, min_ground_level, max_ground_level):
        building_footprint = box(0.0, 0.0, 1.0, 1.0)

        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                bounds=(-0.5, -0.5, 1.5, 1.5),
                data=np.array(
                    [
                        [
                            [min_ground_level, min_ground_level],
                            [max_ground_level, min_ground_level],
                        ]
                    ]
                ),
            )
        )

        building_footprint_transformer = self.get_instance(
            elevation_handler=elevation_handler
        )

        assert building_footprint_transformer._get_min_max_ground_levels(
            geometry=Geometry(geom=building_footprint, properties={})
        ) == (min_ground_level, max_ground_level)

    @pytest.mark.parametrize(
        "min_ground_level, max_ground_level, building_height, expected_building_triangles",
        [
            (
                0.0,
                3.0,
                5.0,
                create_expected_building_triangles(
                    top_level=3.0 + 5.0,
                    bottom_level=0.0 - 2.0,
                ),
            ),
            (
                -30.0,
                5.0,
                10.0,
                create_expected_building_triangles(
                    top_level=5.0 + 10.0,
                    bottom_level=-30.0 - 2.0,
                ),
            ),
        ],
    )
    def test_transform(
        self,
        min_ground_level,
        max_ground_level,
        building_height,
        expected_building_triangles,
        mocker,
    ):
        building_footprint = box(0.0, 0.0, 1.0, 1.0)

        mocker.patch.object(
            self.instance_cls, "get_height", return_value=building_height
        )

        elevation_handler = ElevationHandler(
            raster_window=create_raster_window(
                bounds=(-0.5, -0.5, 1.5, 1.5),
                data=np.array(
                    [
                        [
                            [min_ground_level, min_ground_level],
                            [max_ground_level, min_ground_level],
                        ]
                    ]
                ),
            )
        )

        building_footprint_transformer = self.get_instance(
            elevation_handler=elevation_handler
        )

        transformed = list(
            building_footprint_transformer.transform_geometry(
                geometry=Geometry(geom=building_footprint, properties={})
            )
        )

        assert transformed == expected_building_triangles
