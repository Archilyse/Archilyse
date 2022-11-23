import pytest
from shapely.geometry import Point

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from surroundings.constants import BOUNDING_BOX_EXTENSION
from surroundings.osm.osm_grounds_handler import OSMGroundsHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMGroundsHandler:
    def test_get_triangles_monaco(self, monaco_street_location):
        surrounding_handler = OSMGroundsHandler(
            location=monaco_street_location,
            region=REGION.MC,
            simulation_version=random_simulation_version(),
        )

        triangles = list(surrounding_handler.get_triangles())

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=100000000.0,
            first_elem_height=-0.5,
            expected_num_triangles=2,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.GROUNDS},
        )

    @pytest.mark.parametrize(
        "simulation_version, first_element_height",
        [
            (SIMULATION_VERSION.EXPERIMENTAL, 594.7824096679688),
            (SIMULATION_VERSION.PH_01_2021, 592.7824096679688),
        ],
    )
    def test_get_triangles_swisstopo(
        self, mocked_swisstopo_esri_ascii_grid, simulation_version, first_element_height
    ):
        with mocked_swisstopo_esri_ascii_grid("swiss_1091_3"):
            surrounding_handler = OSMGroundsHandler(
                location=Point(2673000.0069945017, 1243000.0131927931),
                region=REGION.CH,
                simulation_version=simulation_version,
                bounding_box_extension=BOUNDING_BOX_EXTENSION - 5.0,
            )
            triangles = list(surrounding_handler.get_triangles())

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=1000000.0,
            first_elem_height=first_element_height,
            expected_num_triangles=20000,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.GROUNDS},
        )


# TODO: missing test for osm ground handler with srtm elevation
