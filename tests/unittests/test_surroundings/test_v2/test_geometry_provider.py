from collections import OrderedDict
from unittest.mock import PropertyMock

import fiona
import pytest
from shapely.geometry import Point, box, mapping

from common_utils.constants import REGION
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_provider import ShapeFileGeometryProvider
from tests.surroundings_utils import create_fiona_collection


class _TestShapeFileGeometryProvider:
    instance_cls = ShapeFileGeometryProvider

    def get_instance(self, bounding_box=None, region=None, clip_geometries=False):
        return self.instance_cls(
            bounding_box=bounding_box, region=region, clip_geometries=clip_geometries
        )

    def test_geometry_filter(self, mocker):
        assert self.get_instance().geometry_filter(geometry=mocker.ANY) is True

    @pytest.fixture
    def simple_shapefile_with_points(self):
        schema = {"geometry": "Point", "properties": {"some": "float"}}
        entities = [
            (Point(*xy), {"some": float(i)}) for i, xy in enumerate([(0, 0), (1, 1)])
        ]
        with create_fiona_collection(schema=schema, records=entities) as collection:
            yield collection.name

    @pytest.mark.parametrize(
        "region, bounds, filter_return_value, expected_coords",
        [
            (REGION.CH, (0, 0, 1, 1), True, [(0, 0), (1, 1)]),
            (REGION.CH, (0, 0, 1, 1), False, []),
            (REGION.CH, (0, 0, 0.5, 0.5), True, [(0, 0)]),
            (REGION.CH, (0, 0, 0.5, 0.5), False, []),
            (
                REGION.LAT_LON,
                (
                    -19.917997943128036,
                    32.12448649090249,
                    -19.917991271398623,
                    32.124492168466794,
                ),
                True,
                [(-19.91799616385958, 32.12448649090249)],
            ),
        ],
    )
    def test_get_geometries(
        self,
        mocker,
        simple_shapefile_with_points,
        region,
        bounds,
        filter_return_value,
        expected_coords,
    ):
        mocker.patch.object(
            self.instance_cls,
            "get_source_filenames",
            return_value=[simple_shapefile_with_points],
        )
        mocker.patch.object(
            self.instance_cls,
            "geometry_filter",
            return_value=filter_return_value,
        )
        mocker.patch.object(
            self.instance_cls,
            "dataset_crs",
            PropertyMock(return_value=REGION.CH),
        )

        expected_geometries = [
            Geometry(geom=Point(*coords), properties=OrderedDict({"some": float(i)}))
            for i, coords in enumerate(expected_coords)
        ]

        geometry_provider = self.get_instance(bounding_box=box(*bounds), region=region)
        geometries = list(geometry_provider.get_geometries())
        for g in geometries:
            g.properties.pop("type", None)  # For the Noisy types

        assert geometries == expected_geometries

    def test_get_geometries_clips_geometries(self, mocker):
        fake_geometries = [
            {"geometry": mapping(box(0.0, 0.0, 1.0, 1.0)), "properties": {}}
        ]

        fake_shape_file = mocker.MagicMock()
        fake_shape_file.bounds = (0.0, 0.0, 1.0, 1.0)
        fake_shape_file.filter.return_value = fake_geometries

        mocker.patch.object(
            self.instance_cls,
            "get_source_filenames",
            return_value=[mocker.ANY],
        )
        mocker.patch.object(
            self.instance_cls,
            "dataset_crs",
            PropertyMock(return_value=REGION.CH),
        )
        mocker.patch.object(
            self.instance_cls,
            "geometry_filter",
            return_value=True,
        )
        mocker.patch.object(
            fiona, "open"
        ).return_value.__enter__.return_value = fake_shape_file

        geometry_provider = self.get_instance(
            bounding_box=box(0.0, 0.0, 0.5, 0.5), region=REGION.CH, clip_geometries=True
        )
        (geometry,) = list(geometry_provider.get_geometries())

        assert geometry.geom.equals(box(0.0, 0.0, 0.5, 0.5))
        geometry.properties.pop("type", None)  # For the Noisy types
        assert geometry.properties == {}
