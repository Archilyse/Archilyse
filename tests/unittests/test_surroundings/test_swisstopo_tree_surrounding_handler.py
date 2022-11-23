import json

import fiona
import pytest
from shapely.geometry import box

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from surroundings.swisstopo import tree_surrounding_handler
from tests.utils import check_surr_triangles, random_simulation_version


@pytest.fixture
def extruded_spy(mocker):
    from surroundings import base_tree_surrounding_handler

    return mocker.spy(
        base_tree_surrounding_handler, "get_triangles_from_extruded_polygon"
    )


class TestTreeSurroundingHandler:
    @pytest.mark.parametrize(
        "layouts, num_triangles, area, extruded_calls, first_tree_height, simulation_version",
        [
            (
                [],
                432 * 2,
                2869.3844051113506,
                36 * 2,
                250.0,
                SIMULATION_VERSION.PH_01_2021,
            ),
            (
                [box(2612860, 1267240, 2612880, 1267260)],
                396 * 2,
                2661.609684149128,
                33 * 2,
                250.0,
                SIMULATION_VERSION.PH_01_2021,
            ),
        ],
    )
    def test_get_triangles(
        self,
        mocker,
        fixtures_swisstopo_path,
        tree_surr_location,
        layouts,
        num_triangles,
        area,
        extruded_calls,
        first_tree_height,
        mocked_gcp_download,
        mock_elevation,
        simulation_version,
        extruded_spy,
    ):
        """
        To plot the trees in 3D
        >>> from surroundings.visualization.sourroundings_3d_figure import create_3d_surroundings_from_triangles_per_type
        >>> create_3d_surroundings_from_triangles_per_type(
        >>>    output_name="test.html", triangles_per_surroundings_type=tree_triangles
        >>> )
        """

        with fixtures_swisstopo_path.joinpath("trees/trees.json").open() as f:
            m = mocker.Mock()
            m.filter.side_effect = [json.load(f), []]
            mocker.patch.object(fiona, "open", return_value=m)
            # Trees top are located in the z axis at around 260 270 meters of altitude
        mock_elevation(250)

        tree_triangles = list(
            tree_surrounding_handler.SwissTopoTreeSurroundingHandler(
                location=tree_surr_location, simulation_version=simulation_version
            ).get_triangles(building_footprints=layouts)
        )

        # Spy and mocks calls
        assert extruded_spy.call_count == extruded_calls

        # Content checks
        check_surr_triangles(
            expected_area=area,
            first_elem_height=first_tree_height,  # In this case represents the height of the triangle in base
            expected_num_triangles=num_triangles,
            surr_triangles=tree_triangles,
            expected_surr_type={SurroundingType.TREES},
        )

    def test_get_triangles_geometry_is_none(
        self,
        mocker,
        fixtures_path,
        tree_surr_location,
        mocked_gcp_download,
        mock_elevation,
        extruded_spy,
    ):
        m = mocker.Mock()
        m.filter.side_effect = [[], []]
        mocked_fiona = mocker.patch.object(fiona, "open", return_value=m)
        mock_elevation(250)

        triangles = list(
            tree_surrounding_handler.SwissTopoTreeSurroundingHandler(
                location=tree_surr_location,
                simulation_version=random_simulation_version(),
            ).get_triangles(building_footprints=[])
        )

        assert triangles == []
        assert mocked_fiona.call_count == 2
        extruded_spy.assert_not_called()

    def test_exclude_overlapping_with_building(
        self,
        mocker,
        building_footprints_as_wkts,
        mocked_gcp_download,
        mock_elevation,
    ):
        building_multipolygon = building_footprints_as_wkts[-1]
        mock_elevation(250)
        # returns 2 points.
        # a) just outside of the building footprint by 1m, so intersecting the building both trunk and crown
        # b) just outside of the building footprint by 2.5m, so intersecting the building only the trunk
        m = mocker.Mock()
        m.filter.side_effect = (
            [
                {
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            2686719.7027289746,
                            1245828.4655811298,
                            260.1110000000044,
                        ],
                    }
                },
                {
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            2686719.7027289746,
                            1245827.4655811298,
                            260.1110000000044,
                        ],
                    }
                },
            ],
            [],
        )
        mocker.patch.object(fiona, "open", return_value=m)

        triangles = list(
            tree_surrounding_handler.SwissTopoTreeSurroundingHandler(
                location=building_multipolygon.geoms[0].centroid,
                simulation_version=SIMULATION_VERSION.PH_01_2021,
            ).get_triangles(building_footprints=[building_multipolygon])
        )
        # Discards 1 trunk and 2 crowns
        assert len(triangles) == 12
