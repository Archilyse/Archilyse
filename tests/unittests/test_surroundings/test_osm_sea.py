from common_utils.constants import REGION, SurroundingType
from surroundings.osm import OSMSeaHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMSeaHandler:
    def test_osm_sea_get_triangles(self, monaco_sea_location, sea_monaco_mocked):
        surrounding_handler = OSMSeaHandler(
            location=monaco_sea_location,
            region=REGION.MC,
            simulation_version=random_simulation_version(),
        )

        triangles = list(surrounding_handler.get_triangles(building_footprints=[]))
        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=51150859.82068357,
            first_elem_height=0.0,
            expected_num_triangles=3349,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.SEA},
        )
