from shapely.geometry import Point

from common_utils.constants import REGION, SurroundingType
from surroundings.srtm.grounds_surrounding_handler import SRTMGroundSurroundingHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestSRTMGroundSurroundingHandler:
    def test_get_triangles(self, mocked_srtm_tiles):
        handler = SRTMGroundSurroundingHandler(
            location=Point(2679552.5, 1244805.0),
            region=REGION.CH,
            bounding_box_extension=200,
            simulation_version=random_simulation_version(),
        )
        with mocked_srtm_tiles("n47_e008_1arc_v3"):
            triangles = list(handler.get_triangles())

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=168538.6161,
            first_elem_height=821.7328,
            expected_num_triangles=520,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.GROUNDS},
        )

    def test_get_triangles_w_layout(self, mocked_srtm_tiles):
        location = Point(2679552.5, 1244805.0)
        handler = SRTMGroundSurroundingHandler(
            location=Point(2679552.5, 1244805.0),
            region=REGION.CH,
            bounding_box_extension=200,
            simulation_version=random_simulation_version(),
            building_footprints=[location.buffer(5)],
        )
        with mocked_srtm_tiles("n47_e008_1arc_v3"):
            triangles = list(handler.get_triangles())

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=168538.6161,
            first_elem_height=821.7328,
            expected_num_triangles=558,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.GROUNDS},
        )
