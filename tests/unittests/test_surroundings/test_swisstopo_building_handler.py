import pytest
from shapely import wkt
from shapely.affinity import scale, translate
from shapely.geometry import MultiPolygon, Point, Polygon, box

from brooks.models import SimLayout, SimSpace
from common_utils.constants import REGION, SurroundingType
from handlers import PlanLayoutHandler
from surroundings.base_building_handler import Building
from surroundings.constants import BOUNDING_BOX_EXTENSION_GEOREFERENCING
from surroundings.swisstopo.building_surrounding_handler import (
    SwissTopoBuildingSurroundingHandler,
)
from tests.utils import random_simulation_version


@pytest.mark.parametrize(
    "bounding_box_extension,expected_nbr_of_buildings",
    [(10000, 790), (BOUNDING_BOX_EXTENSION_GEOREFERENCING, 14)],
)
def test_create_buildings(
    bounding_box_extension,
    expected_nbr_of_buildings,
    mocked_swiss_topo_building_files_and_location,
):
    buildings = list(
        SwissTopoBuildingSurroundingHandler(
            location=mocked_swiss_topo_building_files_and_location.centroid,
            bounding_box_extension=bounding_box_extension,
            simulation_version=random_simulation_version(),
        ).get_buildings()
    )

    assert len(buildings) == expected_nbr_of_buildings
    assert isinstance(buildings[0], Building)


def test_create_complex_building(mocker):
    from tests.fixtures.surroundings.swisstopo.buildings.complex_entity import (
        complex_entity,
    )

    handler = SwissTopoBuildingSurroundingHandler(
        location=Point(2609051, 1264033),
        bounding_box_extension=1000000,
        simulation_version=random_simulation_version(),
    )
    handler.load_entities = mocker.MagicMock(return_value=[complex_entity])
    buildings = list(handler.get_buildings())
    assert len(buildings) == 1


class TestSwisstopoFootprintConstruction:
    def test_building_footprint_empty_with_unary_union(self, fixtures_swisstopo_path):
        """
        This is an example of a swisstopo building for which the footprint construction with the unary union
        would return an empty geometry. Only the second method which filters out first all invalid polygons and then does
        the unary union returns a not empty footprint for some unknown reason
        """
        with fixtures_swisstopo_path.joinpath(
            "buildings/building_footprint_empty.wkt"
        ).open("r") as f:
            building_geometry = wkt.load(f)

        building_footprint = SwissTopoBuildingSurroundingHandler(
            location=Point(2609051, 1264033),
            simulation_version=random_simulation_version(),
        )._create_building_footprint(geometry=building_geometry)
        assert pytest.approx(expected=6.68, rel=0.01) == building_footprint.area

    def test_geometry_contains_invalid_geometries(self):
        invalid_polygon = Polygon([(0, 1), (0, 2), (0, 1)])
        valid_polygon = box(0, 0, 2, 2)
        geometry = MultiPolygon([invalid_polygon, valid_polygon])
        footprint = SwissTopoBuildingSurroundingHandler._create_building_footprint(
            geometry=geometry
        )
        assert footprint.area == pytest.approx(expected=4.0, rel=0.01)

    def test_building_geometry_contains_invalid_geometries(self, fixtures_path):
        """This fixture contains a building with a polygon that removes some area if it is not merged properly,
        generating a triangulated building with a hole. See PR 1351"""
        with fixtures_path.joinpath(
            "surroundings/swisstopo/buildings/building_footprint_invalid_polygons.wkt"
        ).open("r") as f:
            building_geometry = wkt.load(f)
        footprint = SwissTopoBuildingSurroundingHandler._create_building_footprint(
            geometry=building_geometry
        )
        # Invalid polygons are adding some area after the 8th decimal
        assert footprint.area == 327.09340801423394


def test_create_buildings_triangles(mocked_swiss_topo_building_files_and_location):
    building_type_triangle_tuples = list(
        SwissTopoBuildingSurroundingHandler(
            location=mocked_swiss_topo_building_files_and_location.centroid,
            simulation_version=random_simulation_version(),
        ).get_triangles(building_footprints=[])
    )
    assert len(building_type_triangle_tuples) == 2903
    assert building_type_triangle_tuples[0][0] is SurroundingType.BUILDINGS
    assert isinstance(building_type_triangle_tuples[0][1], list)
    assert isinstance(building_type_triangle_tuples[0][1][0], tuple)
    assert isinstance(building_type_triangle_tuples[0][1][0][0], float)


class TestRemoveTargetBuilding:
    def test_remove_target_buildings_artifical_case(self):
        building_footprint = box(minx=0, miny=0, maxx=10, maxy=10)

        wrongly_georefernced_layout = translate(geom=building_footprint, xoff=0.5)

        assert SwissTopoBuildingSurroundingHandler._is_target_building(
            building_footprint=scale(geom=building_footprint, xfact=0.9, yfact=0.85),
            building_footprints=[wrongly_georefernced_layout],
        )
        assert not SwissTopoBuildingSurroundingHandler._is_target_building(
            building_footprint=translate(geom=building_footprint, xoff=10),
            building_footprints=[wrongly_georefernced_layout],
        )

    def test_remove_target_buildings_real_case(self, mocker, mock_working_dir):
        from tests.fixtures.remove_target_fixtures import (
            brooks_layout_footprint,
            swisstopo_building1_footprint,
            swisstopo_building2_footprint,
        )

        layout_stub = SimLayout(spaces={SimSpace(footprint=brooks_layout_footprint)})
        layout_stub.apply_georef_transformation(
            georeferencing_transformation=PlanLayoutHandler(
                plan_info={
                    "id": -999,
                    "georef_y": 46.81108341747524,
                    "georef_rot_x": 6140.64624380213,
                    "georef_rot_angle": 12.0,
                    "georef_rot_y": -4584.76046166693,
                    "georef_x": 7.148974902822271,
                },
                site_info={"georef_region": REGION.CH.name},
            ).get_georeferencing_transformation(to_georeference=True)
        )
        assert not SwissTopoBuildingSurroundingHandler._is_target_building(
            building_footprint=swisstopo_building1_footprint,
            building_footprints=[layout_stub.footprint],
        )
        assert SwissTopoBuildingSurroundingHandler._is_target_building(
            building_footprint=swisstopo_building2_footprint,
            building_footprints=[layout_stub.footprint],
        )

    def test_removing_target_building_with_self_intersecting_layout(
        self, building_footprints_as_wkts, invalid_layout_footprint_path
    ):
        """

        if a layout footprint is self intersecting, shapely standard operations like intersection, within, contains
         can not be performed anymore. In this case we have to work with the centroid of the layout footprint
         to remove target buildings
        """

        swisstopo_building_footprint = building_footprints_as_wkts[0]

        with invalid_layout_footprint_path.open() as f:
            layout_footprint = wkt.load(f)
        layout_footprint = translate(
            layout_footprint,
            xoff=swisstopo_building_footprint.centroid.x - layout_footprint.centroid.x,
            yoff=swisstopo_building_footprint.centroid.y - layout_footprint.centroid.y,
        )

        assert SwissTopoBuildingSurroundingHandler._is_target_building(
            building_footprint=swisstopo_building_footprint,
            building_footprints=[layout_footprint],
        )
