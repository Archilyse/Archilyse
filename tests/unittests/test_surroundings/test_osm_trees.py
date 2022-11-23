import json

import pytest
from shapely.geometry import Point

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from surroundings.osm import OSMTreesHandler
from surroundings.srtm import SRTMElevationHandler
from tests.utils import check_surr_triangles


class TestOSMTreesHandler:
    @pytest.mark.parametrize(
        "simulation_version, expected_area",
        [
            (SIMULATION_VERSION.EXPERIMENTAL, 20.80),
            (SIMULATION_VERSION.PH_01_2021, 28.48),
        ],
    )
    def test_get_triangles(
        self,
        mocker,
        fixtures_osm_path,
        mock_elevation,
        simulation_version,
        expected_area,
    ):
        mock_elevation(100, SRTMElevationHandler)

        with fixtures_osm_path.joinpath("trees/entities.shp").open(mode="r") as f:
            mocker.patch.object(
                OSMTreesHandler, "load_entities", return_value=json.load(f)
            )

        surrounding_handler = OSMTreesHandler(
            location=project_geometry(
                geometry=Point(8.8953449, 47.553854),
                crs_from=REGION.LAT_LON,
                crs_to=REGION.CZ,
            ),
            region=REGION.CZ,
            simulation_version=simulation_version,
        )

        triangles = list(surrounding_handler.get_triangles(building_footprints=[]))

        # Content checks we created 1 tree, which is basically 2 cubes, 6 sides each, so 12 cube faces
        # and 2 triangles per face
        assert triangles is not None
        check_surr_triangles(
            expected_area=expected_area,
            first_elem_height=100.0,
            expected_num_triangles=24,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.TREES},
        )
