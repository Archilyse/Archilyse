import json
from collections import OrderedDict

import pytest

from common_utils.constants import REGION, SurroundingType
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.osm import OSMRailwayHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMRailwayHandler:
    def test_get_railway_triangles(
        self, mocker, fixtures_osm_path, oslo_location, dummy_elevation, mock_elevation
    ):
        mock_elevation(100, ZeroElevationHandler)

        with fixtures_osm_path.joinpath("railways/oslo_railways.json").open(
            mode="r"
        ) as f:
            mocker.patch.object(
                OSMRailwayHandler,
                "load_entities",
                return_value=json.load(f),
            )

        railway_surrounding_handler = OSMRailwayHandler(
            location=oslo_location,
            region=REGION.DK,
            bounding_box_extension=500,
            simulation_version=random_simulation_version(),
        )

        railway_triangles = list(
            railway_surrounding_handler.get_triangles(building_footprints=[])
        )

        # Content checks
        assert railway_triangles is not None
        check_surr_triangles(
            expected_area=18408.477,
            first_elem_height=100.25,
            expected_num_triangles=4468,
            surr_triangles=railway_triangles,
            expected_surr_type={SurroundingType.RAILROADS},
        )

    @pytest.mark.parametrize(
        "properties,expected",
        [
            (
                OrderedDict(
                    [
                        ("osm_id", "4978262"),
                        ("code", 6101),
                        ("fclass", "rail"),
                        ("name", "Ligne de Marseille à Vintimille"),
                        ("layer", -1),
                        ("bridge", "F"),
                        ("tunnel", "T"),
                    ]
                ),
                True,
            ),
            (
                OrderedDict(
                    [
                        ("osm_id", "2327984"),
                        ("code", 6101),
                        ("fclass", "rail"),
                        ("name", None),
                        ("layer", 0),
                        ("bridge", "F"),
                        ("tunnel", "F"),
                    ]
                ),
                False,
            ),
        ],
    )
    def test_is_tunnel(self, properties, expected):
        assert OSMRailwayHandler._is_tunnel(properties=properties) is expected
