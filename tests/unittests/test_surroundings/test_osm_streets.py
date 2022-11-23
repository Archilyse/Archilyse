import json
from math import isclose

import pytest
from shapely.geometry import LineString

from common_utils.constants import REGION, SurroundingType
from dufresne.polygon import get_sides_as_lines_by_length
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.osm.osm_street_handler import OSM_STREET_TYPE_WIDTH, OSMStreetHandler
from surroundings.utils import FilteredPolygonEntity
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMStreetHandler:
    def test_osm_get_street_triangles(
        self,
        mocker,
        fixtures_osm_path,
        monaco_street_location,
        dummy_elevation,
        mock_elevation,
    ):
        mock_elevation(100, ZeroElevationHandler)
        with fixtures_osm_path.joinpath("streets/monaco.json").open() as f:
            mocker.patch.object(
                OSMStreetHandler, "load_entities", return_value=json.load(f)
            )

        street_surrounding_handler = OSMStreetHandler(
            location=monaco_street_location,
            region=REGION.MC,
            bounding_box_extension=100,
            simulation_version=random_simulation_version(),
        )

        street_triangles = list(
            street_surrounding_handler.get_triangles(building_footprints=[])
        )

        # Content checks
        assert street_triangles is not None
        check_surr_triangles(
            expected_area=728.296,
            first_elem_height=100.2,
            expected_num_triangles=59,
            surr_triangles=street_triangles,
            expected_surr_type={SurroundingType.STREETS},
        )

    @pytest.mark.parametrize("road_class", OSM_STREET_TYPE_WIDTH.keys())
    def test_street_width_from_osm_keys(
        self, fixtures_osm_path, road_class, monaco_street_location, dummy_elevation
    ):
        street_surrounding_handler = OSMStreetHandler(
            location=monaco_street_location,
            region=REGION.MC,
            simulation_version=random_simulation_version(),
        )
        street_line = LineString(
            [
                (209962.8655835035, 4826140.099471907),
                (209964.17231034557, 4826169.2199380025),
            ]
        )

        street_polygons = street_surrounding_handler._apply_width(
            entity=FilteredPolygonEntity(
                geometry=LineString(), entity={"properties": {"fclass": road_class}}
            ),
            line=street_line,
        )
        width = get_sides_as_lines_by_length(
            street_polygons.geoms[0].minimum_rotated_rectangle
        )[0].length

        assert isclose(width, OSM_STREET_TYPE_WIDTH[road_class], abs_tol=1e-2)
