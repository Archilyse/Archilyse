from shapely.geometry import Point, Polygon

from surroundings.v2.base import (
    BaseGeometryProvider,
    BaseGeometryTransformer,
    BaseSurroundingHandler,
)
from surroundings.v2.geometry import Geometry
from tests.utils import check_surr_triangles


class _TestBaseSurroundingHandler:
    instance_cls = BaseSurroundingHandler

    def get_instance(self, bounding_box=None, region=None, elevation_handler=None):
        return self.instance_cls(
            bounding_box=bounding_box,
            region=region,
            elevation_handler=elevation_handler,
        )

    def test_get_triangles(self, mocker):
        fake_surrounding_type = mocker.MagicMock()

        class FakeGeometryProvider(BaseGeometryProvider):
            def get_geometries(self):
                yield Geometry(geom=Point(0, 0), properties=mocker.ANY)

        class FakeGeometryTransformer(BaseGeometryTransformer):
            def transform_geometry(self, geometry):
                yield Polygon([(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1), (0, 0, 1)])

        mocker.patch.object(
            self.instance_cls, "geometry_provider", FakeGeometryProvider()
        )
        mocker.patch.object(
            self.instance_cls, "geometry_transformer", FakeGeometryTransformer()
        )
        mocker.patch.object(
            self.instance_cls,
            "get_surrounding_type",
            return_value=fake_surrounding_type,
        )

        triangles = list(self.get_instance().get_triangles())

        check_surr_triangles(
            expected_area=1.0,
            first_elem_height=1.0,
            expected_num_triangles=2,
            surr_triangles=triangles,
            expected_surr_type={fake_surrounding_type},
        )
