import pytest
from shapely.geometry import LineString, Point, Polygon, box

from surroundings.ground_excavator import GroundExcavator
from tests.utils import check_polygons_z


class TestGroundExcavator:
    @pytest.mark.parametrize(
        "min_z, lowering_construction_site", [(1, 0), (2, 1), (3, 2)]
    )
    def test_get_elevation_construction_site_floor(
        self, mocker, min_z, lowering_construction_site
    ):
        mocked_building_borders_3d = mocker.patch.object(
            GroundExcavator,
            "_get_building_borders_3d",
            return_value=[
                LineString([(0.0, 0.0, min_z), (0.0, 1.0, 10.0)]),
                LineString([(0.0, 1.0, 10.0), (1.0, 1.0, 10.0)]),
                LineString([(0.0, 0.0, 10.0), (1.0, 0.0, 10.0)]),
                LineString([(1.0, 0.0, 10.0), (1.0, 1.0, 10.0)]),
            ],
        )
        fake_excavation_footprint = Polygon()
        excavator = GroundExcavator(building_footprints=mocker.ANY)
        elevation = excavator._get_elevation_construction_site_floor(
            excavation_footprint=fake_excavation_footprint,
            lowering_construction_site=lowering_construction_site,
        )

        mocked_building_borders_3d.assert_called_once_with(
            excavation_footprint=fake_excavation_footprint
        )
        assert elevation == min_z - lowering_construction_site

    def test_get_borders_3d(self, mocker):
        mocker.patch.object(
            GroundExcavator,
            "_triangles_intersecting_buildings_borders",
            [
                Polygon([(0, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 0)]),
                Polygon([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 0, 0)]),
            ],
        )

        excavation_footprint = box(0, 0, 1, 1)

        excavator = GroundExcavator(building_footprints=mocker.ANY)
        building_borders_3d = list(
            excavator._get_building_borders_3d(
                excavation_footprint=excavation_footprint
            )
        )

        assert building_borders_3d == [
            LineString([(0.0, 0.0, 0.0), (0.0, 1.0, 0.0)]),
            LineString([(0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]),
            LineString([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]),
            LineString([(1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]),
        ]

    def test_extrude_faces_from_linestring(self):
        rectangle = box(-10, -10, 10, 10)
        faces = GroundExcavator._extrude_faces_from_linestring(
            linestring=LineString(rectangle.exterior.coords),
            z_values=[5] * len(rectangle.exterior.coords),
        )
        assert len(faces) == 4

    def test_get_triangles_excavation_floor(self):
        location = Point(2673000, 1243000)
        triangles = GroundExcavator._get_triangles_excavation_floor(
            excavation_footprint=box(
                location.x - 10,
                location.y - 10,
                location.x + 10,
                location.y + 10,
            ),
            ground_elevation=568.9414062,
        )
        check_polygons_z(
            expected_area=400.0,
            first_elem_height=568.94140625,
            expected_num_polygons=2,
            polygons_z=map(Polygon, triangles),
        )
