from shapely.geometry import Point

from common_utils.constants import SurroundingType
from tests.utils import check_surr_triangles, random_simulation_version


class TestSwissTopoMountainSurroundingHandler:
    def test_get_triangles(self, fixtures_swisstopo_path, mocked_gcp_download, mocker):
        from surroundings.swisstopo import SwissTopoMountainSurroundingHandler
        from surroundings.swisstopo.raster_window_triangulator import (
            SwissTopoMountainsRasterWindowProvider,
        )

        mocker.patch.object(
            SwissTopoMountainsRasterWindowProvider,
            "get_raster_filenames",
            return_value=[
                fixtures_swisstopo_path.joinpath("alti/mocked_swiss_mountains.tif")
            ],
        )

        type_triangle_tuples = list(
            SwissTopoMountainSurroundingHandler(
                location=Point(2673000, 1243000),
                bounding_box_extension=50,
                mountain_bounding_box_extension=2000,
                simulation_version=random_simulation_version(),
            ).get_triangles()
        )

        check_surr_triangles(
            expected_area=7477500.0,
            first_elem_height=644.205810546875,
            expected_num_triangles=5982,
            surr_triangles=type_triangle_tuples,
            expected_surr_type={SurroundingType.MOUNTAINS},
        )
